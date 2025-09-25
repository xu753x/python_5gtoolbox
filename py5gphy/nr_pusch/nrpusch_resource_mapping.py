# -*- coding:utf-8 -*-

import numpy as np
import copy

from py5gphy.common import nr_slot

from py5gphy.nr_pusch import nr_pusch_dmrs

def pusch_data_re_mapping_prepare(RE_usage_inslot, pusch_config):
    """ calculate total RE numbder that PUSCH data can map to,
        and add PUSCH RE type value to those RE
        this functio should be called after PUSCH-DMRS resouce mapping
    RE_usage_inslot, pusch_data_RE_num = pusch_data_re_mapping_prepare(RE_usage_inslot, pusch_config)
    input:
        RE_usage_inslot: 14sym X REsize, indicate RE usage for each RE
    output:
        RE_usage_inslot: add PUSCH data RE type into RE_usage_inslot
        pusch_RE_num: number of RE used by pusch data mapping, used for rate matching

    """
    #get info
    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    RBStart = pusch_config['ResAlloType1']['RBStart']
    RBSize = pusch_config['ResAlloType1']['RBSize']
    carrier_RE_size = len(RE_usage_inslot[0,:]) // 14

    empty_value = nr_slot.get_REusage_value('empty')
    pusch_data_value = nr_slot.get_REusage_value('PUSCH-DATA')

    #get RE array used for pusch
    pusch_data_RE_num = 0
    for m in range(NrOfSymbols):
        sym = m + StartSymbolIndex
        pusch_RE_map = RE_usage_inslot[:,sym*carrier_RE_size + RBStart*12 : sym*carrier_RE_size +(RBStart+RBSize)*12]
    
        pusch_data_RE_num += np.count_nonzero(pusch_RE_map[0,:] == empty_value)
        pusch_RE_map[pusch_RE_map == empty_value] = pusch_data_value

    return RE_usage_inslot, pusch_data_RE_num

def pusch_data_re_mapping(pusch_precoded, fd_slot_data, RE_usage_inslot, pusch_config):
    """ pusch resouce mapping, put pusch data into fd_slot_data
    fd_slot_data = pusch_data_re_mapping(pusch_precoded, fd_slot_data, RE_usage_inslot, pusch_config)
    """

    #get info
    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    RBStart = pusch_config['ResAlloType1']['RBStart']
    RBSize = pusch_config['ResAlloType1']['RBSize']
    
    carrier_RE_size = len(fd_slot_data[0,:]) // 14

    pusch_data_value = nr_slot.get_REusage_value('PUSCH-DATA')

    in_offset = 0
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        #get RE that may used for pusch data mapping in the symbol
        pusch_re_mapping = RE_usage_inslot[0,sym*carrier_RE_size + RBStart*12 : sym*carrier_RE_size + (RBStart+RBSize)*12]
        #get RE mapping len in the symbol
        mapping_len = np.count_nonzero(pusch_re_mapping==pusch_data_value)
        if mapping_len > 0:
            out_d = fd_slot_data[:, sym*carrier_RE_size + RBStart*12 : sym*carrier_RE_size + (RBStart+RBSize)*12]
            if pusch_precoded.ndim == 1: # for one ant
                out_d[:, pusch_re_mapping==pusch_data_value] = pusch_precoded[in_offset:in_offset+mapping_len]
            else:
                out_d[:, pusch_re_mapping==pusch_data_value] = pusch_precoded[: , in_offset:in_offset+mapping_len]
            in_offset += mapping_len
    
    return fd_slot_data

def copy_Rx_pusch_resource(rx_fd_slot_data, pusch_config):
    """
    """
    #get info
    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    RBStart = pusch_config['ResAlloType1']['RBStart']
    RBSize = pusch_config['ResAlloType1']['RBSize']
    DMRSAddPos = pusch_config["DMRS"]["DMRSAddPos"]

    Ld = StartSymbolIndex + NrOfSymbols

    DMRS_symlist =nr_pusch_dmrs.get_DMRS_symlist(Ld,DMRSAddPos)

    PortIndexList = pusch_config["PortIndexList"]
    num_of_layers = pusch_config['num_of_layers']
    PortIndexList = PortIndexList[0:num_of_layers]

    NumCDMGroupsWithoutData = pusch_config["DMRS"]["NumCDMGroupsWithoutData"]
    
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

    pusch_resource = np.zeros((NrOfSymbols,RBSize*12,Nr),'c8')
    pusch_RE_usage = np.zeros((NrOfSymbols,RBSize*12))
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        start_pos = sym*carrier_RE_size + RBStart*12
        for nr in range(Nr):
            pusch_resource[sym - StartSymbolIndex,:,nr] = copy.copy(rx_fd_slot_data[nr,start_pos : start_pos + RBSize*12])

        if sym in DMRS_symlist:
            pusch_RE_usage[sym - StartSymbolIndex,:] = np.tile(dmrs_RE_map_in_PRB,RBSize)

    return pusch_resource,pusch_RE_usage