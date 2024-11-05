# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os
import time

from py5gphy.smallblock import nr_smallblock_decoder

def test_nr_smallblock_decode():
    curpath = "tests/smallblock/testvectors"
    for f in os.listdir(curpath):
            if f.endswith(".mat") and f.startswith("smallblock_encode_testvec"):
                matfile = io.loadmat(curpath + '/' + f)
                #read data from mat file
                ck_ref = matfile['inbits'][0]
                dn = matfile['dn'][0]
                K = matfile['K'][0][0]
                Qm = matfile['Qm'][0][0]
                
                if K <= 2:
                    ck = nr_smallblock_decoder.decode_smallblock(dn, K, Qm)
                else:
                    ck = nr_smallblock_decoder.decode_smallblock(dn, K)

                assert np.array_equal(ck, ck_ref)
    

if __name__ == "__main__":
    test_nr_smallblock_decode()

    pass