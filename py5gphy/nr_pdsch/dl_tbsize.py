# -*- coding:utf-8 -*-

import math

def gen_tbsize(pdsch_config):
    """ determine PDSCH TB size, modulation order and target code rate following 38.214 5.1.3
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)"""

    ###get input
    mcs_table = pdsch_config["mcs_table"]
    mcs_index = pdsch_config["mcs_index"]
    num_of_layers = pdsch_config["num_of_layers"]
    StartSymbolIndex = pdsch_config["StartSymbolIndex"]
    NrOfSymbols = pdsch_config["NrOfSymbols"]

    Ld = StartSymbolIndex + NrOfSymbols #38.211 Table 7.4.1.1.2-3: PDSCH DM-RS positions l for single-symbol DM-RS.

    #support ResourceAllocType=1 only
    assert pdsch_config["ResourceAllocType"] == 1

    nPRB = pdsch_config["ResAlloType1"]["RBSize"]
    NrOfSymbols = pdsch_config["NrOfSymbols"]
    NprbDmrs = _get_NprbDmrs(pdsch_config["DMRS"], Ld)

    ###process
    Qm, coderateby1024 = _get_Qm_coderate(mcs_table,mcs_index)
    
    #(1) The UE shall first determine the number of REs (NRE) within the slot
    # only support N_PRB_oh = 0
    NREbar = 12 * NrOfSymbols - NprbDmrs 
    #total number of REs allocated for PDSCH
    NRE = min(156, NREbar) * nPRB

    #(2)Intermediate number of information bits (Ninfo) is obtained by Ninfo = NRE·R·Qm·υ
    Ninfo = NRE * coderateby1024 / 1024 * Qm * num_of_layers

    table51321 = [
        24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 208, 224, 240, 256, 272, 288, 304, 320,
        336, 352, 368, 384, 408, 432, 456, 480, 504, 528, 552, 576, 608, 640, 672, 704, 736, 768, 808, 848, 888, 928, 984, 1032, 1064, 1128, 1160, 1192, 1224, 1256,
        1288, 1320, 1352, 1416, 1480, 1544, 1608, 1672, 1736, 1800, 1864, 1928, 2024, 2088, 2152, 2216, 2280, 2408, 2472, 2536, 2600, 2664, 2728, 2792, 2856, 2976, 3104, 3240, 3368, 3496, 3624, 3752, 3824,
    ]
    if Ninfo <= 3824:
        #(3)When Ninfo ≤ 3824, TBS is determined as follows
        n = max(3, math.floor(math.log2(Ninfo)) - 6)
        Ninfobar = max(24, (2 ** n) * math.floor(Ninfo/(2**n)))
        TBSize = [v for v in table51321 if v >=Ninfobar][0]
    else:
        #(4) When Ninfo > 3824, TBS is determined as follows
        n = math.floor(math.log2(Ninfo - 24)) - 5
        # 38.214 wrote for round operation: ties in the round function are broken towards the next largest integer
        # which means round(x.5) = x+1
        #Matlab and python 2 round function did in this way: round halfway to right
        #while for python 3,decimals are rounded to the nearest even number which means, round(1.5)=2, round(2.5)=2
        #here need addiotnal operation to handle round(even_value.5) = even_value case
        #cal round((Ninfo-24)/(2**n)))
        tmp = (Ninfo-24)/(2**n)
        if tmp == math.floor((Ninfo-24)/(2**n))+0.5:
            rounded = math.floor((Ninfo-24)/(2**n)) + 1
        else:
            rounded = round((Ninfo-24)/(2**n)) 
        Ninfobar = max(3840, (2**n)*rounded)
        
        if coderateby1024 <= 1/4*1024:
            C = math.ceil((Ninfobar+24)/3816)
            TBSize = 8*C*math.ceil((Ninfobar+24)/(8*C)) - 24
        else:
            if Ninfobar > 8424:
                C = math.ceil((Ninfobar+24)/8424)
                TBSize = 8*C*math.ceil((Ninfobar+24)/(8*C)) - 24
            else:
                TBSize = 8*math.ceil((Ninfobar+24)/8) - 24
    
    return TBSize, Qm, coderateby1024

