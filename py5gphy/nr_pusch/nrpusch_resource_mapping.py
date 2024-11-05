# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nr_slot

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
