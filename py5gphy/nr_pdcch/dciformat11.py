# -*- coding:utf-8 -*-

import numpy as np
import math

def gen_dciformat11(NDLBWPRB,RIV, StartSymbolIndex, NrOfSymbols, Imcs, rv,harqid):
    """ generate DCI format 1_1
    """

    #Identifier for DCI formats – 1 bits
    dci = [1] #DL format

    #Carrier indicator – 0 or 3 bits as defined in Clause 10.1 of [5, TS 38.213].
    #select 0 bits

    #- Bandwidth part indicator – 0, 1 or 2 bits as determined by the number of DL BWPs
    #select 0 bits

    #Frequency domain resource assignment, select resource allocation type 1
    riv_size = math.ceil(np.log2(NDLBWPRB*(NDLBWPRB+1)/2))
    bits = [ (RIV >> (riv_size - 1 - n)) & 1  for n in range(riv_size) ]
    dci.extend(bits)

    #Time domain resource assignment – 0, 1, 2, 3, or 4 bits as defined in Clause 5.1.2.1 of [6, TS 38.214].
    #select 4 bits
    if (StartSymbolIndex==2) and (NrOfSymbols==12):
        tdra = 0
    else:
        assert 0
    bits = [ (tdra >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)
    
    #VRB-to-PRB mapping – 1 bit according to Table 7.3.1.2.2-5
    bpb_prb_mapping = 0 #non interleaved
    dci.append(bpb_prb_mapping)

    #PRB bundling size indicator – 0 bit if the higher layer parameter prb-BundlingType is not configured
    #select 0 bit

    #Rate matching indicator – 0, 1, or 2 bits according to higher layer parameters
    #select 0 bit

    #ZP CSI-RS trigger – 0, 1, or 2 bits as defined in Clause 5.1.4.2 of [6, TS 38.214].
    #select 0 bit

    #For transport block 1:
    # Modulation and coding scheme – 5 bits as defined in Clause 5.1.3 of [6, TS 38.214]
    mcsbits = [ (Imcs >> (5 - 1 - n)) & 1  for n in range(5) ]
    dci.extend(mcsbits)

    #- New data indicator – 1 bit
    NDI = 1
    dci.append(NDI)
    
    # Redundancy version – 2 bits as defined in Table 7.3.1.1.1-2
    rvbits = [ (rv >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(rvbits)

    #For transport block 2 (only present if maxNrofCodeWordsScheduledByDCI equals 2):
    #choose maxNrofCodeWordsScheduledByDCI = 1 which means no TB2

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

    #Antenna port(s) – 4, 5, or 6 bits as defined by Tables 7.3.1.2.2-1/2/3/4
    #support only Tables 7.3.1.2.2-1, 4 bits
    ant_port = 0
    bits = [ (ant_port >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)

    #Transmission configuration indication – 0 bit if higher layer parameter tci-PresentInDCI is not enabled;
    # 0 bit

    #SRS request – 2 bits as defined by Table 7.3.1.1.2-24 for UEs not configured with supplementaryUplink
    srs_present = 0
    bits = [ (srs_present >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)

    #CBG transmission information (CBGTI) – 0 bit if higher layer parameter codeBlockGroupTransmission for
    #PDSCH is not configured,
    #select 0 bit

    #- CBG flushing out information (CBGFI) – 1 bit if higher layer parameter codeBlockGroupFlushIndicator is
    #configured as "TRUE", 0 bit otherwise.
    #select 0 bit

    #- DMRS sequence initialization – 1 bit.
    #nSCID value
    nSCID = 0
    dci.append(nSCID)

    return np.array(dci)

if __name__ == "__main__":
    #total bit size for 100MHz is 51
    dci = gen_dciformat11(273,20, 2, 12, 5, 2, 1)

    #total bit size for 5MHz 30KHZ scs is 42
    dci = gen_dciformat11(11,20, 2, 12, 5, 2, 1)
    pass

