# -*- coding:utf-8 -*-

import numpy as np
import math

def gen_dciformat00(NULBWPRB,RIV, Imcs, rv,harqid):
    """ generate DCI format 0_0
    """
    #Identifier for DCI formats – 1 bits
    dci = [0] #UL DCI format

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

    #- TPC command for scheduled PUSCH – 2 bits as defined in Clause 7.1.1 of [5, TS 38.213]
    TPC = 0
    bits = [ (TPC >> (2 - 1 - n)) & 1  for n in range(2) ]
    dci.extend(bits)

    #- Padding bits, if required.

    return np.array(dci)

if __name__ == "__main__":
    #total bit size for 100MHz is 36
    dci = gen_dciformat00(273,20, 5, 2, 1)

    #total bit size for 5MHz 30KHZ scs is 27
    dci = gen_dciformat00(11,20, 5, 2, 1)
    pass