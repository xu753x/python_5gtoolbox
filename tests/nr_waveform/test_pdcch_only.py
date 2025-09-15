# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
from zipfile import ZipFile 
import json

from tests.nr_pdcch import nr_pdcch_testvectors
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_dl_waveform

def get_pdcch_testvectors():
    path = "tests/nr_pdcch/testvectors"
    if len(os.listdir(path)) < 10: #desn't unzip testvectors
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
    

@pytest.mark.parametrize('filename', get_pdcch_testvectors())
def test_nr_pdcch_only(filename):
    #read data
    matfile = io.loadmat(filename)
    dcibits_out,RM_out, mod_out, dmrssym_out, fd_slot_data_ref, pdcch_tvcfg = \
        nr_pdcch_testvectors.read_pdcch_testvec_matfile(matfile)
    carrier_config, coreset_config, search_space_config, pdcch_config = \
        nr_pdcch_testvectors.gen_pdcch_testvec_config(pdcch_tvcfg)

    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofslots'] = int(2*carrier_config['scs']/15)
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    NumDCIBits = pdcch_config['NumDCIBits']
    inbits = np.tile(np.array([1,0,1,0,1,1]), int((NumDCIBits / 6)+6))
    pdcch_config['data_source'] = list(inbits[0 : NumDCIBits])

    pdcch_config_list = []
    pdcch_config_list.append(pdcch_config)
    search_space_list = []
    search_space_list.append(search_space_config)
    coreset_config_list = []
    coreset_config_list.append(coreset_config)

    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    ssb_config["enable"] = 'False'
    pdsch_config_list = []
    csirs_config_list = []

    BW = carrier_config['BW']
    scs = carrier_config['scs']
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    slot_size = carrier_prbsize*12*14

    [nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list] = nr_dl_waveform.gen_dl_channel_list(
    waveform_config,carrier_config,
    ssb_config,pdcch_config_list,
    search_space_list,coreset_config_list,
    csirs_config_list,pdsch_config_list
    )
    fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config,  
                nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list )
    #only check first slot
    slot = 0
    sel_fd_waveform = fd_waveform[:,slot*slot_size:(slot+1)*slot_size]
    sel_fd_slot_data_ref = fd_slot_data_ref[:,slot*slot_size:(slot+1)*slot_size]
    assert np.allclose(sel_fd_waveform, sel_fd_slot_data_ref, atol=1e-5)

    