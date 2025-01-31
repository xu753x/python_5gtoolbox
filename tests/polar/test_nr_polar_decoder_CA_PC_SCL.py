# -*- coding: utf-8 -*-
import numpy as np
import pytest
import math

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_decoder_SC
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL

"""
K: input bit size before CRC
N: polar encode size by 2^m
(nMax, iIL,CRCLEN, padCRC,rnti): 
    [9,1,24, 0,0] for DL BCH, K<=140
    [9,1,24, 1,xxx] for DL DCI, K<=140
    [10,0,6] for UL DCI with K in [12:19]
    [10,0,11] for UL UCI with K >=20
L: SCL polar decoder path size
snr_db: SNR in db, 255 means no noise
"""
testlists = \
[   #K,     N,   nMax, iIL CRCLEN,padCRC, rnti,     L,  snr_db
    [20,    64,    9,    1,  24,     0,    0,       1,   255  ],
    [30,    64,    9,    1,  24,     0,    0,       8,   30  ],
    [40,    128,   9,    1,  24,     0,    0,       16,   30  ],
    [40,    128,   9,    1,  24,     1,    1,       16,   30  ],
    [60,    128,   9,    1,  24,     1,    12345,   16,  30  ],
    [100,   256,   9,    1,  24,     1,    2345,    16,  30  ],
    [140,   512,   9,    1,  24,     1,    32345,   12,  30  ],
    [12,    64,    10,   0,  6,      0,    0,       8,   30  ],  #n_wm_PC=0
    [14,    256,    10,   0,  6,      0,    0,       8,   30  ], #n_wm_PC=1
    [19,    64,   10,   0,  6,      0,    0,       8,   30  ],  #CRC6
    [20,    128,   10,   0,  11,     0,    0,       8,   30  ],
    [100,   256,   10,   0,  11,     0,    0,       16,   30  ],
    [400,   512,   10,   0,  11,     0,    0,       16,   30  ],
    [600,   1024,  10,   0,  11,     0,    0,       16,   30  ],
]
def get_testvectors():                        
    return testlists

@pytest.mark.parametrize('testcase', get_testvectors())
def test_nr_polar_SCL_decoder_no_noise(testcase):
    K = testcase[0]
    N = testcase[1]; E=N
    nMax = testcase[2]
    iIL = testcase[3]
    CRCLEN = testcase[4]
    padCRC = testcase[5]
    rnti = testcase[6]
    L = testcase[7]
    snr_db = testcase[8]
    
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
    LLRin = (1-2*encodedbits) # no noise

    decbits, status = nr_polar_decoder_CA_PC_SCL.nr_decode_polar_SCL(LLRin, E, blkandcrc.size, L, nMax, iIL, CRCLEN, padCRC, rnti )
    assert status == True
    assert np.array_equal(decbits, blkandcrc)

@pytest.mark.parametrize('testcase', get_testvectors())
def test_nr_polar_SCL_decoder(testcase):
    K = testcase[0]
    N = testcase[1]; E=N
    nMax = testcase[2]
    iIL = testcase[3]
    CRCLEN = testcase[4]
    padCRC = testcase[5]
    rnti = testcase[6]
    L = testcase[7]
    snr_db = testcase[8]
    
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
    if snr_db != 255:
        LLRin = (1-2*encodedbits) + np.random.normal(0, 10**(-snr_db/20), encodedbits.size)
    else:
        LLRin = (1-2*encodedbits)

    decbits, status = nr_polar_decoder_CA_PC_SCL.nr_decode_polar_SCL(LLRin, E, blkandcrc.size, L, nMax, iIL, CRCLEN, padCRC, rnti )
    assert status == True
    assert np.array_equal(decbits, blkandcrc)

