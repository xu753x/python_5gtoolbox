# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os
import time
from zipfile import ZipFile 

from py5gphy.ldpc import nr_ldpc_decode

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
        if f.endswith(".mat") and f.startswith("ldpc_encode_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_ldpc_decode_BF(filename):
    """ test LDPC BF decoder"""
    #ldpc decoder parameters
    snr_db = 4
    bler_target = 0.3
    max_count = 200
    L = 32

    matfile = io.loadmat(filename)
    #read data from mat file
    ck_ref = matfile['in'][0]
    dn = matfile['dn'][0]
    Zc = matfile['Zc'][0][0]
    bgn = matfile['bgn'][0][0]

    #test to verify bler <= bler_target
    failed_count = 0
    for _ in range(max_count):
        en = 1 - 2*dn #BPSK modulation, 0 -> 1, 1 -> -1
        fn = en + np.random.normal(0, 10**(-snr_db/20), dn.size) #add noise
        #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
        noise_power = 10**(-snr_db/10)
        LLRin = 2*fn/noise_power

        dn_decoded, status = nr_ldpc_decode.nr_decode_ldpc(LLRin, Zc, bgn, L, algo='BF')
        if not np.array_equal(ck_ref,dn_decoded[0:ck_ref.size]):
            failed_count += 1
    
    bler = failed_count/max_count
    assert bler <= bler_target
    
