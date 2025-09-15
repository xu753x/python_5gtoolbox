# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 
import json

from tests.nr_pucch import nr_pucch_format4_testvectors
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_ul_waveform

def get_testvectors():
    path = "tests/nr_pucch/testvectors_format4"
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
        if f.endswith(".mat") and f.startswith("nr_pucchformat4_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pucchformat4_only(filename):
    #read data
    matfile = io.loadmat(filename)
    codeword_out, symbols_out, ref_fd_slot_data, pucchformat4_tvcfg = \
        nr_pucch_format4_testvectors.read_pucch_format4_testvec_matfile(matfile)
    carrier_config, pucch_format4_config = \
        nr_pucch_format4_testvectors.gen_pucchformat4_testvec_config(pucchformat4_tvcfg)
    
    BW = carrier_config['BW']
    scs = carrier_config['scs']
    if scs == 30:
        numofslot = 4
    else:
        numofslot = 2
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    slot_size = carrier_prbsize*12*14

    path = "py5gphy/nr_default_config/"
    with open(path + "default_UL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofslots'] = int(2*carrier_config['scs']/15)
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    pusch_config_list = []
    srs_config_list = []
    pucch_format0_config_list = []
    pucch_format1_config_list = []
    pucch_format2_config_list = []
    pucch_format3_config_list = []
    
    #input data seq is [0,0,1,1,...] for even slot and [1,1,0,0,...] for odd slot
    NumUCIBits = pucch_format4_config['NumUCIBits']
    for m in [0,1]:
        if NumUCIBits % 4:
            #input data seq is [0,0,1,1,...] for even slot and [1,1,0,0,...] for odd slot
            if m == 1: #odd slot
                d1 = np.tile(np.array([1,1,0,0]), int((pucch_format4_config['NumUCIBits'] // 4)+4))
            else: #even slot
                d1 = np.tile(np.array([0,0,1,1]), int((pucch_format4_config['NumUCIBits'] // 4)+4))
            pucch_format4_config['UCIbits'] = d1[0:pucch_format4_config['NumUCIBits']]
        pucch_format4_config_list = []
        pucch_format4_config_list.append(pucch_format4_config)
    
        fd_waveform, td_waveform, ul_waveform = nr_ul_waveform.gen_ul_waveform(waveform_config, 
                    carrier_config, pusch_config_list, srs_config_list,
                    pucch_format0_config_list,pucch_format1_config_list,pucch_format2_config_list,
                    pucch_format3_config_list,pucch_format4_config_list)

        #compare even slot for m==0 and odd slot for m==1
        sel1 = fd_waveform[0,:].reshape((-1,slot_size))
        sel2 = ref_fd_slot_data[0,:].reshape((-1,slot_size))
        data1 = sel1[m::2,:]
        data2 = sel2[m::2,:]
        assert np.allclose(data1, data2, atol=1e-5)

    