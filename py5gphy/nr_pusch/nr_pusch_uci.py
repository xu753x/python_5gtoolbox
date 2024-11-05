# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.nr_pusch import nr_ulsch
from py5gphy.nr_pusch import nr_ulsch_info
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch_datactrl_multiplex
from py5gphy.crc import crc
from py5gphy.smallblock import nr_smallblock_encoder
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_ratematch
from py5gphy.polar import nr_polar_cbsegment
import math


def encode_uci_on_ulsch(UCIbits, NumUCIBits, Etot, Qm):
    """following to 38.212 6.3.1.2 - 6.3.1.6 
    UCI encoding processing
    """
       
    A = NumUCIBits
    if A <= 11:
        #small block lengths
        #6.3.1.2.2 UCI encoded by channel coding of small block lengths, no CRC
        c_seq = UCIbits
        #6.3.1.3.2 UCI encoded by channel coding of small block lengths
        d_seq = nr_smallblock_encoder.encode_smallblock(c_seq,Qm)
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


def ULSCHandUCIProcess(pusch_config, trblk, Gtotal, rv, DMRS_symlist):
    """ ULSCH and UCI bit processing"""
    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)
    EnableULSCH = pusch_config['EnableULSCH']
    
    #ULSCH CRC and codeblock segment, cbs(code blocks) is used to calculate UCI resources
    if EnableULSCH == 1:
        cbs, Zc, bgn = nr_ulsch.ULSCH_Crc_CodeBlockSegment(trblk, TBSize, coderateby1024)
        #get total bits size of ULSCH code block
        ULSCH_size = cbs.shape[0] * cbs.shape[1]
    else:
        ULSCH_size = 0

    EnableACK = pusch_config['EnableACK']
    NumACKBits = pusch_config['NumACKBits']
    EnableCSI1 = pusch_config['EnableCSI1']
    NumCSI1Bits = pusch_config['NumCSI1Bits']
    EnableCSI2 = pusch_config['EnableCSI2']
    NumCSI2Bits = pusch_config['NumCSI2Bits']
    num_of_layers = pusch_config['num_of_layers']
    
    RMinfo = nr_ulsch_info.getULSCH_RM_info(pusch_config, DMRS_symlist,ULSCH_size, Qm, coderateby1024,Gtotal)
    
    if EnableULSCH == 1:
        #ULSCH LDPC encode, rate matching and code block concatenation from 6.2.4 to 6.2.6
        g_ulsch = nr_ulsch.ULSCH_ldpc_ratematch(cbs, Zc, bgn, Qm, RMinfo['G_ULSCH'], num_of_layers, rv)
    else:
        g_ulsch = np.array([])

    if EnableACK*NumACKBits >0:
        ACKbits = pusch_config['ACKbits']
        assert NumACKBits == len(ACKbits)
        g_ack = encode_uci_on_ulsch(ACKbits, NumACKBits, RMinfo['Euci_ack'], Qm)
    else:
        g_ack = np.array([])
    
    if EnableCSI1*NumCSI1Bits >0:
        CSI1bits = pusch_config['CSI1bits']
        assert NumCSI1Bits == len(CSI1bits)
        g_csi1 = encode_uci_on_ulsch(CSI1bits, NumCSI1Bits, RMinfo['Euci_CSI1'], Qm)
    else:
        g_csi1 = np.array([])
    
    if EnableCSI2*NumCSI2Bits >0:
        CSI2bits = pusch_config['CSI2bits']
        assert NumCSI2Bits == len(CSI2bits)
        g_csi2 = encode_uci_on_ulsch(CSI2bits, NumCSI2Bits, RMinfo['Euci_CSI2'], Qm)
    else:
        g_csi2 = np.array([])
    
    #6.2.7 Data and control multiplexing
    g_seq = nr_pusch_datactrl_multiplex.data_control_multiplex( 
        g_ulsch, g_ack, g_csi1, g_csi2, pusch_config, Gtotal,
        DMRS_symlist,RMinfo, Qm)

    return g_seq

if __name__ == "__main__":
    print("test nr ULSCH with UCI")
    from tests.nr_pusch import test_ulsch_with_uci
    file_lists = test_ulsch_with_uci.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_ulsch_with_uci.test_nr_ulsch_with_uci(filename)