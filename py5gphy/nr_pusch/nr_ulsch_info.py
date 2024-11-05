# -*- coding:utf-8 -*-

import numpy as np
import math

def getULSCH_RM_info(pusch_config, DMRS_symlist,ULSCH_size, Qm, coderateby1024,Gtotal):
    """ following to 38.212 6.3.2.4, calculate rate matching parameters
        cbs is ULSCH code blocks
    """
    EnableULSCH = pusch_config['EnableULSCH']
    nAlphaScaling = pusch_config['UCIScaling']
    
    EnableACK = pusch_config['EnableACK']
    NumACKBits = pusch_config['NumACKBits']
    I_HARQ_ACK_offset = pusch_config['I_HARQ_ACK_offset']
    
    EnableCSI1 = pusch_config['EnableCSI1']
    NumCSI1Bits = pusch_config['NumCSI1Bits']
    I_CSI1offset = pusch_config['I_CSI1offset']
    
    EnableCSI2 = pusch_config['EnableCSI2']
    NumCSI2Bits = pusch_config['NumCSI2Bits']
    I_CSI2offset = pusch_config['I_CSI2offset']
    
    RBSize = pusch_config['ResAlloType1']['RBSize']
    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    num_of_layers = pusch_config['num_of_layers']
    
    OACK = EnableACK * NumACKBits
    OCSI1 = EnableCSI1 * NumCSI1Bits
    OCSI2 = EnableCSI2 * NumCSI2Bits

    num_nonDMRS_sym = NrOfSymbols - len(DMRS_symlist)
    #sum MUCI_sc over all non DMRSSymbol
    TotalMUCI = num_nonDMRS_sym * RBSize * 12

    #L0 is symbol index of the first OFDM symbol that does not carry DMRS of the PUSCH, after the first DMRS
    #symbol(s), in the PUSCH transmission.
    L0 = DMRS_symlist[0] + 1
    #num of non DNRS syms from first symbol to L0
    num_nonDMRS_sym_till_L0 = L0 - StartSymbolIndex - 1
    SumMUCIfromL0 = (num_nonDMRS_sym-num_nonDMRS_sym_till_L0) * RBSize * 12
    
    #6.3.2.4.1.1 HARQ-ACK
    if OACK == 0:
            Qbar_ACK = 0
    else:
        NumbitsPlusL = _get_plusLsize(OACK)
        belta_offset = _get_HARQ_ACK_Belta_offset(I_HARQ_ACK_offset)
        if EnableULSCH == 1:
            #For HARQ-ACK transmission on PUSCH with UL-SCH,
            d1 = math.ceil(NumbitsPlusL * belta_offset * TotalMUCI / ULSCH_size)
            Qbar_ACK = min(d1, math.ceil(nAlphaScaling * SumMUCIfromL0))
        else:
            #For HARQ-ACK transmission on PUSCH without UL-SCH
            Qbar_ACK = min(math.ceil(NumbitsPlusL * belta_offset / (Qm*coderateby1024/1024)), math.ceil(nAlphaScaling * SumMUCIfromL0))

    Euci_ack = num_of_layers * Qbar_ACK * Qm

    ####6.3.2.4.1.2 CSI part 1
    #calculate total_ACK_rsv_RE = sum of Mbar_ACK_rvd(L) the number of reserved resource
    #elements for potential HARQ-ACK transmission in OFDM symbol defined in Clause 6.2.7
    #in 6.2.7 step 1: if the number of HARQ-ACK information bits to be transmitted on PUSCH is 0, 1 or 2 bits
    #the number of reserved resource elements for potential HARQ-ACK transmission is calculated according to Clause
    #6.3.2.4.2.1, by setting ACK O = 2
    #in 6.3.2.4.2.1: cal Qbar_ACK according to Clause 6.3.2.4.1.1, by setting the number of CRC bits L=0
    # Get the number of reserved ACK bits, based on the number of
    # HARQ-ACK bits
    if OACK <= 2:
        OACKrvd = 2
        NumbitsPlusL = _get_plusLsize(OACKrvd)
        belta_offset = _get_HARQ_ACK_Belta_offset(I_HARQ_ACK_offset)
        if EnableULSCH == 1:
            #For HARQ-ACK transmission on PUSCH with UL-SCH,
            d1 = math.ceil(NumbitsPlusL * belta_offset * TotalMUCI / ULSCH_size)
            Qbar_ACKrvd = min(d1, math.ceil(nAlphaScaling * SumMUCIfromL0))
        else:
            #For HARQ-ACK transmission on PUSCH without UL-SCH
            Qbar_ACKrvd = min(math.ceil(NumbitsPlusL * belta_offset / (Qm*coderateby1024/1024)), math.ceil(nAlphaScaling * SumMUCIfromL0))

    else:
        OACKrvd = 0
        Qbar_ACKrvd = 0
    Euci_ackrvd = num_of_layers * Qbar_ACKrvd * Qm
    
    if OCSI1 == 0:
            Qbar_CSI1 = 0
    else:
        NumbitsPlusL = _get_plusLsize(OCSI1)
        belta_offset = _get_CSI_Belta_offset(I_CSI1offset)
        if NumACKBits > 2:
            #the number of coded modulation symbols per layer for HARQ-ACK transmitted on the PUSCH if
            #number of HARQ-ACK information bits is more than 2,
            Qbar_ACKCSI1 = Qbar_ACK
        else:
            #the number of HARQ-ACK information bits is no more than 2 bits
            Qbar_ACKCSI1 = Qbar_ACKrvd
        
        if EnableULSCH == 1:
            #For CSI part 1 transmission on PUSCH with UL-SCH,
            d1 = math.ceil(NumbitsPlusL * belta_offset * TotalMUCI / ULSCH_size)
            
            Qbar_CSI1 = min(d1, math.ceil(nAlphaScaling * TotalMUCI) - Qbar_ACKCSI1)
        else:
            #For HARQ-ACK transmission on PUSCH without UL-SCH
            if OCSI2 > 0:
                #if there is CSI part 2 to be transmitted on the PUSCH,
                Qbar_CSI1 = min(math.ceil(NumbitsPlusL * belta_offset / (Qm*coderateby1024/1024)), TotalMUCI-Qbar_ACKCSI1)
            else:
                Qbar_CSI1 = TotalMUCI-Qbar_ACKCSI1

    Euci_CSI1 = num_of_layers * Qbar_CSI1 * Qm

    #6.3.2.4.1.3 CSI part 2
    if NumCSI2Bits == 0:
            Qbar_CSI2 = 0
    else:
        NumbitsPlusL = _get_plusLsize(NumCSI2Bits)
        belta_offset = _get_CSI_Belta_offset(I_CSI2offset)
        if NumACKBits > 2:
            #the number of coded modulation symbols per layer for HARQ-ACK transmitted on the PUSCH if
            #number of HARQ-ACK information bits is more than 2,
            Qbar_ACKCSI2 = Qbar_ACK
        else:
            #the number of HARQ-ACK information bits is no more than 2 bits
            Qbar_ACKCSI2 = 0
        
        if EnableULSCH == 1:
            #For CSI part 1 transmission on PUSCH with UL-SCH,
            d1 = math.ceil(NumbitsPlusL * belta_offset * TotalMUCI / ULSCH_size)
            
            Qbar_CSI2 = min(d1, math.ceil(nAlphaScaling * TotalMUCI) - Qbar_ACKCSI2 - Qbar_CSI1)
        else:
            #For HARQ-ACK transmission on PUSCH without UL-SCH
            Qbar_CSI2 = TotalMUCI - Qbar_ACKCSI2 - Qbar_CSI1

    Euci_CSI2 = num_of_layers * Qbar_CSI2 * Qm
    
    assert Gtotal >= Euci_CSI1 + Euci_CSI2
    #get ULSCH E value, refer to 38.212 6.2.7 step 1 and step 2
    #when NumACKBits<=2, phibarULSCH doesn;t remove ACK REs
    if EnableULSCH == 1:
        if NumACKBits > 2:
            G_ULSCH = Gtotal - Euci_CSI1 - Euci_CSI2 - Euci_ack
        else:
            G_ULSCH = Gtotal - Euci_CSI1 - Euci_CSI2
    else:
        G_ULSCH = 0

    #validate rate match values
    #38.212 5.4.1 polar code rate match E is no larger than 8192
    assert Euci_CSI1 <= 8192
    assert Euci_CSI2 <= 8192
    assert Euci_ack <= 8192
    assert Euci_ack >= _getMinUCIBitCapacity(OACK)
    assert Euci_CSI1 >= _getMinUCIBitCapacity(OCSI1)
    assert Euci_CSI2 >= _getMinUCIBitCapacity(OCSI2)

    RMinfo = {}
    RMinfo['Euci_ack'] = Euci_ack
    RMinfo['Qbar_ACK'] = Qbar_ACK
    RMinfo['Euci_CSI1'] = Euci_CSI1
    RMinfo['Qbar_CSI1'] = Qbar_CSI1
    RMinfo['Euci_CSI2'] = Euci_CSI2
    RMinfo['Qbar_CSI2'] = Qbar_CSI2
    RMinfo['Euci_ackrvd'] = Euci_ackrvd
    RMinfo['Qbar_ACKrvd'] = Qbar_ACKrvd
    RMinfo['G_ULSCH'] = G_ULSCH
    return RMinfo

