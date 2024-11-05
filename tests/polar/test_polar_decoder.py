# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os

from py5gphy.polar import nr_polar_decoder

def test_nr_polar_decoder():
    curpath = "tests/polar/testvectors"
    for f in os.listdir(curpath):
        if f.endswith(".mat") and f.startswith("polarencoder_testvec"):
            matfile = io.loadmat(curpath + '/' + f)
            #read data from mat file
            inbits = matfile['in'][0]
            outd = matfile['outd'][0]
            E = matfile['E'][0][0]
            nMax = matfile['nMax'][0][0]
            iIL = matfile['iIL'][0][0]

            decbits = nr_polar_decoder.decode_polar(outd, E, inbits.size, nMax, iIL)

            assert np.array_equal(decbits, inbits)

    pass

if __name__ == "__main__":
    test_nr_polar_decoder()

    pass