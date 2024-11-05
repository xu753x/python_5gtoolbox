# -*- coding:utf-8 -*-

import numpy as np
import copy
import math

def data_control_multiplex(g_ulsch, g_ack, g_csi1, g_csi2, pusch_config, Gtotal,
        DMRS_symlist,RMinfo, Qm):
    """38.212 6.2.7 Data and control multiplexing
    """
    
    RBSize = pusch_config['ResAlloType1']['RBSize']
    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    NumCDMGroupsWithoutData = pusch_config["DMRS"]["NumCDMGroupsWithoutData"]
    if NumCDMGroupsWithoutData==1:
        dataREnuminPRB = 6
    else:
        dataREnuminPRB = 0
    NL = pusch_config['num_of_layers']

    #get MULSCH,number of elements for each sym for ULSCH
    phiULSCH = []
    MULSCH = [0] * NrOfSymbols #number of elements for each sym
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        if sym in DMRS_symlist:
            MULSCH[sym-StartSymbolIndex] = RBSize * dataREnuminPRB
        else:
            MULSCH[sym-StartSymbolIndex] = RBSize * 12
        phiULSCH.append(list(range(MULSCH[sym-StartSymbolIndex])))
    
    #get MUCI number of elements for each sym for UCI
    phiUCI = []
    MUCI = [0] * NrOfSymbols #number of elements for each sym
    for sym in range(StartSymbolIndex, StartSymbolIndex+NrOfSymbols):
        if sym in DMRS_symlist:
            MUCI[sym-StartSymbolIndex] = 0
        else:
            MUCI[sym-StartSymbolIndex] = RBSize * 12
        phiUCI.append(list(range(MUCI[sym-StartSymbolIndex])))

    ## support non frequency hopping only
    L1 = DMRS_symlist[0] + 1 #first sym after first DMRS
    #OFDM symbol index of the first OFDM symbol that does not carry DMRS
    if StartSymbolIndex in DMRS_symlist:
        LCSI1 = StartSymbolIndex + 1
    else:
        LCSI1 = StartSymbolIndex
    
    GACK_1 = len(g_ack)
    GCSI1_1 = len(g_csi1)
    GCSI2_1 = len(g_csi2)
    NPUSCHhop = 1
    NPUSCHsymb_hop1 = NrOfSymbols

    #The multiplexed data and control coded bit sequence g0,g1,g2,.. is obtained according to the following:
    g_seq = np.zeros(Gtotal, 'i1')
    gbarLkv_seq = np.zeros((NrOfSymbols, RBSize * 12, NL*Qm))

    #step 1
    phibarULSCH = copy.deepcopy(phiULSCH)
    MbarULSCH = copy.deepcopy(MULSCH)
    phibarUCI = copy.deepcopy(phiUCI)
    MbarUCI = copy.deepcopy(MUCI)

    EnableACK = pusch_config['EnableACK']
    NumACKBits = pusch_config['NumACKBits']

    phibarrvd = [ [] for m in range(NPUSCHsymb_hop1)]
    if EnableACK*NumACKBits <=2:
        GACKrvd = RMinfo['Euci_ackrvd']
        
        mACKcount1 = 0

        L = L1
        while mACKcount1 < GACKrvd:
            if MbarUCI[L] > 0:
                if GACKrvd - mACKcount1 >= MbarUCI[L]*NL*Qm:
                    d = 1
                    mREcount = MbarULSCH[L]
                else:
                    d = math.floor(MbarUCI[L]*NL*Qm/(GACKrvd-mACKcount1))
                    mREcount = math.ceil((GACKrvd-mACKcount1)/(NL*Qm))
                
                for j in range(mREcount):
                    phibarrvd[L].append(phibarULSCH[L][j*d])
                    mACKcount1 += NL*Qm
            L += 1
    
    Mbarphibarrvd = [0] * NPUSCHsymb_hop1
    for m in range(NPUSCHsymb_hop1):
        Mbarphibarrvd[m] = len(phibarrvd[m])

    #step 2
    if EnableACK*NumACKBits > 2:
        mACKcount1 = 0
        mACKcountall = 0
        GACK = RMinfo['Euci_ack']
        
        L = L1
        while mACKcount1 < GACK:
            if MbarUCI[L] > 0:
                if GACK - mACKcount1 >= MbarUCI[L]*NL*Qm:
                    d = 1
                    mREcount = MbarULSCH[L]
                else:
                    d = math.floor(MbarUCI[L]*NL*Qm/(GACK-mACKcount1)) 
                    mREcount = math.ceil((GACK-mACKcount1)/(NL*Qm))
                
                for j in range(mREcount):
                    k = phibarUCI[L][j*d]
                    for v in range(NL*Qm):
                        gbarLkv_seq[L][k][v] =  g_ack[mACKcountall]
                        mACKcountall += 1
                        mACKcount1 += 1
                
                phibarUCItmp = []
                for j in range(mREcount):
                    phibarUCItmp.append(phibarUCI[L][j*d])
                
                #rmove phibarUCItmp from phibarUCI and from phibarULSCH
                new_list = [m for m in phibarUCI[L] if m not in phibarUCItmp]
                phibarUCI[L] = new_list
                
                new_list = [m for m in phibarULSCH[L] if m not in phibarUCItmp]
                phibarULSCH[L] = new_list
                

                MbarUCI[L] = len(phibarUCI[L])
                MbarULSCH[L] = len(phibarULSCH[L])
            L += 1

    #step 3
    EnableCSI1 = pusch_config['EnableCSI1']
    NumCSI1Bits = pusch_config['NumCSI1Bits']
    
    EnableCSI2 = pusch_config['EnableCSI2']
    NumCSI2Bits = pusch_config['NumCSI2Bits']
    
    if EnableCSI1*NumCSI1Bits >0:
        mCSI1count = 0
        mCSI1countall = 0
        L=LCSI1
        while MbarUCI[L] - Mbarphibarrvd[L] <= 0:
            L += 1
        
        while mCSI1count < GCSI1_1:
            if MbarUCI[L] - Mbarphibarrvd[L] > 0:
                if GCSI1_1-mCSI1count >= (MbarUCI[L]-Mbarphibarrvd[L])*NL*Qm:
                    d = 1
                    mREcount = MbarUCI[L]-Mbarphibarrvd[L]
                else:
                    d = math.floor((MbarUCI[L]-Mbarphibarrvd[L])*NL*Qm/(GCSI1_1-mCSI1count))
                    mREcount = math.ceil((GCSI1_1-mCSI1count)/(NL*Qm))
                
                phibartemp = []
                for m in phibarUCI[L]:
                    if m not in phibarrvd[L]:
                        phibartemp.append(m)
                
                for j in range(mREcount):
                    k = phibartemp[j*d]
                    for v in range(NL*Qm):
                        gbarLkv_seq[L][k][v] = g_csi1[mCSI1countall]
                        mCSI1countall += 1
                        mCSI1count += 1

                phibarUCItmp = []
                for j in range(mREcount):
                    phibarUCItmp.append(phibartemp[j*d])
                
                #rmove phibarUCItmp from phibarUCI and from phibarULSCH
                new_list = [m for m in phibarUCI[L] if m not in phibarUCItmp]
                phibarUCI[L] = new_list
                
                new_list = [m for m in phibarULSCH[L] if m not in phibarUCItmp]
                phibarULSCH[L] = new_list

                MbarUCI[L] = len(phibarUCI[L])
                MbarULSCH[L] = len(phibarULSCH[L])
            L += 1

    #CSI 2
    if EnableCSI2*NumCSI2Bits >0:
        mCSI2count = 0
        mCSI2countall = 0
        L=LCSI1
        while MbarUCI[L] <= 0:
            L += 1
        
        while mCSI2count < GCSI2_1:
            if MbarUCI[L] > 0:
                if GCSI2_1-mCSI2count >= MbarUCI[L]*NL*Qm:
                    d = 1
                    mREcount = MbarUCI[L]
                else:
                    d = math.floor(MbarUCI[L]*NL*Qm/(GCSI2_1-mCSI2count))
                    mREcount = math.ceil((GCSI2_1-mCSI2count)/(NL*Qm))
                
                for j in range(mREcount):
                    k = phibarUCI[L][j*d]
                    for v in range(NL*Qm):
                        gbarLkv_seq[L][k][v] = g_csi2[mCSI2countall]
                        mCSI2countall += 1
                        mCSI2count += 1

                phibarUCItmp = []
                for j in range(mREcount):
                    phibarUCItmp.append(phibarUCI[L][j*d])
                
                #rmove phibarUCItmp from phibarUCI and from phibarULSCH
                new_list = [m for m in phibarUCI[L] if m not in phibarUCItmp]
                phibarUCI[L] = new_list
                
                new_list = [m for m in phibarULSCH[L] if m not in phibarUCItmp]
                phibarULSCH[L] = new_list
                
                MbarUCI[L] = len(phibarUCI[L])
                MbarULSCH[L] = len(phibarULSCH[L])
            L += 1

    #step 4
    EnableULSCH = pusch_config['EnableULSCH']
    if EnableULSCH == 1:
        mULSCHcount = 0
        for L in range(NrOfSymbols):
            if MbarULSCH[L] > 0:
                for j in range(MbarULSCH[L]):
                    k = phibarULSCH[L][j]
                    for v in range(NL*Qm):
                        gbarLkv_seq[L][k][v] = g_ulsch[mULSCHcount]
                        mULSCHcount += 1
    
    #step 5
    if EnableACK*NumACKBits in [1,2]:
        mACKcount = 0
        mACKcountall = 0
        GACK = RMinfo['Euci_ack']
        L = L1
        while mACKcount < GACK:
            if Mbarphibarrvd[L] > 0:
                if GACK - mACKcount >= Mbarphibarrvd[L]*NL*Qm:
                    d = 1
                    mREcount = Mbarphibarrvd[L]
                else:
                    d = math.floor(Mbarphibarrvd[L]*NL*Qm/(GACK - mACKcount))
                    mREcount = math.ceil((GACK - mACKcount)/(NL*Qm))
                
                for j in range(mREcount):
                    k= phibarrvd[L][j*d]
                    for v in range(NL*Qm):
                        gbarLkv_seq[L][k][v] = g_ack[mACKcountall]
                        mACKcountall += 1
                        mACKcount += 1

            L += 1
    
    #step 6
    t = 0
    for L in range(NrOfSymbols):
        for j in range(MULSCH[L]):
            k = phiULSCH[L][j]
            for v in range(NL*Qm):
                g_seq[t] = gbarLkv_seq[L][k][v]
                t += 1

    return g_seq