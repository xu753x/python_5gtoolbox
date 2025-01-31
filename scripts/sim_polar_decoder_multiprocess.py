# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL_optionB
from py5gphy.polar import nr_polar_decoder_SC
from py5gphy.polar import nr_polar_decoder_SC_optionB

def verify_polar_decoder(decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,counts):
    failed_count = 0
    for count in range(counts):
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
        LLRin = (1-2*encodedbits) + np.random.normal(0, 10**(-snr_db/20), encodedbits.size)

        if decoder == 'SC':
            decbits, status = nr_polar_decoder_SC.nr_decode_polar_SC(LLRin, E, blkandcrc.size, nMax, iIL)
        elif decoder == 'SC_optionB':
            decbits, status = nr_polar_decoder_SC_optionB.nr_decode_polar_SC_optionB(LLRin, E, blkandcrc.size, nMax, iIL)
        elif decoder == 'SCL':
            decbits, status = nr_polar_decoder_CA_PC_SCL.nr_decode_polar_SCL(LLRin, E, blkandcrc.size, L, nMax, iIL, CRCLEN, padCRC, rnti )
        elif decoder == 'SCL_optionB':
            decbits, status = nr_polar_decoder_CA_PC_SCL_optionB.nr_decode_polar_SCL_optionB(LLRin, E, blkandcrc.size, L, nMax, iIL, CRCLEN, padCRC, rnti )
        else:
            assert 0
        
        #check decoder result
        print('done  decoder={},L={},snr={},count={}'.format(decoder,L,snr_db,count))
        if not np.array_equal(decbits, blkandcrc):
            failed_count += 1
            print("failed, failed number = {}".format(failed_count))
    
    return [[decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,counts],failed_count]

def gen_pool_list():
                #K,     N,   nMax, iIL CRCLEN,padCRC, rnti
    testcase = [64,    128,   10,   0,  11,     0,    0    ]
    K = testcase[0]
    N = testcase[1]; E=N
    nMax = testcase[2]
    iIL = testcase[3]
    CRCLEN = testcase[4]
    padCRC = testcase[5]
    rnti = testcase[6]   

    snr_range = np.arange(0.5,2,0.5).tolist()
    test_decoders = ['SC','SC_optionB','SCL','SCL_optionB']
    L_range = [8,16,32]

    testlist = []
    for decoder in test_decoders:
        if decoder in ['SC','SC_optionB']:
            tmp_L_range = [1]
        else:
            tmp_L_range = L_range
        for L in tmp_L_range:
            for snr_db in snr_range:
                #set test counts
                if decoder in ['SC','SC_optionB']:
                    if snr_db <= 2:
                        testcounts = 200
                    else:
                        testcounts = 600
                else: #['SCL','SCL_optionB']
                    if snr_db <= 2:
                        testcounts = 400
                    elif snr_db <= 3:
                        testcounts = 3000
                    elif snr_db <= 3.5:
                        testcounts = 30000
                    else:
                        testcounts = 10**5

                #generate one test for each 200 testcounts
                for _ in range(testcounts // 200):
                    testlist.append((decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,200))
    
    return testlist

if __name__ == '__main__':
    testlist = gen_pool_list()
    start = time.time()
    with Pool(6) as p:
        for result in p.starmap(verify_polar_decoder, testlist):
            pass
    
    print("polar decoder multi processing elpased time: {:6.6f}".format(time.time() - start))