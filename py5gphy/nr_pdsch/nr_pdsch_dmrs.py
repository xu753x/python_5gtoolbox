# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nrModulation
from py5gphy.common import nr_slot

def _gen_seq(nSCID, nNIDnSCID, DMRSRE_startpos, DMRS_RESize, slot, sym):
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

def pdsch_dmrs_process(fd_slot_data,RE_usage_inslot, pdsch_config, precoding_matrix, num_of_ant, slot):
    """ DMRS generation, precoding and resource mapping following to 38.211 7.4.1.1
    fd_slot_data,RE_usage_inslot= pdsch_dmrs_process(fd_slot_data,RE_usage_inslot, 
            pdsch_config, precoding_matrix, num_of_ant, slot)
    """
    RBStart = pdsch_config['ResAlloType1']['RBStart']
    RBSize = pdsch_config['ResAlloType1']['RBSize']
    DMRS_config = pdsch_config["DMRS"]
    PortIndexList = pdsch_config["PortIndexList"]
    num_of_layers = pdsch_config['num_of_layers']
    StartSymbolIndex = pdsch_config["StartSymbolIndex"]
    NrOfSymbols = pdsch_config["NrOfSymbols"]

    Ld = StartSymbolIndex + NrOfSymbols #38.211 Table 7.4.1.1.2-3: PDSCH DM-RS positions l for single-symbol DM-RS.
    
    
    DMRSConfigType = DMRS_config["DMRSConfigType"]
    assert DMRSConfigType == 1
    NrOfDMRSSymbols = DMRS_config["NrOfDMRSSymbols"]
    assert NrOfDMRSSymbols == 1
    PDSCHMappintType = DMRS_config["PDSCHMappintType"]
    assert PDSCHMappintType == "A"
    DMRSAddPos = DMRS_config["DMRSAddPos"]
    assert DMRSAddPos <= 3
    NumCDMGroupsWithoutData = DMRS_config["NumCDMGroupsWithoutData"]
    nSCID = DMRS_config["nSCID"]
    nNIDnSCID = DMRS_config["nNIDnSCID"]

    #gen DMRS symb list, by 38.211 Table 7.4.1.1.2-3: PDSCH DM-RS positions l for single-symbol DM-RS
    if Ld <=7:
        DMRS_symlist = [2]
    elif Ld <=9:
        if DMRSAddPos==0:
            DMRS_symlist = [2]    
        else:
            DMRS_symlist = [2,7]
    elif Ld <=11:
        if DMRSAddPos==0:
            DMRS_symlist = [2]    
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 9]
        else:
            DMRS_symlist = [2,6,9]
    elif Ld ==12:
        if DMRSAddPos==0:
            DMRS_symlist = [2]    
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 9]
        elif DMRSAddPos == 2:
            DMRS_symlist = [2, 6,9]
        else:
            DMRS_symlist = [2,5,8,11]
    else:
        #for Ld = 13,14
        if DMRSAddPos==0:
            DMRS_symlist = [2]
        elif DMRSAddPos == 1:
            DMRS_symlist = [2, 11]
        elif DMRSAddPos == 2:
            DMRS_symlist = [2, 7, 11]
        elif DMRSAddPos == 3:
            DMRS_symlist = [2, 5, 8, 11]
    
    #following to 38.214 table 4.1-1, get PDSCH DMRS scaling factor
    if NumCDMGroupsWithoutData == 1:
        DMRS_scaling = 1 #0db EPRE ratio
    else:
        DMRS_scaling = 10 ** (-3/20) #-3db EPRE ratio
    
    DMRSReferencePoint = DMRS_config["DMRSReferencePoint"]
    if DMRSReferencePoint == "CRB0":
        # should be subcarrier 0 in common resource block 0
        prbrefpoint = 0
    elif DMRSReferencePoint == "CORESET0":
        #subcarrier 0 of the lowest-numbered resource block in CORESET 0 if the corresponding PDCCH is associated
        #with CORESET 0 and Type0-PDCCH common search space and is addressed to SI-RNTI
        #TODO: add CORESET0 PRB later
        prbrefpoint = 0
    DMRSRE_startpos = (prbrefpoint+RBStart) * 6
    DMRS_RESize = RBSize * 6 # for DMRSConfigType 1 

    carrier_RE_size = len(fd_slot_data[0,:]) // 14

    ##### main processing #######
    
    # handling PDSCH DMRS conflict with CSI-RS and SSB:
    # (1)DMRS shall skip SSB PRB (2) error if DMRS overlap with CSI-RS RE
    # it is OK if DMRS and CSI-RS occupy the same PRB but different REs
    #spec description:
    # from 38.211 7.4.1.1.2 Mapping to physical resources: The UE may assume that no DM-RS collides with the SS/PBCH block.
    #38.214 5.1.4 PDSCH resource mapping: A UE is not expected to handle the case where PDSCH DM-RS REs are overlapping, 
    # even partially, with any RE(s) not available for PDSCH

    ###  fill RE_map_in_PRB
    no_pdsch_value = nr_slot.get_REusage_value('PDSCH-DMRS-RSV')
    pdsch_dmrs_value = nr_slot.get_REusage_value('PDSCH-DMRS')
    #gen RE type mapping to DMRS PRB
    RE_map_in_PRB = np.zeros((num_of_layers,12),'i1')
    if NumCDMGroupsWithoutData == 2:
        #PDSCH data can not map to any RE if NumCDMGroupsWithoutData==2
        RE_map_in_PRB[:,:] = no_pdsch_value
    
    for m in range(num_of_layers):
        p = PortIndexList[m]
        d0 = p - 1000
        RE_map_in_PRB[d0,(d0//2) % 2::2] = pdsch_dmrs_value

    csirs_value = nr_slot.get_REusage_value('CSI-RS')
    ssb_value = nr_slot.get_REusage_value('SSB')

    ### DMRS procssing 38.211 7.4.1.1
    for sym in DMRS_symlist:
        start_pos = sym*carrier_RE_size + RBStart*12
        #generate DMRS seq
        DMRS_seq = _gen_seq(nSCID, nNIDnSCID, DMRSRE_startpos, DMRS_RESize, slot, sym)

        #resource mapping
        DMRS_data = np.zeros((num_of_layers, DMRS_RESize*2), 'c8')
        for m in range(num_of_layers):
            port = PortIndexList[m]
            #38.211 Table 7.4.1.1.2-1: Parameters for PDSCH DM-RS configuration type 1.
            d0 = port - 1000
            delta = (d0//2) % 2
            wf = [1, 1 - (d0 % 2)*2] 
            wt = 1 #support single symbol only : l' = 0 only

            DMRS_data[m, 0+delta::4] = DMRS_scaling * wf[0] * wt* DMRS_seq[0::2]
            DMRS_data[m, 2+delta::4] = DMRS_scaling * wf[1] * wt* DMRS_seq[1::2]
            
            #check if collide with CSI-RS
            mapping_RE = RE_usage_inslot[:, start_pos+delta : start_pos + RBSize*12 : 2]
            if np.count_nonzero(mapping_RE == csirs_value):
                assert 0
        
        #precoding 
        precoded = np.zeros((num_of_ant, RBSize*12), 'c8')
        if not precoding_matrix:
            precoded[0:num_of_layers,:] = DMRS_data
    
        sel_precoding_matrix = np.array(precoding_matrix)
        sel_pmi = sel_precoding_matrix[0:num_of_ant,0:num_of_layers]
        precoded = sel_pmi @ DMRS_data

        #mapping to fd_slot_data
        # PDSCH DMRS should avoid map to SSB PRB, and DMRS should not collide with CSI-RS PRB
        
        pdsch_re_mapping = RE_usage_inslot[:, start_pos : start_pos + RBSize*12]
        
        for prb in range(RBStart, RBStart+RBSize):
            start_pos = sym*carrier_RE_size + prb*12
            pdsch_re_mapping = RE_usage_inslot[:, start_pos : start_pos + 12]
            #skip if SSB PRB
            if np.count_nonzero(pdsch_re_mapping[0,:]==ssb_value) == 0:
                #not SSB PRB, map data
                fd_slot_data[:, start_pos : start_pos + 12] = precoded[:,(prb-RBStart)*12:(prb-RBStart)*12+12]
                pdsch_re_mapping[0:num_of_layers,:] = RE_map_in_PRB
    
    return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    from tests.nr_pdsch import test_nr_pdsch
    file_lists = test_nr_pdsch.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pdsch.test_nr_pdsch(filename)