# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import lowPAPR_seq
from py5gphy.common import nrModulation
from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch_precoding

def process(fd_slot_data,RE_usage_inslot, pusch_config, slot):
    """ DMRS generation, precoding and resource mapping following to 38.211 7.4.1.1
    fd_slot_data,RE_usage_inslot= pusch_dmrs_process(fd_slot_data,RE_usage_inslot, 
            pusch_config, precoding_matrix, slot)
    """
    RBStart = pusch_config['ResAlloType1']['RBStart']
    RBSize = pusch_config['ResAlloType1']['RBSize']
    DMRS_config = pusch_config["DMRS"]
    PortIndexList = pusch_config["PortIndexList"]
    num_of_layers = pusch_config['num_of_layers']
    nTransPrecode = pusch_config['nTransPrecode']
    NrOfSymbols = pusch_config['NrOfSymbols']
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    nPMI = pusch_config['nPMI']

    DMRSConfigType = DMRS_config["DMRSConfigType"]
    assert DMRSConfigType == 1
    NrOfDMRSSymbols = DMRS_config["NrOfDMRSSymbols"]
    assert NrOfDMRSSymbols == 1
    PDSCHMappintType = DMRS_config["PUSCHMappintType"]
    assert PDSCHMappintType == "A"
    DMRSAddPos = DMRS_config["DMRSAddPos"]
    assert DMRSAddPos <= 3
    NumCDMGroupsWithoutData = DMRS_config["NumCDMGroupsWithoutData"]
    dmrs_TypeA_Position = DMRS_config["dmrs_TypeA_Position"]
    assert dmrs_TypeA_Position == 'pos2'
    nSCID = DMRS_config["nSCID"]
    if nSCID == 0:
        nNIDnSCID = DMRS_config["transformPrecodingDisabled"]["NID0"]
    else:
        nNIDnSCID = DMRS_config["transformPrecodingDisabled"]["NID1"]
    
    nPuschID = DMRS_config["transformPrecodingEnabled"]["nPuschID"]
    groupOrSequenceHopping = DMRS_config["transformPrecodingEnabled"]["groupOrSequenceHopping"]

    #gen DMRS symb list from 38.211 Table 6.4.1.1.3-3:,support only dmrs_TypeA_Position==pos2 and PUSCH mapping type A
    if NrOfSymbols <= 7:
        DMRS_symlist = [2]
    elif NrOfSymbols <= 9:
        if DMRSAddPos == 0:
            DMRS_symlist = [2]
        else:
            DMRS_symlist = [2, 7]
    elif NrOfSymbols <= 11:
        if DMRSAddPos == 0:
            DMRS_symlist = [2]
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 9]
        else:
            DMRS_symlist = [2, 6, 9]
    elif NrOfSymbols == 12:
        if DMRSAddPos == 0:
            DMRS_symlist = [2]
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 9]
        elif DMRSAddPos == 2:
            DMRS_symlist = [2, 6, 9]
        else:
            DMRS_symlist = [2, 5, 8, 11]
    else:
        if DMRSAddPos==0:
            DMRS_symlist = [2]
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 11]
        elif DMRSAddPos == 2:
            DMRS_symlist = [2, 7, 11]
        elif DMRSAddPos == 3:
            DMRS_symlist = [2, 5, 8, 11]
    
    #following to 38.214 Table 6.2.2-1: The ratio of PUSCH EPRE to DM-RS EPRE, get PUSCH DMRS scaling factor
    if NumCDMGroupsWithoutData == 1:
        DMRS_scaling = 1 #0db EPRE ratio
    else:
        DMRS_scaling = 10 ** (-3/20) #-3db EPRE ratio
    
    DMRSRE_startpos = RBStart * 6
    DMRS_RESize = RBSize * 6 # for DMRSConfigType 1 

    carrier_RE_size = len(fd_slot_data[0,:]) // 14

    ##### main processing #######
    ### DMRS procssing 38.211 7.4.1.1
    precoding_matrix = nr_pusch_precoding.get_precoding_matrix(num_of_layers, nNrOfAntennaPorts, nPMI)
    for sym in DMRS_symlist:
        #generate DMRS seq
        if nTransPrecode == 0: #transform precoding disabled
            DMRS_seq = _gen_seq_without_transform_precoding(nSCID, nNIDnSCID, DMRSRE_startpos, DMRS_RESize, slot, sym)
        else:
            DMRS_seq = _gen_seq_with_transform_precoding(nPuschID, groupOrSequenceHopping, DMRS_RESize, slot, sym)

        #resource mapping
        DMRS_data = np.zeros((num_of_layers, RBSize*12), 'c8')
        for m in range(num_of_layers):
            port = PortIndexList[m]
            #38.211 Table 7.4.1.1.2-1: Parameters for PDSCH DM-RS configuration type 1.
            d0 = port - 1000
            delta = (d0//2) % 2
            wf = [1, 1 - (d0 % 2)*2] 
            wt = 1 #support single symbol only : l' = 0 only

            DMRS_data[m, 0+delta::4] = DMRS_scaling * wf[0] * wt* DMRS_seq[0::2]
            DMRS_data[m, 2+delta::4] = DMRS_scaling * wf[1] * wt* DMRS_seq[1::2]

            RE_usage_inslot[m:, sym*carrier_RE_size + RBStart*12 + delta : sym*carrier_RE_size + (RBStart+RBSize)*12 : 2] \
                    = nr_slot.get_REusage_value('PUSCH-DMRS')
            if NumCDMGroupsWithoutData == 2:
                #PUSCH data can not map to any RE if NumCDMGroupsWithoutData==2
                assert delta in [0,1]
                RE_usage_inslot[m:, sym*carrier_RE_size + RBStart*12 + (1-delta) : sym*carrier_RE_size + (RBStart+RBSize)*12 : 2] \
                        = nr_slot.get_REusage_value('PUSCH-DMRS-RSV')
        
        #precoding 
        precoded = np.zeros((nNrOfAntennaPorts, RBSize*12), 'c8')
        precoded = precoding_matrix @ DMRS_data

        #mapping to fd_slot_data
        fd_slot_data[:, sym*carrier_RE_size + RBStart*12 : sym*carrier_RE_size + (RBStart+RBSize)*12] = precoded

        DMRSinfo = {}
        DMRSinfo['DMRS_symlist'] = DMRS_symlist
    return fd_slot_data, RE_usage_inslot, DMRSinfo

def _gen_seq_without_transform_precoding(nSCID, nNIDnSCID, DMRSRE_startpos, DMRS_RESize, slot, sym):
    """ generate DMRS sequence r(n) following to 38.211 7.4.1.1.1
    DMRSRE_startpos: PDSCH DMRS RE start position
    """
    
    tmp1 = ((14*slot + sym + 1)*(2*nNIDnSCID + 1)) << 17
    tmp2 = 2*nNIDnSCID + nSCID
    cinit = (tmp1 + tmp2) % (2**31)
    
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, 2*(DMRSRE_startpos+DMRS_RESize))
    sel_seq = prbs_seq[2*DMRSRE_startpos:]
    DMRSseq = nrModulation.nrModulate(sel_seq, 'QPSK')
    return DMRSseq

