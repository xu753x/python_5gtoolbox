# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.common import nrModulation

def get_testvectors():
    path = "tests/common/testvectors_modulation"
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
        if f.endswith(".mat") and f.startswith("nrModulation"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_modulation(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['b'][0]
    mod_data_ref = matfile['mod_data'][0]
    modtype = matfile['modtype'][0]
                
    mod_data = nrModulation.nrModulate(inbits, modtype)
    assert np.allclose(mod_data_ref, mod_data,atol=1e-5)