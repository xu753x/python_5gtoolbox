# -*- coding:utf-8 -*-

import numpy as np
import math
from py5gphy.smallblock import nr_smallblock_encoder
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_ratematch
from py5gphy.polar import nr_polar_cbsegment

def encode_uci(UCIbits, NumUCIBits, Etot):
    """following to 38.212 6.3.1.2 - 6.3.1.6 
    UCI encoding processing
    """
       
    A = NumUCIBits
    if A <= 11:
        #small block lengths
        #6.3.1.2.2 UCI encoded by channel coding of small block lengths, no CRC
        c_seq = UCIbits
        #6.3.1.3.2 UCI encoded by channel coding of small block lengths
        d_seq = nr_smallblock_encoder.encode_smallblock(c_seq,Qm=2)
        #6.3.1.4.2 UCI encoded by channel coding of small block lengths
        repeats = np.tile(d_seq, math.ceil(Etot/len(d_seq)))
        f_seq = repeats[0:Etot]
        #6.3.1.5 Code block concatenation
        g_seq = f_seq
    else:
        g_seq = np.zeros(Etot, 'i1')
        #polar code block segment and add CRC at the end of cb block
        polar_cb_blks, C, Er = nr_polar_cbsegment.polar_cbsegment(UCIbits, Etot)

        for m in range(C):
            #6.3.1.3.1 UCI encoded by Polar code
            nMax = 10
            iIL = 0
            dn = nr_polar_encoder.encode_polar(polar_cb_blks[m,:], Er, nMax, iIL)
            #6.3.1.4.1 UCI encoded by Polar code
            iBIL = 1
            K = len(polar_cb_blks[m,:])
            f_seq = nr_polar_ratematch.ratematch_polar(dn, K, Er, iBIL)
            #6.3.1.5 Code block concatenation
            g_seq[m*Er : (m+1)*Er] = f_seq
    return g_seq
