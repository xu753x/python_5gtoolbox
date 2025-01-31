# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
from zipfile import ZipFile 

from tests.nr_pdcch import nr_pdcch_testvectors
from py5gphy.nr_pdcch import nr_pdcch
from py5gphy.nr_pdcch import nr_searchspace
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_pdcch/testvectors"
    if len(os.listdir(path)) < 20: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrPDCCH_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists    
    

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdcch(filename):
    #read data
    matfile = io.loadmat(filename)
    dcibits_out,RM_out, mod_out, dmrssym_out, fd_slot_data_ref, pdcch_tvcfg = \
        nr_pdcch_testvectors.read_pdcch_testvec_matfile(matfile)
    carrier_config, coreset_config, search_space_config, pdcch_config = \
        nr_pdcch_testvectors.gen_pdcch_testvec_config(pdcch_tvcfg)

    nrSearchSpace = nr_searchspace.NrSearchSpace(carrier_config, search_space_config, coreset_config)
    
    #init slot data
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    #matlab code generate 4 slots of data for 30khz scs and 2 slots of data for 15khz scs
    scs = carrier_config['scs']
    if scs == 30:
        slot_num = 4
    else:
        slot_num = 2
    NumDCIBits = pdcch_config['NumDCIBits']
    inbits = np.tile(np.array([1,0,1,0,1,1]), int((NumDCIBits*slot_num // 6)+6))
    
    for slot in range(slot_num):
        fd_slot_data, RE_usage_inslot = \
            nr_slot.init_fd_slot(carrier_config['num_of_ant'], nrSearchSpace.carrier_prb_size)
    
        sfn = 1 #any value is OK

        #solve input bit sequence issue
        
        offset = NumDCIBits * slot
        pdcch_config['data_source'] = inbits[offset : offset + NumDCIBits]
        
        nrPDCCH = nr_pdcch.Pdcch(pdcch_config, nrSearchSpace) 
    
        fd_slot_data, RE_usage_inslot = \
            nrPDCCH.process(fd_slot_data, RE_usage_inslot,sfn,slot)
    
        #verify
        samplesize_in_slot = int(fd_slot_data_ref.shape[1]/slot_num)
        sel_fd_slot_data_ref = fd_slot_data_ref[0,slot*samplesize_in_slot:(slot+1)*samplesize_in_slot]

        assert np.allclose(fd_slot_data, sel_fd_slot_data_ref,atol=1e-5)

    