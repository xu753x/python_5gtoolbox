# -*- coding:utf-8 -*-
import numpy as np

def ratematch_smallblock(dn, E):
    """ small block rate match by 3GPP 38.212 5.4.3
    fe = ratematch_smallblock(dn, E)
    input:
        dn: N length input sequencce
        E: rate match output length
    output:
        fe: E length seqeunce 
    """

    N = dn.size

    if E <= N:
        fe = dn[0:E]
    else:
        M = np.ceil(E / N)
        d1 = list(dn) * int(M) #repeate dn M times
        fe = np.array(d1[0:E], 'i1')
    
    return fe

if __name__ == "__main__":
    print("test smallblock rate match")
    from tests.smallblock import test_smallblock_ratematch
    testlists = [([1,0,0,1], 3, [1,0,0]),
     ([1,0,0,1], 6, [1,0,0,1,1,0]),
     ]
    for ins, M, expected in testlists:
        test_smallblock_ratematch.test_smallblock_ratematch(ins, M, expected)