def gen_TBS_LBRM(pdsch_config, carrier_prb_size, carrier_maxMIMO_layers):
    """ determine TBS_LBRM according to 38.212 5.4.2.1
    TBS_LBRM = gen_TBS_LBRM(pdsch_config,carrier_prb_size,carrier_maxMIMO_layers)"""

    ###get input
    mcs_table = pdsch_config["mcs_table"]
    X = carrier_maxMIMO_layers

    # GET TBS_LBRM parameters
    maxMIMO_layers = min(X, 4)
    if mcs_table.upper() == "256QAM":
        Qm = 8
    else:
        Qm = 6
    coderateby1024 = 948
    if carrier_prb_size< 33:
        nPRB_LBRM = 32
    elif carrier_prb_size <= 66:
        nPRB_LBRM = 66
    elif carrier_prb_size <= 107:
        nPRB_LBRM = 107
    elif carrier_prb_size <= 135:
        nPRB_LBRM = 135
    elif carrier_prb_size <= 162:
        nPRB_LBRM = 162
    elif carrier_prb_size <= 217:
        nPRB_LBRM = 217
    else:
        nPRB_LBRM = 273
    NRE = 156 * nPRB_LBRM
    #support ResourceAllocType=1 only
    assert pdsch_config["ResourceAllocType"] == 1

    # following to 38.214 5.1.3.2
    #(2)Intermediate number of information bits (Ninfo) is obtained by Ninfo = NRE·R·Qm·υ
    Ninfo = NRE * coderateby1024 / 1024 * Qm * maxMIMO_layers

    table51321 = [
        24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 208, 224, 240, 256, 272, 288, 304, 320,
        336, 352, 368, 384, 408, 432, 456, 480, 504, 528, 552, 576, 608, 640, 672, 704, 736, 768, 808, 848, 888, 928, 984, 1032, 1064, 1128, 1160, 1192, 1224, 1256,
        1288, 1320, 1352, 1416, 1480, 1544, 1608, 1672, 1736, 1800, 1864, 1928, 2024, 2088, 2152, 2216, 2280, 2408, 2472, 2536, 2600, 2664, 2728, 2792, 2856, 2976, 3104, 3240, 3368, 3496, 3624, 3752, 3824,
    ]
    if Ninfo <= 3824:
        #(3)When Ninfo ≤ 3824, TBS is determined as follows
        n = max(3, math.floor(math.log2(Ninfo)) - 6)
        Ninfobar = max(24, (2 ** n) * math.floor(Ninfo/(2**n)))
        TBSize = [v for v in table51321 if v >=Ninfobar][0]
    else:
        #(4) When Ninfo > 3824, TBS is determined as follows
        n = math.floor(math.log2(Ninfo - 24)) - 5
        # 38.214 wrote for round operation: ties in the round function are broken towards the next largest integer
        # which means round(x.5) = x+1
        #Matlab and python 2 round function did in this way: round halfway to right
        #while for python 3,decimals are rounded to the nearest even number which means, round(1.5)=2, round(2.5)=2
        #here need addiotnal operation to handle round(even_value.5) = even_value case
        tmp = (Ninfo-24)/(2**n)
        if tmp == math.floor((Ninfo-24)/(2**n))+0.5:
            rounded = math.floor((Ninfo-24)/(2**n)) + 1
        else:
            rounded = round((Ninfo-24)/(2**n)) 
        Ninfobar = max(3840, (2**n)*rounded)
        
        if coderateby1024 <= 1/4*1024:
            C = math.ceil((Ninfobar+24)/3816)
            TBSize = 8*C*math.ceil((Ninfobar+24)/(8*C)) - 24
        else:
            if Ninfobar > 8424:
                C = math.ceil((Ninfobar+24)/8424)
                TBSize = 8*C*math.ceil((Ninfobar+24)/(8*C)) - 24
            else:
                TBSize = 8*math.ceil((Ninfobar+24)/8) - 24
    
    TBS_LBRM = TBSize
    return TBS_LBRM

def _get_Qm_coderate(mcs_table, mcs_index):
    """return Qm and coderateby1024"""
    table_64qam = [
        [2, 120], [2, 157], [2, 193], [2, 251], [2, 308], [2, 379], [2, 449], [2, 526], 
        [2, 602], [2, 679], [4, 340], [4, 378], [4, 434], [4, 490], [4, 553], [4, 616], 
        [4, 658], [6, 438], [6, 466], [6, 517], [6, 567], [6, 616], [6, 666], [6, 719], 
        [6, 772], [6, 822], [6, 873], [6, 910], [6, 948] 
    ]
    
    table_256qam = [
        [2, 120],[2, 193],[2, 308],[2, 449],[2, 602],[4, 378],[4, 434],[4, 490],[4, 553],
        [4, 616],[4, 658],[6, 466],[6, 517],[6, 567],[6, 616],[6, 666],[6, 719],[6, 772],
        [6, 822],[6, 873],[8, 682.5],[8, 711],[8, 754],[8, 797],[8, 841],[8, 885],[8, 916.5],[8, 948]
    ]

    table_64qamLowSE = [
        [2, 30], [2, 40], [2, 50], [2, 64], [2, 78], [2, 99], [2, 120], [2, 157], [2, 193], 
        [2, 251], [2, 308], [2, 379], [2, 449], [2, 526], [2, 602], [4, 340], [4, 378], [4, 434], 
        [4, 490], [4, 553], [4, 616], [6, 438], [6, 466], [6, 517], [6, 567], [6, 616], [6, 666], 
        [6, 719], [6, 772]
    ]

    if mcs_table.upper() == "64QAM":
        assert mcs_index <= 28
        return table_64qam[mcs_index]
    elif mcs_table.upper() == "256QAM":
        assert mcs_index <= 27
        return table_256qam[mcs_index]
    elif mcs_table.upper() == "64QAMLOWSE":
        assert mcs_index <= 28
        return table_64qamLowSE[mcs_index]
    else:
        raise NameError( "wrong mcs table")
        
