# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_decode
from py5gphy.ldpc import nr_ldpc_cbsegment
from py5gphy.ldpc import nr_ldpc_ratematch
from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import nr_ldpc_raterecover

def DLSCHDecode(LLr,TBSize, Qm, coderateby1024, num_of_layers, rv, TBS_LBRM, LDPC_decoder_config,HARQ_on=False,current_LLr_dns=np.array([])):
    """ DLSCH receiving processing, including de-rate matching, LDPC decoder,CRC decoder"""

    G = LLr.size
    #get Transport block plus CRC size
    A = TBSize
    if A > 3824:
        B = A + 24
        tbcrcpoly = '24A'
    else:
        B=A+16
        tbcrcpoly = '16'

    # 7.2.2 LDPC base graph selection
    bgn = 1
    if (A <= 292) \
            or ((A <= 3824) and (coderateby1024 <= 0.67*1024)) \
            or (coderateby1024 <= 0.25*1024):
        bgn = 2

    #Get information of code block segments
    #C: num of CB, 
    #  cbz: Number of bits in each code block (excluding CB-CRC bits and filler bits)
    #  L: Number of parity bits in each code block
    #  F: Number of filler bits in each code block
    #  K: Number of bits in each code block (including CB-CRC bits and filler bits)
    #  Zc: minimum value of Z in all sets of lifting sizes in Table 5.3.2-1
    C, cbz, L, F, K, Zc = ldpc_info.get_cbs_info(B, bgn)
    
    K_apo = cbz + L #filler bit location of CB segment output is from K_apo to K

    if bgn == 1:
        N = 66 * Zc
    else:
        N = 50 * Zc

    # cal Ncb, I_LBRM=1 for DL SCH
    Nref = math.floor(TBS_LBRM / (C * 2/3))
    Ncb = min(N, Nref)

    k0 = nr_ldpc_ratematch.get_k0(Ncb, bgn, rv, Zc)

    #Er list is rate matching output len for each code block, this value could be different by 1 for different code block
    Er_list = nr_ldpc_ratematch.get_Er_ldpc(G, C, Qm, num_of_layers)

    tbblkandcrc = np.zeros(B)
    tb_offset = 0
    g_offset = 0
    new_LLr_dns = np.zeros((C,N))
    for c in range(C):
        E = Er_list[c]
        #get RM output code block
        LLr_fe = LLr[g_offset:g_offset+E]
        g_offset += E

        #de-rate matching
        LLr_dn = nr_ldpc_raterecover.raterecover_ldpc(LLr_fe, Ncb, N, k0, Qm,Zc,K_apo,K)

        new_LLr_dns[c,: ] = LLr_dn
        #HARQ combine
        if HARQ_on:
            if current_LLr_dns.size == 0:
                #first tx
                new_LLr_dns[c,:] = LLr_dn
                current_LLr_dn = LLr_dn
            else:
                #HARQ combine
                for m in range(LLr_dn.size):
                    if LLr_dn[m]==0 or current_LLr_dns[c,m] == 0:
                        #any value = 0 means this bit is punctured
                        new_LLr_dns[c,m] = LLr_dn[m] + current_LLr_dns[c,m]
                    else:
                        #no zero value, get average value
                        new_LLr_dns[c,m] = (LLr_dn[m] + current_LLr_dns[c,m])/2
        else:
            new_LLr_dns[c,:] = LLr_dn
            
        #ldpc decoder
        blkandcrc, ck, status = nr_ldpc_decode.nr_decode_ldpc(new_LLr_dns[c,:], Zc, bgn, LDPC_decoder_config["L"], algo=LDPC_decoder_config["algo"],alpha=LDPC_decoder_config["alpha"], beta=LDPC_decoder_config["beta"])

        if C > 1:
            #CB crc decoder by removing filler bits
            cbblk,crc_err = crc.nr_crc_decode(blkandcrc[0:K_apo],'24B')
            #if crc_err:
            #    return False,np.zeros(TBSize,'i8'),new_LLr_dns
        else:
            cbblk = blkandcrc[0:K_apo]
        
        #add to TB blk
        tbblkandcrc[tb_offset:tb_offset+cbz] = cbblk
        tb_offset += cbz
    
    #TB blk CRC decode
    tbblk, tbcrc_error = crc.nr_crc_decode(tbblkandcrc,tbcrcpoly)
    

    return tbcrc_error==0, tbblk, new_LLr_dns

if __name__ == "__main__":
    print("test nr DLSCH Rx processing")
    from tests.nr_pdsch import test_nr_dlsch_decode
    file_lists = test_nr_dlsch_decode.get_testvectors()

    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dlsch_decode.test_nr_dlsch_rx_with_matlab_Nref(filename)