def _get_plusLsize(Numbits):
    if Numbits <= 11:
        #6.3.2.4.2 UCI encoded by channel coding of small block lengths
        L = 0
    else:
        if Numbits >= 360:
            L = 11
        else:
            if Numbits <= 19:
                L = 6
            else:
                L = 11
    
    NumbitsPlusL =  Numbits + L
    return NumbitsPlusL

def _get_HARQ_ACK_Belta_offset(I_HARQ_ACK_offset):
    """ 38.213 Table 9.3-1: Mapping of beta_offset values for HARQ-ACK information and the index signalled by
        higher layers
    """
    table = [1.000,2.000,2.500,3.125,4.000,5.000,6.250,8.000,10.000,12.625, 15.875, 20.000, 31.000, 50.000, 80.000, 126.000]
    assert I_HARQ_ACK_offset in range(16)
    return table[I_HARQ_ACK_offset]

def _get_CSI_Belta_offset(I_CSIoffset):
    """ 38.213 Table 9.3-1: Mapping of beta_offset values for HARQ-ACK information and the index signalled by
        higher layers
    """
    table = [1.125,1.250,1.375,1.625,1.750,2.000,2.250,2.500,2.875,3.125,
            3.500, 4.000, 5.000, 6.250, 8.000, 10.000, 12.625, 15.875, 20.000]
    assert I_CSIoffset in range(19)
    return table[I_CSIoffset]

def _getMinUCIBitCapacity(A):
    """ retur minimum bit capacity for UCI encoding. """
    if A <= 11:  #Small block lengths
        minE = A
    elif A <= 19: #Parity check (PC) polar encoding
        minE = A + 6 + 3  #A+crcLen+nPC
    else:
        crclen = 11
        if A < 1013:
            #One code block segment, A + crcLen
            minE = A + crclen
        else:
            #Two code block segments, A + padding bit if 'A' is odd +crcLen*2
            minE = A + (A % 2) + crclen*2
    
    return minE