# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.common import nr_slot

def nrssb_config_validate(carrier_config, ssb_config):

    #read input
    SSBPattern = ssb_config["SSBPattern"]
    ssb_PositionsInBurst = ssb_config["ssb_PositionsInBurst"]
    SSBperiod = ssb_config["SSBperiod"]
    kSSB = ssb_config["kSSB"]
    NSSB_CRB = ssb_config["NSSB_CRB"]
    
    #38.331 6.2.2 MIB 
    subCarrierSpacingCommon = ssb_config["MIB"]["subCarrierSpacingCommon"]
    assert subCarrierSpacingCommon in [0,1]
    dmrs_TypeA_Position = ssb_config["MIB"]["dmrs_TypeA_Position"]
    assert dmrs_TypeA_Position in [0,1]
    pdcch_ConfigSIB1 = ssb_config["MIB"]["pdcch_ConfigSIB1"]
    assert pdcch_ConfigSIB1 in range(256)

    cellBarred = ssb_config["MIB"]["cellBarred"]
    assert cellBarred in [0,1]
    intraFreqReselection = ssb_config["MIB"]["intraFreqReselection"]
    assert intraFreqReselection in [0,1]

    assert SSBPattern in ["Case A", "Case B","Case C"]
    assert len(ssb_PositionsInBurst) <= 8

    #38.331 6.3.2 ServingCellConfigCommonSIB
    assert SSBperiod in [5,10,20,40,80,160]
    
    assert kSSB in range(24)
    assert NSSB_CRB in range(2199+1)