def _get_NprbDmrs(DMRS,Ld):
    """ NprbDMRS is the number of
REs for DM-RS per PRB in the scheduled duration including the overhead of the DM-RS CDM groups
without data following 38.214 5.1.3.2"""
    DMRSConfigType = DMRS["DMRSConfigType"]
    NrOfDMRSSymbols = DMRS["NrOfDMRSSymbols"]
    NumCDMGroupsWithoutData = DMRS["NumCDMGroupsWithoutData"]
    DMRSAddPos = DMRS["DMRSAddPos"]

    #first get RE number in one PRB that is  reserved for DMRS
    assert DMRSConfigType in [1,2]
    if DMRSConfigType == 1:
        assert NumCDMGroupsWithoutData in [1, 2]
        if NumCDMGroupsWithoutData == 1:
            DMRS_RE_num_in_PRB = 6
        else:
            DMRS_RE_num_in_PRB = 12
    else: #DMRSConfigType = 2
        assert NumCDMGroupsWithoutData in [1, 2, 3]
        if NumCDMGroupsWithoutData == 1:
            DMRS_RE_num_in_PRB = 4
        elif NumCDMGroupsWithoutData == 2:
            DMRS_RE_num_in_PRB = 8
        else:
            DMRS_RE_num_in_PRB = 12
    
    #second get number of DMRS symbol,
    #only support PDSCH mappingtype B here
    assert NrOfDMRSSymbols in [1, 2]
    if NrOfDMRSSymbols == 1:
        assert DMRSAddPos in [0, 1, 2, 3]
        #38.211 Table 7.4.1.1.2-3: PDSCH DM-RS positions l for single-symbol DM-RS.
        if Ld <= 7:
            DMRS_sym_num = 1
        elif Ld <=9:
            if DMRSAddPos == 0:
                DMRS_sym_num = 1
            else:
                DMRS_sym_num = 2
        elif Ld <= 11:
            if DMRSAddPos == 0:
                DMRS_sym_num = 1
            elif DMRSAddPos == 1:
                DMRS_sym_num = 2
            else:
                DMRS_sym_num = 3
        else:
            DMRS_sym_num = DMRSAddPos + 1
    else:
        assert DMRSAddPos in [0, 1]
        DMRS_sym_num = DMRSAddPos*2 + 2
        if Ld <= 9:
            DMRS_sym_num = 2
        else:
            DMRS_sym_num = (DMRSAddPos+1)*2
    
    NprbDmrs = DMRS_sym_num * DMRS_RE_num_in_PRB
    return NprbDmrs


if __name__ == "__main__":
    print("test PDSCH TX size ")
    from py5gphy.nr_pdsch import nr_pdsch
    import json
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)

    pdsch_config["mcs_table"] = '64QAM'
    pdsch_config["mcs_index"] = 0
    pdsch_config["num_of_layers"] = 1
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 10
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 2
    pdsch_config["DMRS"]["DMRSAddPos"] = 0
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 304) and (Qm == 2) and (coderateby1024==120)

    pdsch_config["mcs_table"] = '64QAM'
    pdsch_config["mcs_index"] = 3
    pdsch_config["num_of_layers"] = 1
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 10
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 1
    pdsch_config["DMRS"]["DMRSAddPos"] = 0
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 672) and (Qm == 2) and (coderateby1024==251)

    pdsch_config["mcs_table"] = '64QAM'
    pdsch_config["mcs_index"] = 10
    pdsch_config["num_of_layers"] = 2
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 40
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 2
    pdsch_config["DMRS"]["DMRSAddPos"] = 1
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 12808) and (Qm == 4) and (coderateby1024==340)

    pdsch_config["mcs_table"] = '64QAM'
    pdsch_config["mcs_index"] = 18
    pdsch_config["num_of_layers"] = 4
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 100
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 2
    pdsch_config["DMRS"]["DMRSAddPos"] = 2
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 118896) and (Qm == 6) and (coderateby1024==466)

    pdsch_config["mcs_table"] = '256QAM'
    pdsch_config["mcs_index"] = 26
    pdsch_config["num_of_layers"] = 4
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 273
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 2
    pdsch_config["DMRS"]["DMRSAddPos"] = 3
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 753816) and (Qm == 8) and (coderateby1024==916.5)

    pdsch_config["mcs_table"] = '256QAM'
    pdsch_config["mcs_index"] = 27
    pdsch_config["num_of_layers"] = 4
    pdsch_config["NrOfSymbols"] = 12
    pdsch_config["ResAlloType1"]["RBSize"] = 273
    pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 2
    pdsch_config["DMRS"]["DMRSAddPos"] = 0
    TBSize, Qm, coderateby1024 = gen_tbsize(pdsch_config)
    assert (TBSize == 1081512) and (Qm == 8) and (coderateby1024==948)
    aaa=1
