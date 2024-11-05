# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_ssb import nrPBCH

def get_pbch_testvectors():
    path = "tests/nr_ssb/testvectors"
    if len(os.listdir(path)) < 20: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrPBCH_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_pbch_testvectors())
def test_nrPBCH(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    rm_bitseq = matfile['rm_bitseq'][0]
    mod_data_ref = matfile['mod_data'][0]
    NcellID = matfile['NcellID'][0][0]
    iSSB = matfile['iSSB'][0][0]

    mod_data = nrPBCH.nrPBCHencode(rm_bitseq, NcellID, iSSB)
    assert np.allclose(mod_data, mod_data_ref,atol=1e-5)