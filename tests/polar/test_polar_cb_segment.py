# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np


from py5gphy.polar import nr_polar_cbsegment

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
        if f.endswith(".mat") and f.startswith("polar_cbsegment_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_polar_cb_segment(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    uciBits = matfile['in'][0]
    outd = matfile['outd']
    Euci = matfile['Euci'][0][0]
    Cref = matfile['C'][0][0]
    Er_ref = matfile['Er'][0][0]
    A = matfile['A'][0][0]

    polar_cb_blks, C, Er = nr_polar_cbsegment.polar_cbsegment(uciBits, Euci)

    assert np.array_equal(outd, polar_cb_blks)
    assert C == Cref
    assert Er == Er_ref
    