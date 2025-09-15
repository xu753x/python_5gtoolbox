# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from tests.nr_pdsch import nr_pdsch_testvectors
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_dl_waveform

def get_pdsch_testvectors():
    path = "tests/nr_pdsch/testvectors"
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
        if f.endswith(".mat") and f.startswith("nrPDSCH_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_pdsch_testvectors())
def test_nr_pdsch_only(filename):
    """ the main pupose this this test is to test PDSCH scrambling, modulation and resurce mapping
     defined in 38.211 7.3.1
     the teste vectors contain only PDSCH channel, no SSB/PDCCH/CSI-RS channel which may have PRB resource conflict with PDSCH
     """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config_list = []
    pdsch_config_list.append(pdsch_config)
    
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofslots'] = int(2*carrier_config['scs']/15)
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    pdcch_config_list = []
    search_space_list = []
    coreset_config_list = []
    
    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    ssb_config["enable"] = 'False'
    csirs_config_list = []

    [nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list] = nr_dl_waveform.gen_dl_channel_list(
    waveform_config,carrier_config,
    ssb_config,pdcch_config_list,
    search_space_list,coreset_config_list,
    csirs_config_list,pdsch_config_list
    )
    fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config,  
                nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list )
    assert np.allclose(fd_waveform, ref_fd_slot_data, atol=1e-5)