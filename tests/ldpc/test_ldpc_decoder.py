# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os
import time

from py5gphy.ldpc import nr_ldpc_decode

def test_nr_ldpc_decode():
    curpath = "tests/ldpc/testvectors"
    for f in os.listdir(curpath):
            if f.endswith(".mat") and f.startswith("ldpc_encode_testvec"):
                print("LDPC decode testvector: " + f)
                matfile = io.loadmat(curpath + '/' + f)
                #read data from mat file
                ck_ref = matfile['in'][0]
                dn = matfile['dn'][0]
                Zc = matfile['Zc'][0][0]
                bgn = matfile['bgn'][0][0]
                
                start = time.time()
                ck = nr_ldpc_decode.decode_ldpc(dn, bgn)
                print("decode_ldpc elpased time: {:6.2f}".format(time.time() - start))

                assert np.array_equal(ck, ck_ref)
    

if __name__ == "__main__":
    test_nr_ldpc_decode()

    pass