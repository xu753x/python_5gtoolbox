# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.common import nrModulation
from py5gphy.demodulation import nr_Demodulation

def get_testvectors():
    path = "tests/demodulation/testvectors"
    if len(os.listdir(path)) < 3: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrDeModulation_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_demodulation(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['b'][0]
    mod_data_ref = matfile['mod_data'][0]
    modtype = matfile['modtype'][0]
    snr = matfile['snr'][0][0]
    LLR_ref = matfile['LLR'][0]
    demod_data = matfile['demod_data'][0]
    noise_power = matfile['noise_power'][0][0]
                
    hardbits, LLR = nr_Demodulation.nrDemodulate(demod_data, modtype,noise_power*np.ones(demod_data.size))
    assert np.allclose(LLR, LLR_ref,atol=1e-5)