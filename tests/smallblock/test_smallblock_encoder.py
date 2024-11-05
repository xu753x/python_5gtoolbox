# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.smallblock import nr_smallblock_encoder

def get_testvectors():
    path = "tests/smallblock/testvectors"
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
        if f.endswith(".mat") and f.startswith("smallblock_encode_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_smallblock_encode(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    inbits = matfile['inbits'][0]
    dn_ref = matfile['dn'][0]
    K = matfile['K'][0][0]
    Qm = matfile['Qm'][0][0]
                
    inbits = inbits.astype(np.int8)
    if K <= 2:
        dn = nr_smallblock_encoder.encode_smallblock(inbits, Qm)
    else:
        dn = nr_smallblock_encoder.encode_smallblock(inbits)

    assert np.array_equal(dn, dn_ref)
    