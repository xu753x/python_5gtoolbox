# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.polar import nr_polar_encoder

def get_testvectors():
    path = "tests/polar/testvectors"
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
        if f.endswith(".mat") and f.startswith("polarencoder_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_polar_encoder(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['in'][0]
    outd = matfile['outd'][0]
    E = matfile['E'][0][0]
    nMax = matfile['nMax'][0][0]
    iIL = matfile['iIL'][0][0]

    outbits = nr_polar_encoder.encode_polar(inbits, E, nMax, iIL)

    assert np.array_equal(outd, outbits)