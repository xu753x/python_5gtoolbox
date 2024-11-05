# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_encode
from py5gphy.ldpc import nr_ldpc_cbsegment
from py5gphy.ldpc import nr_ldpc_ratematch

def DLSCHEncode(trblk, TBSize, Qm, coderateby1024, num_of_layers, rv, TBS_LBRM, G):
    """ complete one trblk processing of DLSCH CRC, LDPC encoder, rate match
    following to 38.212 7.2
    g_seq = DLSCHEncode(trblk, TBSize, Qm, coderateby1024, num_of_layers, rv, TBS_LBRM, G)
    input:
        trblk: tr block seq
        TBSize: trblk size
        Qm: modulation order
        coderateby1024: coderate * 1024
        num_of_layers: PDSCH layer number
        rv: redundancy versions
        TBS_LBRM: refer to 38.212 5.4.2.1, used for calculate circular buffer length
        G: the total number of coded bits available for transmission of the transport block
    output:
        g_seq: it sequence after code block concatenation
    """

    #7.2.1 Transport block CRC attachment
    assert len(trblk) == TBSize
    A = TBSize
    if A > 3824:
        blkandcrc = crc.nr_crc_encode(trblk, '24A')
    else:
        blkandcrc = crc.nr_crc_encode(trblk, '16')
    B = len(blkandcrc)

    #7.2.2 LDPC base graph selection
    bgn = 1
    if (A <= 292) \
            or ((A <= 3824) and (coderateby1024 <= 0.67*1024)) \
            or (coderateby1024 <= 0.25*1024):
        bgn = 2

    #7.2.3 Code block segmentation and code block CRC attachment
    cbs, Zc = nr_ldpc_cbsegment.ldpc_cbsegment(blkandcrc, bgn)   

    #7.2.4 Channel coding +7.2.5 rate matching + 7.2.6 code block concatenation
    g_seq = np.zeros(G, 'i1')
    g_offset = 0

    C = cbs.shape[0]
    Er_list = nr_ldpc_ratematch.get_Er_ldpc(G, C, Qm, num_of_layers)

    for c in range(C):
        ck = cbs[c,:]
        #7.2.4 Channel coding
        dn = nr_ldpc_encode.encode_ldpc(ck, bgn)
        N = dn.shape[0]

        #7.2.5 rate matching
        # cal Ncb, I_LBRM=1 for DL SCH
        Nref = math.floor(TBS_LBRM / (C * 2/3))
        Ncb = min(N, Nref)

        k0 = nr_ldpc_ratematch.get_k0(Ncb, bgn, rv, Zc)
        E = Er_list[c]
        fe = nr_ldpc_ratematch.ratematch_ldpc(dn, Ncb, E, k0, Qm)

        #7.2.6 code block concatenation
        g_seq[g_offset : g_offset + E] = fe
        g_offset += E
    
    return g_seq


if __name__ == "__main__":
    print("test nr DLSCH")
    from tests.nr_pdsch import test_nr_dlsch
    file_lists = test_nr_dlsch.get_testvectors()

    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dlsch.test_nr_dlsch_without_matlab_Nref_value(filename)

    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dlsch.test_nr_dlsch_parameter(filename)
    
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dlsch.test_nr_dlsch_with_matlab_Nref(filename)

    