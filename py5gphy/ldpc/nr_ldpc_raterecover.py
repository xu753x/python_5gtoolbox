# -*- coding:utf-8 -*-

import numpy as np
import math

def raterecover_ldpc(fe, N, K, kd, Ncb, E, k0, Qm):
    """ does one code block LDPC rate recover by 38.212 5.4.2
    the function include bit de-interleaving and bit selection.
    the calculation of rate match related parameters(such as Nref, Er,k0..) is not in this function
    dn = raterecover_ldpc(fe, E, Qm):
    input:
        fe: Ncb length input sequence
        N: rate recover output length
        K: information bits length
        kd: filler bit location on output, filler bit length = K - kd
        Ncb: circular buffer length
        E: rate match output length
        k0: starting position, refer to table 5.4.2.1-2
        Qm: modulation order in range[1,2,4,6,8]
    output:
        dn: N length sequence
    """

    assert N >= Ncb
    assert fe.size == E

    #bit de-interleaving
    d1 = fe.reshape(E // Qm, Qm)
    d2=d1.T
    ek = d2.reshape(1,E)[0]
    ek = ek.astype('i1')

    # bit selection
    dn = np.zeros(N, 'i1')
    dn[kd:K] = -1 #filler bits
    j = 0
    k = 0
    while k < E:
        if(dn[(k0 + j) % Ncb]) != -1: #not filler bit
            dn[(k0 + j) % Ncb] = ek[k]
            k += 1
        j += 1
    
    return dn

if __name__ == "__main__":
    from scipy import io
    import os
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
                
                dn = raterecover_ldpc(fe, Ncb, K, kd, Ncb, E, k0, Qm)

                assert np.array_equal(dn, dn_ref)

        
    pass