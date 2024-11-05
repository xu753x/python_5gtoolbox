# -*- coding: utf-8 -*-
import numpy as np
import pytest
from scipy import io
import os
import time

from py5gphy.ldpc import nr_ldpc_raterecover

def test_nr_ldpc_raterecover():
    curpath = "tests/ldpc/testvectors"
    for f in os.listdir(curpath):
        if f.endswith(".mat") and f.startswith("ldpc_ratematch_testvec"):
            if f.startswith("ldpc_ratematch_testvec_Ncb_64_E_42_Qm_6_k0_20"):
                continue

            matfile = io.loadmat(curpath + '/' + f)
            #read data from mat file
            dn_ref = matfile['dn'][0]
            fe = matfile['fe'][0]
            Ncb = matfile['Ncb'][0][0]
            E = matfile['E'][0][0]
            Qm = matfile['Qm'][0][0]
            k0 = matfile['k0'][0][0]
            kd = matfile['kd'][0][0]
            K = matfile['K'][0][0]
              
            dn = nr_ldpc_raterecover.raterecover_ldpc(fe, Ncb, K, kd, Ncb, E, k0, Qm)

            assert np.array_equal(dn, dn_ref)
    

if __name__ == "__main__":
    test_nr_ldpc_raterecover()

    pass