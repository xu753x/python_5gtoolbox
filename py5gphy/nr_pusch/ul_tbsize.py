# -*- coding:utf-8 -*-

import numpy as np
import math

def gen_tbsize(pusch_config):
    """ determine PUSCH TB size, modulation order and target code rate following 38.214 6.1.4
    TBSize, Qm, coderateby1024 = gen_tbsize(pusch_config)"""
    
    #get input
    mcs_table = pusch_config['mcs_table']
    num_of_layers = pusch_config['num_of_layers']
    mcs_index = pusch_config['mcs_index']
    nPRB = pusch_config['ResAlloType1']['RBSize']
    nTpPi2BPSK = pusch_config['nTpPi2BPSK']
    NrOfSymbols = pusch_config['NrOfSymbols']
    

    #6.1.4.1 Modulation order and target code rate determination
    Qm, coderateby1024 = _get_Qm_coderate(mcs_table, mcs_index, nTpPi2BPSK)

    #6.1.4.2 Transport block size determination
    NprbDmrs = _get_NprbDmrs(pusch_config["DMRS"], NrOfSymbols)
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

def _get_Qm_coderate(mcs_table, mcs_index, nTpPi2BPSK):
    """return Qm and coderateby1024 refer to 38.214 6.1.4.1 Modulation order and target code rate determination"""
    table_61411 = [
        [1, 240],[1, 314],[2, 193],[2, 251],[2, 308],[2, 379],[2, 449],
        [2, 526],[2, 602],[2, 679],[4, 340],[4, 378],[4, 434],[4, 490],
        [4, 553],[4, 616],[4, 658],[6, 466],[6, 517],[6, 567],[6, 616],
        [6, 666],[6, 719],[6, 772],[6, 822],[6, 873],[6, 910],[6, 948]

    ]
    table_61412 = [
        [1, 60 ],[1, 80 ],[1, 100],[1, 128],[1, 156],[1, 198],[2, 120], 
        [2, 157],[2, 193],[2, 251],[2, 308],[2, 379],[2, 449],[2, 526],
        [2, 602],[2, 679],[4, 378],[4, 434],[4, 490],[4, 553],[4, 616],
        [4, 658],[4, 699],[4, 772],[6, 567],[6, 616],[6, 666],[6, 772]

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
    #For Table 6.1.4.1-1 and Table 6.1.4.1-2, if higher layer parameter tp-pi2BPSK is configured, q = 1 otherwise q=2.
    q = 2 - nTpPi2BPSK

    if mcs_table == "MCStable61411":
        assert mcs_index <= 28
        Qm, coderateby1024 = table_61411[mcs_index]
        if mcs_index <= 1:
            Qm = Qm * q
            coderateby1024 = int(coderateby1024/q)
        return Qm, coderateby1024
    elif mcs_table == "MCStable61412":
        assert mcs_index <= 28
        Qm, coderateby1024 = table_61412[mcs_index]
        if mcs_index <= 5:
            Qm = Qm * q
            coderateby1024 = int(coderateby1024/q)
        return Qm, coderateby1024
    elif mcs_table.upper() == "256QAM":
        assert mcs_index <= 27
        return table_256qam[mcs_index]
    elif mcs_table.upper() == "64QAMLOWSE":
        assert mcs_index <= 28
        return table_64qamLowSE[mcs_index]
    else:
        raise NameError( "wrong mcs table")

def _get_NprbDmrs(DMRS, NrOfSymbols):
    """ NprbDMRS is the number of
REs for DM-RS per PRB in the scheduled duration including the overhead of the DM-RS CDM groups
without data following 38.214 6.1.4.2"""
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
        #38.211 Table 6.4.1.1.3-3, single symbol DMRS, no intra slot frequency hopping, PUSCH mapping typw A 
        assert DMRSAddPos in [0, 1, 2, 3]
        if NrOfSymbols <= 7:
            DMRS_sym_num = 1
        elif NrOfSymbols <= 9:
            DMRS_sym_num = min(DMRSAddPos, 1) + 1
        elif NrOfSymbols <= 11:
            DMRS_sym_num = min(DMRSAddPos, 2) + 1
        else:
            DMRS_sym_num = DMRSAddPos + 1
    else:
        #double DMRS symbol, not supported
        assert 0
    
    NprbDmrs = DMRS_sym_num * DMRS_RE_num_in_PRB
    return NprbDmrs

if __name__ == "__main__":
    print("test nr ULSCH TBSize")
    from tests.nr_pusch import test_nr_ulsch_tbsize
    file_lists = test_nr_ulsch_tbsize.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        if count == 703:
            setbreakpoint = 1
        count += 1
        test_nr_ulsch_tbsize.test_nr_ulsch_tbsize(filename)