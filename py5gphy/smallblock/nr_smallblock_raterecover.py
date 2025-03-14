# -*- coding:utf-8 -*-
import numpy as np

def raterecover_smallblock(LLRin, N):
    """ small block rate match by 3GPP 38.212 5.4.3
    dn = raterecover_smallblock(LLRin, N)
    input:
        LLRin: E length input sequencce
        N: rate recover output length
    output:
        dn: N length seqeunce 0/1 bits
    """
    dn = np.zeros(N,'i1')
    
    E = LLRin.size

    if E <= N: #puncture
        #hard decode LLRin
        fe = np.zeros(E,'i1')
        fe[LLRin >= 0] = 0
        fe[LLRin < 0] = 1
        dn[0:E] = fe
    else: #repitition
        outLLR = np.zeros(N)
        offset = 0
        while offset + N <=E:
            outLLR += LLRin[offset : offset+N]
            offset += N
        if offset < E:
            len = E - offset
            outLLR[0:len] += LLRin[offset:]

        dn[outLLR >= 0] = 0
        dn[outLLR < 0] = 1
    
    return dn

if __name__ == "__main__":
    print("test smallblock rate recover")
    from tests.smallblock import test_smallblock_raterecover
    testlists = [([1,0,0,1], 3, [1,0,0]),
     ([1,0,0,1], 6, [1,0,0,1,1,0]),
     ]
    count = 0
    for ins, M, expected in testlists:
        print("smallblock rate recover,count= {}".format(count))
        count += 1
        test_smallblock_raterecover.test_smallblock_raterecover(ins, M, expected)