# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_ratematch
from py5gphy.common import nrPRBS

def genBCHMIB(ssb_config, sfn):
    """ return 24 bits BCH sequence,
    refer to 38.331 6.2.1
    MIB msg bit length is 23 bits, below BCCH-BCH-MessageType CHOICE 
    occupy 1 bit. so totola BCH sequence is 24 bits
    feature:
        only support sub-6GHz, not support mmWave, so Lmax = 4 or 8
        Lmax = 64 is for mmWave only
        there is no candidate SS/PBCH block index in BCH payload
    BCCH-BCH-MessageType ::= CHOICE {
    mib MIB,
    messageClassExtension SEQUENCE {}
    }
    MIB msg
    MIB ::= SEQUENCE {
    #The 6 most significant bits (MSB) of the 10-bit System Frame Number (SFN). The 4 LSB of the SFN are conveyed in the PBCH transport block as part of channel coding (i.e.
    #outside the MIB encoding), as defined in clause 7.1 in TS 38.212 
    systemFrameNumber BIT STRING (SIZE (6)), => 6 bits, 
    subCarrierSpacingCommon ENUMERATED {scs15or60, scs30or120}, => 1 bit
    ssb-SubcarrierOffset INTEGER (0..15), => 4 bits
    dmrs-TypeA-Position, ENUMERATED {pos2, pos3},  => 1 bit
    pdcch-ConfigSIB1, INTEGER (0..255), => 8 bits
    cellBarred,  ENUMERATED {barred, notBarred},  => 1 bit
    intraFreqReselection ENUMERATED {allowed, notAllowed}, => 1 bit
    spare    BIT STRING (SIZE (1)) => 1 bit
    }            

    """
    kSSB = ssb_config["kSSB"]
    bchmib = np.zeros(24,'i1')
    #sfn MSB 6 bits
    bchmib[1:7] = [sfn >> i & 1 for i in range(9,3,-1)]
    bchmib[7] = ssb_config["MIB"]["subCarrierSpacingCommon"]
    # 4 least kSSB bits
    bchmib[8:12] = [kSSB >> i & 1 for i in range(3,-1,-1)]
    bchmib[12] = ssb_config["MIB"]["dmrs_TypeA_Position"]
    d = ssb_config["MIB"]["pdcch_ConfigSIB1"]
    bchmib[13:21] = [d >> i & 1 for i in range(7,-1,-1)]
    bchmib[21] = ssb_config["MIB"]["cellBarred"]
    bchmib[22] = ssb_config["MIB"]["intraFreqReselection"]
    #last bit is spare bit
    return bchmib

def nrBCHencode(mib, ssb_config, sfn,HRF,NcellID):
    """ BCH payload generation, CRC, polar, rate match
        refer to 3gpp 38.212 7.1
    rm_bitseq = nrBCH(mib, ssb_config, sfn,HRF,NcellID)
        HRF: half frame bit, 0 if first half frame, 1 for second half frame
    """
    #generate sequence
    abar = np.zeros(32, 'i1') #total size is 32 bits
    abar[0:24] = mib
    abar[24:28] = [sfn >> i & 1 for i in range(3,-1,-1)] #4 LSB bits
    abar[28] = HRF
    #support FR1 and without shared spectrum channel only, Lmax = 4 or 8
    kSSB = ssb_config["kSSB"]
    abar[29] = (kSSB >> 4) & 1 #MSB of 5 bits kSSB

    # G(j) as per 38.212 Table 7.1.1-1
    G = [16, 23, 18, 17, 8, 30, 10, 6, 24, 7, 0, 5, 3,
         2, 1, 4, 9, 11, 12, 13, 14, 15, 19, 20, 21, 22, 25, 26, 27, 28, 29, 31]
    
    #payload interleaving
    a = np.zeros(32, 'i1')
    is_scramble = np.ones(32, 'i1') #
    A = 32
    jSFN = 0
    jHRF = 10
    jSSB = 11
    jother = 14
    for idx in range(A):
        if((idx in [1,2,3,4,5,6]) or (idx in [24,25,26,27])):
            #first 6 bits is 6 MSB bits of SFN,24-27 are 4 LSB bits of SFN
            a[G[jSFN]] = abar[idx]
            
            if idx in [25,26]: #3rd and 2nd LSB of SFN, no need scrambling
                is_scramble[G[jSFN]] = 0
            jSFN += 1
        elif idx == 28: #HRF
            a[G[jHRF]] = abar[idx]
            is_scramble[G[jSFN]] = 0 #HRF bit no need scrambling
        elif idx in [29,30,31]: #kSSB
            a[G[jSSB]] = abar[idx]
            jSSB += 1
        else:
            a[G[jother]] = abar[idx]
            jother += 1

    #scrambling
    M = A - 3 #for Lmax 4 or 8
    v = abar[25]*2 + abar[26]
    prbs_seq = nrPRBS.gen_nrPRBS(NcellID,M*(v+1))
    is_scramble[is_scramble==1] = prbs_seq[v*M:v*M+M]
    trblk = (is_scramble + a) % 2

    #24C CRC, 38.212 7.1.3
    blkandcrc = crc.nr_crc_encode(trblk, '24C')

    #polar encoder
    K = blkandcrc.size #must be 56
    assert K == 56
    E = 864 #38.212 7.1.5
    nMax = 9
    iIL = 1
    polarbits = nr_polar_encoder.encode_polar(blkandcrc, E,  nMax, iIL)

    #rate match
    iBIL = 0
    rm_bitseq = nr_polar_ratematch.ratematch_polar(polarbits, K, E, iBIL)

    return rm_bitseq

if __name__ == "__main__":
    print("test MIB generation")
    from tests.nr_ssb import test_nrBCH
    file_lists = test_nrBCH.get_mib_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nrBCH.test_genBCHMIB(filename)
    
    print("test nr BCH encoder")
    from tests.nr_ssb import test_nrBCH
    file_lists = test_nrBCH.get_nrBCH_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nrBCH.test_nrBCHencode(filename)