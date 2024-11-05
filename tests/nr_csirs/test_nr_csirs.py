# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
from zipfile import ZipFile 
import numpy as np
import math

from tests.nr_csirs import nr_csirs_testvector
from py5gphy.nr_csirs import nr_csirs
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_csirs/testvectors"
    if len(os.listdir(path)) < 5: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrCSIRS_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists    

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_csirs(filename):
    #read data
    matfile = io.loadmat(filename)
    csirsSym_out, csirsLinInd_out, fd_slot_data_ref, csirstv_cfg = \
        nr_csirs_testvector.read_nrCSIRS_testvec_matfile(matfile)
    carrier_config, csirs_config = \
        nr_csirs_testvector.gen_nrCSIRS_testvec_config(csirstv_cfg)
    
    #matlab code generate 4 slots of CSIRS data for 30khz scs and 2 slots of data for 15khz scs
    scs = carrier_config['scs']
    if scs == 30:
        slot_num = 4
    else:
        slot_num = 2
    nrCSIRS = nr_csirs.NrCSIRS(carrier_config, csirs_config)

    for slot in range(slot_num):
        BW = carrier_config['BW']
    
        fd_slot_data, RE_usage_inslot = \
            nr_slot.init_fd_slot(carrier_config['num_of_ant'], nrCSIRS.carrier_prb_size)
    
        sfn = 0 #to make sure CSIRS s=i sscheduled in this slot
        csirs_config['slotoffset'] = slot
        nrCSIRS = nr_csirs.NrCSIRS(carrier_config, csirs_config)
        fd_slot_data, RE_usage_inslot = \
            nrCSIRS.process(fd_slot_data, RE_usage_inslot,sfn,slot)

        #verify
        samplesize_in_slot = int(fd_slot_data_ref.shape[1]/slot_num)
        sel_fd_slot_data_ref = fd_slot_data_ref[:,slot*samplesize_in_slot:(slot+1)*samplesize_in_slot]

        assert np.allclose(fd_slot_data, sel_fd_slot_data_ref,atol=1e-5)