# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.polar import polar_interleaver
from py5gphy.polar import polar_construct
from py5gphy.polar import gen_kron_matrix

def decode_polar(indata, E, K, nMax, iIL, algo='raw'):
    """ decode Polar code
    decbits = decode_polar(indata, N, E, K, nMax, iIL, algo)
    input:
        indata: N length input data
        N: length of input data
        E: rate match length
        K: decoded data length
        (nMax, iIL): (9, 1) apply for DL and (10, 0) apply for UL
        algo: algorithm used for polar decoder
             supported polar decoder algothim:
             (1) 'raw': simplest methos, just pick up information bits
    output:
        decbits: L length bits

    """
    if algo != 'raw':
        #add new algo in future
        return 0
    
    ##raw algo
    #get F array, PC array and other values
    F, qPC, N, nPC, nPCwm = polar_construct.construct(K, E, nMax)

    assert indata.size == N

    #get G
    G = gen_kron_matrix.gen_kron(N)
    invG = np.linalg.inv(G)  #inverse matrix
    assert np.array_equal(G @ invG, np.eye(N))  
    
    # get u
    u = (indata @ invG) % 2
    u.astype('i1')

    #get interleaved ck
    ck_itrl = np.zeros(K, 'i1')
    if nPC == 0:
        k = 0
        for idx in range(N):
            if F[idx] == 0:  #information bit
                ck_itrl[k] = u[idx] 
                k += 1
    else:  #nPC > 0
        k = 0
        for idx in range(N):
            if F[idx] == 0:  #information bit
                if idx not in qPC:
                    ck_itrl[k] = u[idx] 
                    k += 1
    
    #de-interleave
    if iIL:
        decbits = polar_interleaver.deinterleave(ck_itrl, K)
    else:
        decbits = ck_itrl

    return decbits.astype('i1')
    

if __name__ == "__main__":
    indata = np.array([1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0], 'i1')
    decbits = decode_polar(indata, 150, 33, 9, 1, algo='raw')
    assert np.array_equal(decbits, np.array([1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0], 'i1'))

    pass