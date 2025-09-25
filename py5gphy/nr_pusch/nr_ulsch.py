# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_encode
from py5gphy.ldpc import nr_ldpc_cbsegment
from py5gphy.ldpc import nr_ldpc_ratematch
from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import nr_ldpc_decode
from py5gphy.ldpc import nr_ldpc_raterecover

def ULSCH_Crc_CodeBlockSegment(trblk, TBSize, coderateby1024):
    """ CRC calculation and code block segment and code bloc CRC attach
    """
    #38.212 6.2.1 Transport block CRC attachment
    assert len(trblk) == TBSize
    A = TBSize
    if A > 3824:
        blkandcrc = crc.nr_crc_encode(trblk, '24A')
    else:
        blkandcrc = crc.nr_crc_encode(trblk, '16')
    B = len(blkandcrc)

    #6.2.2 LDPC base graph selection
    bgn = 1
    if (A <= 292) \
            or ((A <= 3824) and (coderateby1024 <= 0.67*1024)) \
            or (coderateby1024 <= 0.25*1024):
        bgn = 2

    #7.2.3 Code block segmentation and code block CRC attachment
    cbs, Zc = nr_ldpc_cbsegment.ldpc_cbsegment(blkandcrc, bgn)   

    return cbs, Zc, bgn

def ULSCH_encoding_ratematch(cbs, Zc, bgn, Qm, G_ULSCH, num_of_layers, rv):
    """ LDPC encoding and rate matching for each code block, 
    then Code block concatenation
    """
    #6.2.4 Channel coding +7.2.5 rate matching + 7.2.6 code block concatenation
    g_seq = np.zeros(G_ULSCH, 'i1')
    g_offset = 0

    C = cbs.shape[0]
    Er_list = nr_ldpc_ratematch.get_Er_ldpc(G_ULSCH, C, Qm, num_of_layers)

    for c in range(C):
        ck = cbs[c,:]
        #6.2.4 Channel coding
        dn = nr_ldpc_encode.encode_ldpc(ck, bgn)
        N = dn.shape[0]

        #6.2.5 rate matching
        # cal Ncb, support I_LBRM=0 only for UL SCH
        #3gpp spec support I_LBRM=0 and I_LBRM =1 case by setting limitedBufferRM
        #but usually gNB side momory is assumed to be unlimited
        Ncb = N

        k0 = nr_ldpc_ratematch.get_k0(Ncb, bgn, rv, Zc)
        E = Er_list[c]
        fe = nr_ldpc_ratematch.ratematch_ldpc(dn, Ncb, E, k0, Qm)

        #6.2.6 code block concatenation
        g_seq[g_offset : g_offset + E] = fe
        g_offset += E
    
    return g_seq


if __name__ == "__main__":
    print("test nr ULSCH without UCI")
    from tests.nr_pusch import test_ulsch_without_uci
    import time
    file_lists = test_ulsch_without_uci.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        start = time.time()
        test_ulsch_without_uci.test_nr_ulsch_without_uci(filename)
        print("ulsch elpased time: {:6.2f}".format(time.time() - start))

    