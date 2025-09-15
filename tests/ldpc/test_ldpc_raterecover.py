# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.ldpc import nr_ldpc_raterecover
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
def test_nr_ldpc_raterecover(filename):
    matfile = io.loadmat(filename)
    #read data from mat file
    dn_ref = matfile['dn'][0]
    fe = matfile['fe'][0]
    Ncb = matfile['Ncb'][0][0]
    E = matfile['E'][0][0]
    Qm = matfile['Qm'][0][0]
    k0 = matfile['k0'][0][0]
    kd = matfile['kd'][0][0]
    K = matfile['K'][0][0]
    N = dn_ref.size

    if K % 22 == 0:
        #bgn = 1
        Zc = K // 22
    else:
        #bgn = 2
        Zc = K // 10

    LLRin = 1 - 2*fe.astype('i1')
    LLRout = nr_ldpc_raterecover.raterecover_ldpc(LLRin, Ncb, N, k0, Qm,Zc, kd, K)
    outbits = (1-LLRout)/2
    outbits[outbits==0.5] = -1

    fe_ref = nr_ldpc_ratematch.ratematch_ldpc(outbits, Ncb, E, k0, Qm)
    
    assert np.array_equal(fe, fe_ref)
    
