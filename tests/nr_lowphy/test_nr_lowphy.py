# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_lowphy import tx_lowphy_process

def get_testvectors():
    path = "tests/nr_lowphy/testvectors"
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
        if f.endswith(".mat") and f.startswith("nrDL_lowphy_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_lowphy(filename):
    """ the main pupose this this test is to test low phy IFFT, add CP, phase compensation
     """
    #read data
    matfile = io.loadmat(filename)
    # read matfile
    fd_slot_data = matfile["fd_slot_data"]
    waveform_ref = matfile["waveform"]
    SampleRate = matfile["SampleRate"][0][0]
    CarrierFrequency = matfile["CarrierFrequency"][0][0]
    BW = matfile["BW"][0][0]
    scs = matfile["scs"][0][0]
            
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    
    carrier_config["BW"] = BW
    carrier_config["scs"] = scs
    carrier_config["carrier_frequency_in_mhz"] = CarrierFrequency/(10**6)
    carrier_config["num_of_ant"] = 1
    
    if scs == 15:
        numofslot = 2
    else:
        numofslot = 4

    fd_slotsize = int(fd_slot_data.size // numofslot)
    td_slotsize = int(waveform_ref.size // numofslot)
            
    td_waveform = np.zeros((1, waveform_ref.size), 'c8')
            
    for idx in range(numofslot):
        sel_fd_slot_data = fd_slot_data[:,idx*fd_slotsize:(idx+1)*fd_slotsize]
        td_slot = tx_lowphy_process.Tx_low_phy(sel_fd_slot_data, carrier_config, SampleRate)
        td_waveform[0, idx*td_slotsize:(idx+1)*td_slotsize] = td_slot
            
    assert np.allclose(td_waveform, waveform_ref,atol=1e-5)
    