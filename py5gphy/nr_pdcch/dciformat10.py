# -*- coding:utf-8 -*-

import numpy as np
import math


def gen_dciformat10(NDLBWPRB,RIV, StartSymbolIndex, NrOfSymbols, Imcs, rv,harqid):
    """ generate DCI format 1_0
        support C-RNTI only
    """
    return DCI_format10_CRNTI(NDLBWPRB,RIV, StartSymbolIndex, NrOfSymbols, Imcs, rv,harqid)
    

def DCI_format10_CRNTI(NDLBWPRB,RIV, StartSymbolIndex, NrOfSymbols, Imcs, rv,harqid):
    """ generate DCI format 1-0 CRC scrambled by C-RNTI or CSRNTI or MCS-C-RNTI
    and not for random access procedure initiated by a PDCCH order

    """
    #Identifier for DCI formats – 1 bits
    dci = [1] #DL format

    #Frequency domain resource assignment – 
    riv_size = math.ceil(np.log2(NDLBWPRB*(NDLBWPRB+1)/2))
    rivbits = [ (RIV >> (riv_size - 1 - n)) & 1  for n in range(riv_size) ]
    dci.extend(rivbits)

    #Time domain resource assignment – 4 bits as defined in Clause 5.1.2.1 of [6, TS 38.214]
    if (StartSymbolIndex==2) and (NrOfSymbols==12):
        tdra = 0
    else:
        assert 0
    bits = [ (tdra >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)
    
    #VRB-to-PRB mapping – 1 bit according to Table 7.3.1.2.2-5
    bpb_prb_mapping = 0 #non interleaved
    dci.append(bpb_prb_mapping)
    
    # Modulation and coding scheme – 5 bits as defined in Clause 5.1.3 of [6, TS 38.214]
    mcsbits = [ (Imcs >> (5 - 1 - n)) & 1  for n in range(5) ]
    dci.extend(mcsbits)

    #- New data indicator – 1 bit
    NDI = 1
    dci.append(NDI)
    
    # Redundancy version – 2 bits as defined in Table 7.3.1.1.1-2
    rvbits = [ (rv >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(rvbits)

    #- HARQ process number – 4 bits
    bits = [ (harqid >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)
    #- Downlink assignment index – 2 bits as defined in Clause 9.1.3 of [5, TS 38.213], as counter DAI
    DAI = 0
    bits = [ (DAI >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)
    #- TPC command for scheduled PUCCH – 2 bits as defined in Clause 7.2.1 of [5, TS 38.213]
    TPC = 0
    bits = [ (TPC >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)
    #- PUCCH resource indicator – 3 bits as defined in Clause 9.2.3 of [5, TS 38.213]
    PUCCH_RI = 0
    bits = [ (PUCCH_RI >> (3 - 1 - n)) & 1  for n in range(3) ]
    dci.extend(bits)
    #- PDSCH-to-HARQ_feedback timing indicator – 3 bits as defined in Clause 9.2.3 of [5, TS38.213]
    PDSCH_HARQ_fb_timing = 0
    bits = [ (PDSCH_HARQ_fb_timing >> (3 - 1 - n)) & 1  for n in range(3) ]
    dci.extend(bits)

    return np.array(dci)

def type1_RIV_gen(RBstart, RBsize, NsizeBWP):
    """38.214 5.1.2.2.2 Downlink resource allocation type 1

    """
    if (RBsize - 1) <= (NsizeBWP // 2):
        RIV = NsizeBWP*(RBsize-1) + RBstart
    else:
        RIV = NsizeBWP*(NsizeBWP-RBsize+1) + (NsizeBWP-1-RBstart)
    
    return RIV

if __name__ == "__main__":
    #total bit size for 100MHz is 44
    dci = DCI_format10_CRNTI(273,20, 2, 12, 5, 2, 1)
    #total bit size for 5MHz 30khz scs is 35
    dci = DCI_format10_CRNTI(11,20, 2, 12, 5, 2, 1)
    pass