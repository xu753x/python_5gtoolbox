# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os

from py5gphy.polar import nr_polar_raterecover

def test_nr_polar_raterecover():
    curpath = "tests/polar/testvectors"
    for f in os.listdir(curpath):
        if f.endswith(".mat") and f.startswith("polarRM_recover_testvec"):
            matfile = io.loadmat(curpath + '/' + f)
            #read data from mat file
            inbits = matfile['in'][0]
            outd = matfile['outd'][0]
            E = matfile['E'][0][0]
            K = matfile['K'][0][0]
            N = matfile['N'][0][0]
            iBIL = matfile['iBIL'][0][0]

            outbits = nr_polar_raterecover.ratemrecover_polar(inbits, K, N, iBIL)

            assert np.array_equal(outd, outbits)

    pass

if __name__ == "__main__":
    test_nr_polar_raterecover()

    pass