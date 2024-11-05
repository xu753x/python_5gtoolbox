# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.common import lowPAPR_seq

def get_testvectors():
    path = "tests/common/testvectors_lowPAPR"
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
        if f.endswith(".mat") and f.startswith("nrlowPAPR"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_lowPAPR_seq(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    u = matfile['u'][0][0]
    v = matfile['v'][0][0]
    alpha = matfile['alpha'][0][0]
    Msc = matfile['Msc'][0][0]
    seq_ref = matfile['seq'][0]
    
                
    seq = lowPAPR_seq.gen_lowPAPR_seq(u,v,alpha,Msc)
    assert np.allclose(seq, seq_ref,atol=1e-5)