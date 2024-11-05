# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
from zipfile import ZipFile 
import numpy as np
import math
import json

from tests.nr_csirs import nr_csirs_testvector
from py5gphy.nr_csirs import nr_csirs
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_dl_waveform

def get_csirs_testvectors():
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

@pytest.mark.parametrize('filename', get_csirs_testvectors())
def test_nr_csirs_only(filename):
    #read data
    matfile = io.loadmat(filename)
    csirsSym_out, csirsLinInd_out, fd_slot_data_ref, csirstv_cfg = \
        nr_csirs_testvector.read_nrCSIRS_testvec_matfile(matfile)
    carrier_config, csirs_config = \
        nr_csirs_testvector.gen_nrCSIRS_testvec_config(csirstv_cfg)
    
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofsubframes'] = 2
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    ssb_config["enable"] = 'False'
    pdcch_config_list = []
    search_space_list = []
    coreset_config_list = []
    pdsch_config_list = []
    
    
    #matlab code generate 4 slots of CSIRS data for 30khz scs and 2 slots of data for 15khz scs
    #CSI-RS data is scheduled on each slot
    #while CSI-RS only support minimum 4 slot periodicaly, here need change slotoffset to test each slot
    BW = carrier_config['BW']
    scs = carrier_config['scs']
    if scs == 30:
        slot_num = 4
    else:
        slot_num = 2
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    slot_size = carrier_prbsize*12*14

    for slot in range(slot_num):
        csirs_config['slotoffset'] = slot
        csirs_config_list = []
        csirs_config["enable"] = 'True'
        csirs_config_list.append(csirs_config)
        fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config, ssb_config, 
                    pdcch_config_list, search_space_list, coreset_config_list, 
                    csirs_config_list, pdsch_config_list)
        sel_fd_waveform = fd_waveform[:,slot*slot_size:(slot+1)*slot_size]
        sel_fd_slot_data_ref = fd_slot_data_ref[:,slot*slot_size:(slot+1)*slot_size]
        assert np.allclose(sel_fd_waveform, sel_fd_slot_data_ref, atol=1e-5)
