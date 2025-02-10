# -*- coding:utf-8 -*-
import numpy as np
import scipy as sp
import time

from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import ldpc_decoder_bit_flipping
from py5gphy.ldpc import ldpc_decoder_belief_propagation
from py5gphy.ldpc import ldpc_decoder_min_sum


def decode_ldpc(LLRin, H, L, algo='min-sum', alpha=1, beta=0):
    """ LDPC decoder, support BF(bit flipping), BP(belief propagation), min-sum algorithms
    BP is also named sum-product algorithm
    input: 
        LLRin: N length LDPC decoder LLR input data
        H: LDPC matrix, 
        L: iteration size
        algo: one of ["BF", "BP", "min-sum"]
        alpha: (0:1] used for normalized min-sum. 1 means no normalized
        beta: >=0 used for offset min-sum, 0 means no offset
    output:
        ck: N length LDPC decoded sequence
        status: True or False
    """     
    if algo == "BF":
        ck, status = ldpc_decoder_bit_flipping.ldpc_decoder_BF(LLRin, H, L)
    elif algo == "BP":
        ck, status = ldpc_decoder_belief_propagation.ldpc_decoder_BP(LLRin, H, L)
    elif algo == "min-sum":
        ck, status = ldpc_decoder_min_sum.ldpc_decoder_min_sum(LLRin, H, L, alpha, beta)
    else:
        assert 0
    return ck, status

def nr_decode_ldpc(LLRin, bgn, crcpoly, algo='None'):
    """ LDPC decode following to TS38.212 5.3.2
    ck = encode_ldpc(dn, bgn)
    input: 
        LLRin: N length LDPC decoder LLR input data
        bgn: base graph value 1 or 2
        crcpoly: one of ['24A','24B','16']
        algo: ldpc decoder algorithm
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
    
    return ck, True

def for_test_ldpc_encoder(K, H, snr_db):
    ck = np.random.randint(2, size=K)
    #ldpc encoder to get parity bits
    Hrowsize = H.shape[0]
    Hcolsize = H.shape[1]
    H1 = H[:,0:Hcolsize-Hrowsize]
    H2 = H[:,Hcolsize-Hrowsize:Hcolsize]

    L1 = -H1 @ ck.T  #matrix multiply
    outd = np.linalg.solve(H2, L1) #outd = H2\L1;
    wn = np.round(outd) % 2
    wn = wn.astype('i1')

    dn = np.concatenate((ck, wn))

    en = 1 - 2*dn #BPSK modulation, 0 -> 1, 1 -> -1
    fn = en + np.random.normal(0, 10**(-snr_db/20), dn.size) #add noise
    
    #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
    noise_power = 10**(-snr_db/10)
    LLRin = fn/noise_power

    return dn, LLRin

if __name__ == "__main__":
    from scipy import io
    import os
    from py5gphy.crc import crc
    from py5gphy.ldpc import nr_ldpc_encode

    K = 220-24
    bgn = 1
    crcpoly = '24A'
    
    inbits = np.random.randint(2, size=K)
    blkandcrc = crc.nr_crc_encode(inbits, crcpoly)
    dn = nr_ldpc_encode.encode_ldpc(blkandcrc, bgn)
    #LLRin = (1-2*dn) # no noise
    #decbits, status = decode_ldpc(LLRin, bgn, crcpoly)
    #assert status == True
    #assert np.array_equal(decbits, blkandcrc)


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