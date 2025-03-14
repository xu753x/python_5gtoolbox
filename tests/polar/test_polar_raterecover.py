# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.polar import nr_polar_raterecover

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
        if f.endswith(".mat") and f.startswith("polarRM_recover_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_polar_raterecover(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['in'][0]
    outd = matfile['outd'][0]
    E = matfile['E'][0][0]
    K = matfile['K'][0][0]
    N = matfile['N'][0][0]
    iBIL = matfile['iBIL'][0][0]

    LLRin = 1 - 2*inbits.astype('i1')

    LLR_limit = 20

    LLRout = nr_polar_raterecover.ratemrecover_polar(LLRin, K, N, iBIL,LLR_limit)
    LLRout[LLRout==LLR_limit] = 1
    outbits = (1-LLRout)/2

    assert np.array_equal(outd, outbits.astype('u1'))