def _gen_seq_with_transform_precoding(nPuschID, groupOrSequenceHopping, DMRS_RESize, slot, sym):
    #6.4.1.1.1.2 Sequence generation when transform precoding is enabled
    alpha = 0
    fgh = 0
    v = 0
    if groupOrSequenceHopping == 'groupHopping':
        fgh = _gen_fgh(slot,sym,nPuschID)
    elif groupOrSequenceHopping == 'sequenceHopping':
        if DMRS_RESize >= 6*12:
            v = _gen_v(slot,sym,nPuschID)
    u = (fgh + nPuschID) % 30        
    ruv = lowPAPR_seq.gen_lowPAPR_seq(u,v,alpha,DMRS_RESize)
    return ruv

def _gen_fgh(slot,sym,nPuschID):
    """generate fgh when groupOrSequenceHopping equals 'groupHopping',
    """
    #generate one frame of pseudo-random sequence
    cinit = int(nPuschID // 30)
    seq = nrPRBS.gen_nrPRBS(cinit, 8*20*14)

    sel_seq = seq[8*(slot*14+sym):8*(slot*14+sym)+8]
    fgh = sum(sel_seq*(2**np.arange(8))) % 30
    return fgh

def _gen_v(slot,sym,nPuschID):
    """generate v when groupOrSequenceHopping equals 'sequenceHopping',
    when MSRS_sc_b >= 6*12
    """
    #generate one frame of pseudo-random sequence
    seq = nrPRBS.gen_nrPRBS(nPuschID, 20*14)

    v = seq[slot*14+sym]
    return v

if __name__ == "__main__":
    print("test nr PUSCh DMRS")
    from tests.nr_pusch import test_nr_pusch_dmrs
    file_lists = test_nr_pusch_dmrs.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        if count == 703:
            setbreakpoint = 1
        count += 1
        test_nr_pusch_dmrs.test_nr_ulsch_dmrs(filename)
    