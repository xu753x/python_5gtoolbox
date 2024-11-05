# -*- coding:utf-8 -*-

import numpy as np

def genNnvalue(K, E, nMax):
    """ return N and n value following TS38.212 5.3.1 first part
    [N, n] = genNnvalue(K, E, nMax)
    input:
        K: input bit size
        E: rate match output size
        nMax: maimum n value(either 9 or 10)
    output:
        N: polor code output size
        n: log2(N)
    """
    clog2e = int(np.ceil(np.log2(E)))

    if(E <= ((9/8) * 2 ** (clog2e - 1))) and ((K/E) < (9/16)):
        n1 = clog2e - 1
    else:
        n1 = clog2e

    rmin = 1/8
    n2 = int(np.ceil(np.log2(K/rmin)))

    min1 = min(n1, n2, nMax)

    n = max(min1, 5) #nmin = 5

    N = 2 ** n

    return N, n

if __name__ == "__main__":
    # expected [256, 8]
    [N, n] = genNnvalue(20,300,9)

    # expected [512, 9]
    [N, n] = genNnvalue(200,400,10)

    # expected [1024, 10]
    [N, n] = genNnvalue(456,1200,10)

    [N, n] = genNnvalue(30,70,9)

    pass
