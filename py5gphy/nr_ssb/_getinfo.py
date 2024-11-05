# -*- coding:utf-8 -*-

import numpy as np

def get_info(self, carrier_frequency_in_mhz, duplex_type):
    """parse ssb config and get SSB processing related information, refer to 38.213 4.1
    the data that added to ssb_info:
    LMax: max number of SSB block, the value is 4 or 8
    ssbscs: SSB scs(15 or 30), the value shall be equal to carrrier scs in this design
            by 3GPP spec, SSB scs could be different with carrier SCS, which make the system too complicated
            5g product usually only choose same SCS for all DL channel
    ssb_candidate: list of first SSb symbol for each SSB block index,

    """
    #SSB scs and blocks 38.213 4.1
    SSBPattern = self.ssb_config["SSBPattern"]
    if SSBPattern == "Case A":
        ssbscs = 15
        assert (ssbscs/15) == self.ssb_config["MIB"]["subCarrierSpacingCommon"]+1
        if carrier_frequency_in_mhz <= 3000:
            LMax = 4
            ssb_candidate = [2,8,14+2,14+8]
        else:
            LMax = 8
            ssb_candidate = [2,8, 14+2,14+8, 14*2+2,14*2+8,14*3+2,14*3+8]
    elif SSBPattern == "Case B":
        ssbscs = 30
        assert (ssbscs/15) == self.ssb_config["MIB"]["subCarrierSpacingCommon"]+1
        if carrier_frequency_in_mhz <= 3000:
            LMax = 4
            ssb_candidate = [4,8,16,20]
        else:
            LMax = 8
            ssb_candidate = [4,8,16,20,28+4,28+8,28+16,28+20]
    elif SSBPattern == "Case C":
        ssbscs = 30
        assert (ssbscs/15) == self.ssb_config["MIB"]["subCarrierSpacingCommon"]+1
        if duplex_type.upper() == "FDD": #paired spectrum operation
            if carrier_frequency_in_mhz <= 3000:
                LMax = 4
                ssb_candidate = [2,8,14+2,14+8]
            else:
                LMax = 8
                ssb_candidate = [2,8, 14+2,14+8, 14*2+2,14*2+8,14*3+2,14*3+8]
        else: #unpaired spectrum operation
            if carrier_frequency_in_mhz <= 1880:
                LMax = 4
                ssb_candidate = [2,8,14+2,14+8]
            else:
                LMax = 8
                ssb_candidate = [2,8, 14+2,14+8, 14*2+2,14*2+8,14*3+2,14*3+8]
    else:
        raise Exception("SSB case is not one of ['A', 'B','C']")

    self.info={}
    self.info["LMax"] = LMax
    self.info["ssbscs"] = ssbscs
    self.info["ssb_candidate"] = np.array(ssb_candidate)
           
def get_ssbidx_list_in_slot(self, sfn, slot):
    """ return first SSB symbol list that is scheduled in the sfn/slot
    return empty if no SSB
    ssbfirstsym_list, iSSB_list = get_ssbidx_list_in_slot(self, sfn, slot)
    output:
        ssbfirstsym_list: first SSB symbol list in the slot
        iSSB_list: 
            for LMax =4, two least significant bits of the SS/PBCH block index 
            for LMax =8, three least significant bits of the SS/PBCH block index 
    """
    ssbfirstsym_list = np.array([],'i1')
    iSSB_list = np.array([],'i1')
    #gen info
    ssbscs = self.info["ssbscs"]

    if ssbscs == 15:
        hrf = slot // 5
        slot_in_hrf = slot % 5
    else: #30khz
        hrf = slot // 10
        slot_in_hrf = slot % 10

    #check if ssb schedule in the half frame
    if ((sfn* 2 + hrf) % (self.ssb_config['SSBperiod']/5)):
        #no SSB in this half frame,return empty
        return ssbfirstsym_list, iSSB_list

    #check if SSB scheduled in the slot
    #ssb_PositionsInBurst size may be less than LMax(ssb_candidate.size)
    # extend ssb_PositionsInBurst to 1X8 ssb_PositionsInBurst2
    ssb_PositionsInBurst2 = [0]*8
    ssb_PositionsInBurst = self.ssb_config["ssb_PositionsInBurst"]
    size = len(ssb_PositionsInBurst)
    assert size <= 8
    ssb_PositionsInBurst2[0:size] = ssb_PositionsInBurst

    ssb_candidate = self.info["ssb_candidate"]
    for idx in range(ssb_candidate.size):
        #for each SSB candidate, if it is configured
        if ssb_PositionsInBurst2[idx]:
            slotidx = ssb_candidate[idx] // 14 #get SSB candidate slot number
            if slot_in_hrf == slotidx: # if in this slot
                ssbfirstsym_list = np.append(ssbfirstsym_list,ssb_candidate[idx] % 14)
                iSSB_list = np.append(iSSB_list,idx)
    
    return ssbfirstsym_list, iSSB_list
    

