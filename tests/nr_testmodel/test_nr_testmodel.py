# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.nr_testmodel import nr_testmodel_cfg

def get_testvectors():
    path = "tests/nr_testmodel/testvectors"
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
        if f.endswith(".mat") and f.startswith("nrTestMode_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_testmodels(filename):
    """ the main pupose this this test is to test mixed DL channel
    the teste vectors contain SSB, PSCCH,PDSCH,CSI-RS channel
     """
    #read data
    matfile = io.loadmat(filename)
    ref_fd_slot_data = matfile['fd_slot_data']
    scs = matfile["Scs"][0][0]
    BW = matfile["BW"][0][0]
    dm = matfile["dm"][0]
    dlnrref = matfile["dlnrref"][0]
    ncellid = matfile["ncellid"][0][0]
    carrier_frequency_in_mhz = 0

    waveform_config, carrier_config, ssb_config, csirs_config_list, \
        coreset_config_list, search_space_list, pdcch_config_list, pdsch_config_list = \
        nr_testmodel_cfg.gen_nr_TM_cfg(scs, BW, dm, dlnrref,ncellid, carrier_frequency_in_mhz)
    
    # add additional test data
    for pdcch_config in pdcch_config_list:
        pdcch_config['data_source'] = [1,1,0,0]
    
    for pdsch_config in pdsch_config_list:
        pdsch_config['data_source'] = [1,0,0,1]

    fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config, ssb_config, 
                    pdcch_config_list, search_space_list, coreset_config_list, 
                    csirs_config_list, pdsch_config_list)
    
    assert np.allclose(fd_waveform, ref_fd_slot_data, atol=1e-5)