# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 

from tests.nr_pucch import nr_pucch_format3_testvectors
from py5gphy.nr_pucch import nr_pucch_format3
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_pucch/testvectors_format3"
    if len(os.listdir(path)) < 100: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nr_pucchformat3_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pucchformat3(filename):
    #read data
    matfile = io.loadmat(filename)
    codeword_out, symbols_out, fd_slot_data_ref, pucchformat3_tvcfg = \
        nr_pucch_format3_testvectors.read_pucch_format3_testvec_matfile(matfile)
    carrier_config, pucch_format3_config = \
        nr_pucch_format3_testvectors.gen_pucchformat3_testvec_config(pucchformat3_tvcfg)
    
    nrPUCCHFormat3 = nr_pucch_format3.NrPUCCHFormat3(carrier_config, pucch_format3_config)

    #init slot data
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    #matlab code generate 4 slots of data for 30khz scs and 2 slots of data for 15khz scs
    scs = carrier_config['scs']
    if scs == 30:
        slot_num = 4
    else:
        slot_num = 2
    
    for slot in range(slot_num):
        fd_slot_data, RE_usage_inslot = \
            nr_slot.init_fd_slot(carrier_config['num_of_ant'], nrPUCCHFormat3.carrier_prb_size)
    
        sfn = 1 #pucch period is 1 slots, so any value is OK
    
        fd_slot_data, RE_usage_inslot = \
            nrPUCCHFormat3.process(fd_slot_data, RE_usage_inslot,sfn,slot)
    
        #verify
        samplesize_in_slot = int(fd_slot_data_ref.shape[1]/slot_num)
        sel_fd_slot_data_ref = fd_slot_data_ref[0,slot*samplesize_in_slot:(slot+1)*samplesize_in_slot]

        assert np.allclose(fd_slot_data, sel_fd_slot_data_ref,atol=1e-5)

    