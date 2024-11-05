# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.ldpc import nr_ldpc_cbsegment

def get_testvectors():
    path = "tests/ldpc/testvectors"
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
        if f.endswith(".mat") and f.startswith("ldpc_cbsegment_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_ldpc_cb_segment(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['in'][0]
    cbs_ref = matfile['cbs']
    B = matfile['B'][0][0]
    bgn = matfile['bgn'][0][0]
                
    cbs, Zc = nr_ldpc_cbsegment.ldpc_cbsegment(inbits, bgn)
    assert np.array_equal(cbs, cbs_ref)
                
    