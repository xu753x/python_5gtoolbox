# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.nr_pusch import nr_ulsch
from py5gphy.nr_pusch import nr_ulsch_decode
from py5gphy.nr_pusch import nr_ulsch_info
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch_datactrl_multiplex
from py5gphy.crc import crc
from py5gphy.smallblock import nr_smallblock_encoder
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_ratematch
from py5gphy.polar import nr_polar_cbsegment
from py5gphy.nr_pusch import nr_pusch_dmrs


def ULSCHandUCIDecodeProcess(LLr,pusch_config, rv, LDPC_decoder_config,HARQ_on=False,current_LLr_dns=np.array([])):
    """ ULSCH and UCI decoding processing
    """
    Gtotal = LLr.size

    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    DMRSAddPos = pusch_config["DMRS"]["DMRSAddPos"]

    Ld = StartSymbolIndex + NrOfSymbols

    DMRS_symlist =nr_pusch_dmrs.get_DMRS_symlist(Ld,DMRSAddPos)
   
    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)
    EnableULSCH = pusch_config['EnableULSCH']
    
    #ULSCH CRC and codeblock segment, cbs(code blocks) is used to calculate UCI resources
    #below code is to calculate ULSCH_size by calling ULSCH_Crc_CodeBlockSegment method to process all zero input data. it could have a better way to get this value
    if EnableULSCH == 1:
        cbs, Zc, bgn = nr_ulsch.ULSCH_Crc_CodeBlockSegment(np.zeros(TBSize,'i1'), TBSize, coderateby1024)
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

    g_ulsch, g_ack, g_csi1, g_csi2 = nr_pusch_datactrl_multiplex.data_control_separate(LLr, pusch_config,
        DMRS_symlist,RMinfo, Qm)
    
    #right now the code only process ULSCH data, will add UCI bit processing later
    if EnableULSCH == 1:
        #decode ULSCH
        ulsch_status, tbblk,ulsch_new_LLr_dns = nr_ulsch_decode.ULSCH_decoding(g_ulsch,TBSize, coderateby1024, Qm, RMinfo['G_ULSCH'], num_of_layers, rv,LDPC_decoder_config,HARQ_on,current_LLr_dns)
    
        return ulsch_status, tbblk,ulsch_new_LLr_dns
    else:
        return False, np.array([]),np.array([])

if __name__ == "__main__":

    if 1:
        print("test nr ULSCH no UCI decoder")
        from tests.nr_pusch import test_ulsch_without_uci_decode
        file_lists = test_ulsch_without_uci_decode.get_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_ulsch_without_uci_decode.test_nr_ulsch_without_uci_decode(filename)
    
    if 1:
        print("test nr ULSCH with UCI decoder")
        from tests.nr_pusch import test_ulsch_with_uci_decode
        file_lists = test_ulsch_with_uci_decode.get_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_ulsch_with_uci_decode.test_nr_ulsch_with_uci_decode(filename)