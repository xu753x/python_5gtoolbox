# -*- coding:utf-8 -*-
import numpy as np
import scipy as sp
import time

from py5gphy.ldpc import ldpc_info

def decode_ldpc(dn, bgn):
    """ LDPC decode following to TS38.212 5.3.2
    ck = encode_ldpc(dn, bgn)
    input: 
        dn: N length LDPC decoder iput data
        bgn: base graph value 1 or 2
    output:
        ck: K length LDPC decoded sequence
    
    """
    assert bgn in [1,2]
    N = dn.size
    if bgn == 1:
        Zc = N // 66
        K = 22 * Zc
    else:
        Zc = N // 50
        K = 10 * Zc
    
    #step 1: Find the set with index iLS in Table 5.3.2-1 which contains Zc
    iLS = ldpc_info.find_iLS(Zc)
    assert iLS < 8

    #step 2 : get H
    H = ldpc_info.getH(Zc, bgn, iLS)

    #step3: calculate ck[0:2*Zc]
    # per spec, H * [ck w]' = 0
    #where dn sequence = combination of [ck[2*Zc:K],w]
    #ldpc decoder need estimate ck[0:2*Zc]
    #split [ck w]' to 2ZcX1 C1 and NX1 dn,
    #split H to 
    # | H11. H12 |
    # | H21, H22 |
    # H11 is 2Zc X 2Zc matrix, H12 is 2Zc X H_colsize-2Zc
    # H21 is H_linesize-2Zc X 2Zc, H22 is H_linesize-2Zc X H_colsize-2Zc
    #only H11 and H12 are need
    #H11*C1 + H12*dn = 0 -> C1 = inv(H11)*(-H12*dn)
    Hcolsize = H.shape[1]
    H11 = H[0:2*Zc,0:2*Zc]
    H12 = H[0:2*Zc,2*Zc:Hcolsize]

    L1 = -H12 @ dn.T

    outd = np.linalg.solve(H11, L1) #outd = H11\L1;
    
    C1 = np.round(outd) % 2

    C1 = C1.astype('i1')
    
    #step 4, generate ck
    ck = np.append(C1.T,dn[0:K-2*Zc])
    
    return ck

if __name__ == "__main__":
    from scipy import io
    import os
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
                ck = decode_ldpc(dn, bgn)
                print("decode_ldpc elpased time: {:6.2f}".format(time.time() - start))

                assert np.array_equal(ck, ck_ref)


    pass