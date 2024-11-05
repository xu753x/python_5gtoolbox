# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.polar import polar_interleaver
from py5gphy.polar import polar_construct
from py5gphy.polar import gen_kron_matrix

def encode_polar(inbits, E, nMax, iIL):
    """ Encode one polor block follwing TS38.212 5.3.1,
    Input is a single code block and assumes CRC bits are included
    input:
        inbits: np.array int8, 1 X K size of 1/0 bits
        E: rate match output length
        (nMax, iIL): (9, 1) apply for DL and (10, 0) apply for UL
    output:
        outbits: np.array int8, 1 X N size of 1/0 bits

    """

    # make sure all input data value are 0 or 1
    assert (not np.any(np.nonzero(inbits < 0))) \
       and (not np.any(np.nonzero(inbits > 1)))

    assert [nMax, iIL] in [[9, 1], [10, 0]]

    K = inbits.size  # input bits size

    if iIL:
        in_itrl = polar_interleaver.interleave(inbits, K)
    else:
        in_itrl = inbits

    #get F array, PC array and other values
    F, qPC, N, nPC, nPCwm = polar_construct.construct(K, E, nMax)

    # generate u
    u = np.zeros(N,'i2')
    if nPC == 0:
        k = 0
        for idx in range(N):
            if F[idx] == 0:  #information bit
                u[idx] = in_itrl[k]
                k += 1
    else:  #nPC > 0
        y0 = y1 = y2 = y3 = y4 =0
        k = 0
        for idx in range(N):
            yt = y0; y0 = y1; y1 = y2; y2 = y3; y3 = y4; y4 = yt
            if F[idx] == 0:  #information bit
                if idx in qPC:
                    u[idx] = y0
                else:
                    u[idx] = in_itrl[k]
                    k += 1
                    y0 = y0 ^ u[idx]


    #get G
    G = gen_kron_matrix.gen_kron(N)

    #u*G then mod 2
    outbits = (u @ G) % 2
    return outbits.astype('i1')
    

if __name__ == "__main__":
    inbits = np.array([1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0])
    outbits = encode_polar(inbits, 150, 9, 1)
    assert np.array_equal(outbits, np.array([1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0], 'i1'))

    from scipy import io
    import os
    print("test polar encode")
    from tests.polar import test_polar_encoder
    file_lists = test_polar_encoder.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_polar_encoder.test_nr_polar_encoder(filename)

    pass