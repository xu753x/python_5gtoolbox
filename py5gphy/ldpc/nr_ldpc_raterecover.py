# -*- coding:utf-8 -*-

import numpy as np
import math

def raterecover_ldpc(LLRin, N, K, kd, Ncb, E, k0, Qm):
    """ does one code block LDPC rate recover by 38.212 5.4.2
    the function include bit de-interleaving and bit selection.
    the calculation of rate match related parameters(such as Nref, Er,k0..) is not in this function
    dn = raterecover_ldpc(fe, E, Qm):
    input:
        LLRin: Ncb length input LLR sequence
        N: rate recover output length
        K: information bits length
        kd: filler bit location on output, filler bit length = K - kd
        Ncb: circular buffer length
        E: rate match output length
        k0: starting position, refer to table 5.4.2.1-2
        Qm: modulation order in range[1,2,4,6,8]
    output:
        LLRout: N length sequence
    """

    assert N >= Ncb
    assert LLRin.size == E

    #bit de-interleaving
    d1 = LLRin.reshape(E // Qm, Qm)
    d2=d1.T
    ek = d2.reshape(1,E)[0]
    
    # bit selection
    LLRout = np.zeros(N)
    j = 0
    k = 0
    while k < E:
        loc = (k0 + j) % Ncb
        if loc not in range(kd,K): #not filler bit
            LLRout[loc] = ek[k]
            k += 1
        j += 1
    
    return LLRout

if __name__ == "__main__":
    from scipy import io
    import os
    print("test LDPC rate recover")
    from tests.ldpc import test_ldpc_raterecover
    file_lists = test_ldpc_raterecover.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_ldpc_raterecover.test_nr_ldpc_raterecover(filename)
        
    pass