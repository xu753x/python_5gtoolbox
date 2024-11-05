# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.ldpc import nr_ldpc_ratematch

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
        if f.endswith(".mat") and f.startswith("ldpc_ratematch_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_ldpc_ratematch(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    dn = matfile['dn'][0]
    fe_ref = matfile['fe'][0]
    Ncb = matfile['Ncb'][0][0]
    E = matfile['E'][0][0]
    Qm = matfile['Qm'][0][0]
    k0 = matfile['k0'][0][0]
              
    fe = nr_ldpc_ratematch.ratematch_ldpc(dn, Ncb, E, k0, Qm)

    assert np.array_equal(fe, fe_ref)