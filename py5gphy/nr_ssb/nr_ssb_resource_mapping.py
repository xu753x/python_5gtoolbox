# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.common import nr_slot

def nrssb_one_symbol_re_mapping(ssb_data,fd_slot_data, RE_usage_inslot,ssb_sym,NSSB_CRB,kSSB,scs):
    """ support only SSB SCS == carrier SCS case
    #NSSB_CRB is PRB offset between lowest SSB and point A assuming 15KHz scs, need divide by 2 for 30khz
                # by 3gpp spec, ssb SCS could be different with carrier SSB, but the product usually not use in this way
                # here support only that SSB and carrier use the same scs, 
    """
    if scs == 15:
        ssb_offset = NSSB_CRB*12 + kSSB
    else:
        #common PRB offset to pointA express in 15khz scs, 
        #one PRB offset in 30khz scs = 2 NSSB_CRB value in 15khz
        #this valye need to be even
        assert NSSB_CRB % 2 == 0

        #kSSB is in [0,23] for 30khz scs, and is subcarrier offset from CRB subcarrier 0 to first SSB subcarrier
        #if this value is odd, SSB subcarrier will have 15khz offset with other 30khz subcarrier
        #which make the system complicated and unnecessary, here support only even kSSB
        assert kSSB % 2 == 0
        ssb_offset = (NSSB_CRB*12 + kSSB) // 2
    
    ssb_first_prb = ssb_offset // 12
    ssb_scoffset_in_first_prb = ssb_offset % 12

    #get slot offset that SSB map to
    carrier_RE_size = len(fd_slot_data[0,:]) // 14
    data_offset = carrier_RE_size*ssb_sym + ssb_offset
    fd_slot_data[:,data_offset:data_offset+240] = ssb_data

    RE_usage_inslot[0,data_offset:data_offset+240] = nr_slot.get_REusage_value('SSB') # SSB PRB
    if ssb_scoffset_in_first_prb > 0:
        #other subcarrier in first PRB and last PRB are reserved and can not be used to map PDSCH
        ssb_prb_offset = carrier_RE_size*ssb_sym + ssb_first_prb*12
        RE_usage_inslot[0, ssb_prb_offset : ssb_prb_offset +  ssb_scoffset_in_first_prb] = nr_slot.get_REusage_value('SSB-PRB-RSV') 
        
        ssb_last_prb = ssb_first_prb + 20
        ssb_prb_offset = carrier_RE_size*ssb_sym + ssb_last_prb*12
        RE_usage_inslot[0, data_offset+240 : ssb_prb_offset]  = nr_slot.get_REusage_value('SSB-PRB-RSV') 
    
    return fd_slot_data, RE_usage_inslot


