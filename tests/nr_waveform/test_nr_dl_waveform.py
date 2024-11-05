# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from tests.nr_waveform import nr_dl_testvectors

from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_dl_waveform

def get_testvectors():
    path = "tests/nr_waveform/testvectors"
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
        if f.endswith(".mat") and f.startswith("nrPDSCH_mixed_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_DL_waveform(filename):
    """ the main pupose this this test is to test mixed DL channel
    the teste vectors contain SSB, PSCCH,PDSCH,CSI-RS channel
     """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out,layermap_out, fd_slot_data, waveform, DL_tvcfg = \
        nr_dl_testvectors.read_nrPDSCH_mixed_testvec_matfile(matfile)
    waveform_config, carrier_config, ssb_config, pdsch_config, \
        csirs_config, coreset_config, search_space_config, pdcch_config = \
            nr_dl_testvectors.gen_DL_waveform_testvec_config(DL_tvcfg)

    ssb_config["enable"] = "True"
    pdcch_config_list = []
    pdcch_config_list.append(pdcch_config)

    search_space_list = []
    search_space_list.append(search_space_config)

    coreset_config_list = []
    coreset_config_list.append(coreset_config)

    csirs_config_list = []
    csirs_config_list.append(csirs_config)

    pdsch_config_list = []
    pdsch_config_list.append(pdsch_config)

    fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config, ssb_config, 
                    pdcch_config_list, search_space_list, coreset_config_list, 
                    csirs_config_list, pdsch_config_list)
    
    #fd_slot_data generated from matlab 5g toolbox contain PDSCH, PDCCH and CSI-RS, not include SSB
    #waveform is time domain data generated from matlab 5g toolbox that also include SSB
    #this is why need compare time domain data
    #assert np.allclose(fd_waveform, fd_slot_data, atol=1e-5)
    assert np.allclose(td_waveform, waveform, atol=1e-5)