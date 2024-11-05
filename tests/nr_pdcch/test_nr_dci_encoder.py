# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
from zipfile import ZipFile 

from py5gphy.nr_pdcch import nr_dci_encoder

def get_testvectors():
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
        if f.endswith(".mat") and f.startswith("nrDCIencode_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists    
    

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_dci_encoder(filename):
    #read data
    matfile = io.loadmat(filename)
    dciBits = matfile["dciBits"][0]
    dciCW_ref = matfile["dciCW"][0]
    A = matfile["A"][0][0]
    E = matfile["E"][0][0]
    rnti = matfile["rnti"][0][0]

    dciCW = nr_dci_encoder.nrDCIEncode(dciBits, rnti, E)
    assert np.array_equal(dciCW, dciCW_ref)