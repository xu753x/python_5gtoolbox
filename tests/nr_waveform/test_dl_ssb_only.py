# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_waveform import nr_dl_waveform
from tests.nr_ssb import nr_ssb_testvectors

def get_ssb_highphy_testvectors():
    path = "tests/nr_ssb/testvectors_highphy"
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
        if f.endswith(".mat") and f.startswith("nrSSB_highphy_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_ssb_highphy_testvectors())
def test_dl_ssb_only(filename):
    matfile = io.loadmat(filename)
    
    waveform, fd_slot_data_ref, ssb_tvcfg = nr_ssb_testvectors.read_ssb_testvec_matfile(matfile)

    carrier_config,ssb_config = nr_ssb_testvectors.gen_ssb_testvec_config(ssb_tvcfg)

    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofslots'] = int(10*carrier_config['scs']/15)
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    pdcch_config_list = []
    search_space_list = []
    coreset_config_list = []
    csirs_config_list = []
    pdsch_config_list = []
    
    [nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list] = nr_dl_waveform.gen_dl_channel_list(
    waveform_config,carrier_config,
    ssb_config,pdcch_config_list,
    search_space_list,coreset_config_list,
    csirs_config_list,pdsch_config_list
    )
    fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config,  
                nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list )
    
    
    assert np.allclose(fd_slot_data_ref, fd_waveform, atol=1e-5)


    