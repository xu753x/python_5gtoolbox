# -*- coding:utf-8 -*-

import numpy as np
import copy

from py5gphy.common import nr_slot
from py5gphy.nr_pdsch import nr_pdsch_dmrs

def pdsch_data_re_mapping_prepare(RE_usage_inslot, pdsch_config):
    """ calculate total RE number that PDSCH data can map to,
        and add PDSCH RE type value to those RE
        this function should be called after SSB, PDCCH, CDI-RS, PDSCH-DMRS resouce mapping
    RE_usage_inslot, pdsch_data_RE_num = pdsch_data_re_mapping_prepare(RE_usage_inslot, pdsch_config)
    input:
        RE_usage_inslot: 14sym X REsize, indicate RE usage for each RE
    output:
        RE_usage_inslot: add PDSCH data RE type into RE_usage_inslot
        pdsch_RE_num: number of RE used by PDSCH data mapping, used for rate matching

    """
    #get info
    StartSymbolIndex = pdsch_config['StartSymbolIndex']
    NrOfSymbols = pdsch_config['NrOfSymbols']
    RBStart = pdsch_config['ResAlloType1']['RBStart']
    RBSize = pdsch_config['ResAlloType1']['RBSize']

    carrier_RE_size = int(len(RE_usage_inslot[0,:]) // 14)

    empty_value = nr_slot.get_REusage_value('empty')
    pdsch_data_value = nr_slot.get_REusage_value('PDSCH-DATA')
    pdcch_data_value = nr_slot.get_REusage_value('PDCCH-DATA')
    pdcch_dmrs_value = nr_slot.get_REusage_value('PDCCH-DMRS')
    pdsch_data_RE_num = 0
    #get RE array used for PDSCH
    for sym in range(StartSymbolIndex,StartSymbolIndex+NrOfSymbols):
        start_pos = sym*carrier_RE_size + RBStart*12
        pdsch_RE_map = RE_usage_inslot[:,start_pos: start_pos+RBSize*12]
        #38.214 5.1.4.1 define RB symbol level resources that are not available for PDSCH
        # in the end of 5.1.4.1 it defines that if PDSCH PRB overlap with PDCCH PRB, in which condition 
        # the PDCCH PRB are not available for PDSCH.
        #spec said if the PDCCH that schedule this PDSCH has PRB overlap, then PDCCH PRB are not available for PDSCH
        #if other PDCCH(different RNTI) has PRB overlap with the PDSCH, then this PDCCH PRB are available for PDSCH
        #this is not reasonable
        #spec also define additonal requirement for aggregation levels 8 and 16 which make the system more complicated
        #5G product usually avoid any possibility of PDSCH and PDCCH overlap, 
        # furthemore, the product also avoid PDSCH resource overlap with search space resource
        # here we don;t support PDSCH overlap with PDCCH
        if np.count_nonzero(pdsch_RE_map[0,:] == pdcch_data_value) or np.count_nonzero(pdsch_RE_map[0,:] == pdcch_dmrs_value):
            assert 0

        #PDSCH resource mapping avoid:
        #(1) RE used by DMRS and co-scheduled UE DMRS (2) RE used by CSI-RS (3) PRB that are fully or partially used by SSB
        pdsch_data_RE_num += np.count_nonzero(pdsch_RE_map[0,:] == empty_value)
        pdsch_RE_map[:,pdsch_RE_map[0,:] == empty_value] = pdsch_data_value

    return RE_usage_inslot, pdsch_data_RE_num

def pdsch_data_re_mapping(pdsch_precoded, fd_slot_data, RE_usage_inslot, pdsch_config):
    """ PDSCH resouce mapping, put PDSCH data into fd_slot_data
    fd_slot_data = pdsch_data_re_mapping(pdsch_precoded, fd_slot_data, RE_usage_inslot, pdsch_config)
    """

    #get info
    StartSymbolIndex = pdsch_config['StartSymbolIndex']
    NrOfSymbols = pdsch_config['NrOfSymbols']
    RBStart = pdsch_config['ResAlloType1']['RBStart']
    RBSize = pdsch_config['ResAlloType1']['RBSize']
    
    carrier_RE_size = len(fd_slot_data[0,:]) // 14

    pdsch_data_value = nr_slot.get_REusage_value('PDSCH-DATA')

    in_offset = 0
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        #get RE that may used for PDSCH data mapping in the symbol
        start_pos = sym*carrier_RE_size + RBStart*12
        pdsch_re_mapping = RE_usage_inslot[0, start_pos : start_pos + RBSize*12]
        #get RE mapping len in the symbol
        mapping_len = np.count_nonzero(pdsch_re_mapping==pdsch_data_value)
        if mapping_len > 0:
            out_d = fd_slot_data[:, start_pos : start_pos + RBSize*12]
            out_d[:, pdsch_re_mapping==pdsch_data_value] = pdsch_precoded[: , in_offset:in_offset+mapping_len]
            in_offset += mapping_len
    
    return fd_slot_data

def copy_Rx_pdsch_resource(rx_fd_slot_data,pdsch_config):
    #get info
    StartSymbolIndex = pdsch_config['StartSymbolIndex']
    NrOfSymbols = pdsch_config['NrOfSymbols']
    RBStart = pdsch_config['ResAlloType1']['RBStart']
    RBSize = pdsch_config['ResAlloType1']['RBSize']

    Ld = StartSymbolIndex + NrOfSymbols #38.211 Table 7.4.1.1.2-3: PDSCH DM-RS positions l for single-symbol DM-RS.

    DMRSAddPos = pdsch_config["DMRS"]["DMRSAddPos"]
    DMRS_symlist = nr_pdsch_dmrs.get_DMRS_symlist(Ld,DMRSAddPos  )
    PortIndexList = pdsch_config["PortIndexList"]
    num_of_layers = pdsch_config['num_of_layers']
    PortIndexList = PortIndexList[0:num_of_layers]

    NumCDMGroupsWithoutData = pdsch_config["DMRS"]["NumCDMGroupsWithoutData"]
    
    if NumCDMGroupsWithoutData == 2:
        #all RE in one DMRS PRB are assigned for DMRS or DMRS reserved
        dmrs_RE_map_in_PRB = np.ones(12,'i1')
    else:
        dmrs_RE_map_in_PRB = np.zeros(12,'i1')
        if 1000 in PortIndexList or 1001 in PortIndexList:
            #RE 0,2,4,.. used for DMRS
            dmrs_RE_map_in_PRB[0::2] = 1
        if 1002 in PortIndexList or 1003 in PortIndexList:
            #RE 0,2,4,.. used for DMRS
            dmrs_RE_map_in_PRB[1::2] = 1

    carrier_RE_size = len(rx_fd_slot_data[0,:]) // 14
    Nr = rx_fd_slot_data.shape[0]   

    pdsch_resource = np.zeros((NrOfSymbols,RBSize*12,Nr),'c8')
    pdsch_RE_usage = np.zeros((NrOfSymbols,RBSize*12))
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        start_pos = sym*carrier_RE_size + RBStart*12
        for nr in range(Nr):
            pdsch_resource[sym - StartSymbolIndex,:,nr] = copy.copy(rx_fd_slot_data[nr,start_pos : start_pos + RBSize*12])

        if sym in DMRS_symlist:
            pdsch_RE_usage[sym - StartSymbolIndex,:] = np.tile(dmrs_RE_map_in_PRB,RBSize)
    
    return pdsch_resource, pdsch_RE_usage

if __name__ == "__main__":
    print("test PDSCH resource mapping")
    from tests.nr_pdsch import test_nr_pdsch
    file_lists = test_nr_pdsch.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pdsch.test_nr_pdsch(filename)