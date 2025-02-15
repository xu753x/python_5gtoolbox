# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.polar import nr_polar_decoder_CA_PC_SCL
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL_optionB
from py5gphy.polar import nr_polar_decoder_SC
from py5gphy.polar import nr_polar_decoder_SC_optionB
from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder

def nr_decode_polar(algo, LLRin, E, K, L, nMax, iIL, CRCLEN=24, padCRC=0, rnti=0):
    """ polar decoder
    support LLR based SC and SC_optionB, 
            LLR based CRC-aided PC-check Distributed CRC-aided SCL and SCL-optionB
            I have verified that option B algorithm are the same with non-optionB algorithm
    input:
        algo: ['SC', 'SC_optionB', 'SCL', 'SCL_optionB']
        LLRin: N length input LLR demodulation data
        N: length of polar decoder input data
        E: rate match length
        K: decoded data length
        (nMax, iIL,CRCLEN): (9, 1,24) apply for DL and (10, 0,11),(10, 0,6) apply for UL
        L: SCL polar decoder list length, shoule be even value
        CRCLEN: CRClength, CRC is used for CRC-aided SCL decoder
        padCRC: 1: padding 24 '1' ahead of CRC data for CRC encoder which is used by DL DCI
                0: no padding which is used by DL BCH
        rnti: used by DL DCI CRC mask
    output:
        decbits: L length bits
        status: True or False        
    """

    if algo == 'SC':
        ck, status = nr_polar_decoder_SC.nr_decode_polar_SC(LLRin, E, K, nMax, iIL)
    elif algo == 'SC_optionB':
        ck, status = nr_polar_decoder_SC_optionB.nr_decode_polar_SC_optionB(LLRin, E, K, nMax, iIL)
    elif algo == 'SCL':
        ck, status = nr_polar_decoder_CA_PC_SCL.nr_decode_polar_SCL(LLRin, E, K, L, nMax, iIL, CRCLEN, padCRC, rnti)
    elif algo == 'SCL_optionB':
        ck, status = nr_polar_decoder_CA_PC_SCL_optionB.nr_decode_polar_SCL_optionB(LLRin, E, K, L, nMax, iIL, CRCLEN, padCRC, rnti)
    else:
        assert 0
    return ck, status

def for_test_5g_polar_encoder(K, E, nMax, iIL,snr_db= 8,CRCLEN=24,padCRC=0,rnti=0):
    inbits = np.random.randint(2, size=K)
    poly = {6:'6', 11: '11', 24: '24C'}[CRCLEN]
    if padCRC == 0:
        blkandcrc = crc.nr_crc_encode(inbits, poly)
    else:
        #add 24 '1' ahead before CRC24C
        inbits = np.concatenate((np.ones(24,'i1'), inbits))
        blkandcrc = crc.nr_crc_encode(inbits, poly,rnti)
        blkandcrc = blkandcrc[24:]

    encodedbits =  nr_polar_encoder.encode_polar(blkandcrc, E, nMax, iIL)
    
    #LLR generation
    en = 1 - 2*encodedbits #BPSK modulation, 0 -> 1, 1 -> -1
    fn = en + np.random.normal(0, 10**(-snr_db/20), en.size) #add noise
    
    #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
    noise_power = 10**(-snr_db/10)
    LLRin = 2*fn/noise_power

    return LLRin, encodedbits, blkandcrc


if __name__ == "__main__":
    pass
