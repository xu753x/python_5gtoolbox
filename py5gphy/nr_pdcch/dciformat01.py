# -*- coding:utf-8 -*-

import numpy as np
import math

def gen_dciformat01(NULBWPRB,RIV, Imcs, rv,harqid):
    """ generate DCI format 0_1
    """
    #Identifier for DCI formats – 1 bits
    dci = [0] #UL DCI format

    #Carrier indicator – 0 or 3 bits, as defined in Clause 10.1 of [5, TS38.213].
    #0 bit

    #- UL/SUL indicator – 0 bit for UEs not configured with supplementaryUplink in ServingCellConfig
    #0 bit

    #Bandwidth part indicator – 0, 1 or 2 bits as determined by the number of UL BWPs
    #0 bit

    #Frequency domain resource assignment, support non-PUSCH hopping with resource allocation type 1:
    riv_size = math.ceil(np.log2(NULBWPRB*(NULBWPRB+1)/2))
    bits = [ (RIV >> (riv_size - 1 - n)) & 1  for n in range(riv_size) ]
    dci.extend(bits)

    #- Time domain resource assignment – 4 bits as defined in Clause 6.1.2.1 of [6, TS 38.214]
    tdra = 0
    bits = [ (tdra >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)

    #- Frequency hopping flag – 1 bit according to Table 7.3.1.1.1-3, as defined in Clause 6.3 of [6, TS 38.214]
    hopping = 0
    dci.append(hopping)

    #- Modulation and coding scheme – 5 bits as defined in Clause 6.1.4.1 of [6, TS 38.214]
    mcsbits = [ (Imcs >> (5 - 1 - n)) & 1  for n in range(5) ]
    dci.extend(mcsbits)

    #- New data indicator – 1 bit
    NDI = 1
    dci.append(NDI)

    #- Redundancy version – 2 bits as defined in Table 7.3.1.1.1-2
    rvbits = [ (rv >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(rvbits)

    #- HARQ process number – 4 bits
    bits = [ (harqid >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)

    #1st downlink assignment index – 1 or 2 bits
    # select 2 bits for dynamic HARQ-ACK codebook
    dai = 0
    bits = [ (dai >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)

    #2nd downlink assignment index – 0 or 2 bits
    #0 bit

    #SRS resource indicator
    #support Tables 7.3.1.1.2-32 if the higher layer parameter txConfig = codebook
    #and NSRS = 2, number of bits = 1
    srs_id = 1
    dci.append(srs_id)

    #Precoding information and number of layers – number of bits determined by the following
    #select5 4 bits
    precoding_info = 0
    bits = [ (precoding_info >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)

    #Antenna ports – number of bits determined by the following
    #select 4 bits
    ant_port = 0
    bits = [ (ant_port >> (4 - 1 - n)) & 1  for n in range(4) ]
    dci.extend(bits)

    #SRS request – 2 bits as defined by Table 7.3.1.1.2-24 for UEs not configured with supplementaryUplink
    srs_req = 0
    bits = [ (srs_req >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)

    #CSI request – 0, 1, 2, 3, 4, 5, or 6 bits determined by higher layer parameter reportTriggerSize
    #select 0 bit

    #CBG transmission information (CBGTI) –
    # 0 bit

    #PTRS-DMRS association
    #0bit

    #beta_offset indicator – 0 if the higher layer parameter betaOffsets = semiStatic; otherwise 2 bits as defined by
    #Table 9.3-3 in [5, TS 38.213].
    #2 bits
    beta_offset = 0
    bits = [ (beta_offset >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)

    #DMRS sequence initialization – 0 bit if transform precoder is enabled; 1 bit if transform precoder is disabled
    DMRS_seq_init = 0
    dci.append(DMRS_seq_init)

    #UL-SCH indicator – 1 bit. A value of "1" indicates UL-SCH shall be transmitted on the PUSCH
    UL_SCH_ind = 0
    dci.append(UL_SCH_ind)

    return np.array(dci)

if __name__ == "__main__":
    #total bit size for 100MHz is 51
    dci = gen_dciformat01(273,20, 5, 2, 1)

    #total bit size for 5MHz 30KHZ scs is 42
    dci = gen_dciformat01(11,20, 5, 2, 1)
    pass