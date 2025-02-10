# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time
import os

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL_optionB
from py5gphy.polar import nr_polar_decoder_SC
from py5gphy.polar import nr_polar_decoder_SC_optionB

### this is multi processes polor decoder simulation to make simulation faster
# based on simulation
# SC BLER over Eb/No relation is  70%/1.5dB, 30%/3dB
# SCL L=8 BLER over Eb/No relation is 10%/2dB, 1%/3dB
# SCL L=16 BLER over Eb/No relation is 10%/1.8dB, 1%/2.6dB
# SCL L=32 BLER over Eb/No relation is 10%/1.6dB, 1%/2.4dB

def gen_pool_list():
    """ generate testlist for pool mapping
    """
    #set test case
    """ below is the list of polar configuration in 5G
    [#K,     N,   nMax, iIL CRCLEN,padCRC, rnti,     
    [20,    64,    9,    1,  24,     0,    0,         ],
    [30,    64,    9,    1,  24,     0,    0,        ],
    [40,    128,   9,    1,  24,     0,    0,         ],
    [40,    128,   9,    1,  24,     1,    1,         ],
    [60,    128,   9,    1,  24,     1,    12345,    ],
    [100,   256,   9,    1,  24,     1,    2345,     ],
    [140,   512,   9,    1,  24,     1,    32345,    ],
    [12,    64,    10,   0,  6,      0,    0,        ],  #n_wm_PC=0
    [14,    256,    10,   0,  6,      0,    0,        ], #n_wm_PC=1
    [19,    64,   10,   0,  6,      0,    0,       ],  #CRC6
    [20,    128,   10,   0,  11,     0,    0,        ],
    [100,   256,   10,   0,  11,     0,    0,         ],
    [400,   512,   10,   0,  11,     0,    0,         ],
    [600,   1024,  10,   0,  11,     0,    0,         ],

    L usually choose 8,16,32
    snr_db range is [0:4], BLER is less than 10^(-4) for sbr >= 4dB
    """

                #K,     N,   nMax, iIL CRCLEN,padCRC, rnti
    testcase = [64,    128,   10,   0,  11,     0,    0    ]
    K = testcase[0]
    N = testcase[1]; E=N
    nMax = testcase[2]
    iIL = testcase[3]
    CRCLEN = testcase[4]
    padCRC = testcase[5]
    rnti = testcase[6]   

    snr_range = np.arange(0, 3, 0.4).tolist() 
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
                process_testcount = 100
                if decoder in ['SC','SC_optionB']:
                    if snr_db <= 2:
                        testcounts = 2 * process_testcount
                    else:
                        testcounts = 6 * process_testcount
                else: #['SCL','SCL_optionB']
                    if snr_db <= 2:
                        testcounts = 2 * process_testcount
                    elif snr_db <= 3:
                        testcounts = 20 * process_testcount
                    elif snr_db <= 3.5:
                        testcounts = 40 * process_testcount
                    else:
                        testcounts = 10**2 * process_testcount

                #generate one test for each 100 testcounts
                for _ in range(testcounts // process_testcount):
                    testlist.append((decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,process_testcount))
    
    return testlist, snr_range

def verify_polar_decoder(decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,counts):
    print("process is = {},decoder={},L={},snr={}".format(os.getpid(),decoder,L,snr_db))
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
        
        en = 1 - 2*encodedbits #BPSK modulation, 0 -> 1, 1 -> -1
        fn = en + np.random.normal(0, 10**(-snr_db/20), en.size) #add noise
        #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
        noise_power = 10**(-snr_db/10)
        LLRin = fn/noise_power

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
        #print('done  decoder={},L={},snr={},count={}'.format(decoder,L,snr_db,count))
        if not np.array_equal(decbits, blkandcrc):
            failed_count += 1
            #print("decoder={},L={},snr={},count={},failed, failed number = {}".format(decoder,L,snr_db,count,failed_count))
    
    return [[decoder,K,E,nMax,iIL,CRCLEN,padCRC,rnti,L,snr_db,counts],failed_count]

if __name__ == '__main__':
    testlist, snr_range = gen_pool_list()
    
    #test_config_list save testcase configuration: [decoder, L]
    #test_config_list example :[['SC', 1], ['SC_optionB', 1], ['SCL', 8], ['SCL_optionB', 16]]
    test_config_list = []
    
    #test_results_list save [snr, total_count, failed_count] list per snr for each testcase
    #test_results_list example:
    #                       snr,total_count,failed_count     snr, total_count,failed_count
    #test_results_list[0]:  [[0.5, 100,             88],     [1.0, 100,            82]]  for ['SC', 1]
    #test_results_list[1]:  [[0.5, 100,             96],     [1.0, 100,            78]] for  ['SC_optionB', 1]
    #test_results_list[2]:  [[0.5, 100,             65],     [1.0, 100,            47]]  for ['SCL', 8]
    #test_results_list[3]:  [[0.5, 100,             53],     [1.0, 100,            38]]  for ['SCL_optionB', 16]
    test_results_list = []
    
    start = time.time()
    with Pool(8) as p:
        for result in p.starmap(verify_polar_decoder, testlist):
            decoder = result[0][0]
            L = result[0][8]
            snr_db = result[0][9]
            counts = result[0][10]
            failed_count = result[1]
            test_cfg = [decoder, L]
            
            if test_cfg not in test_config_list:
                test_config_list.append(test_cfg)
                test_result = [[snr,0,0] for snr in snr_range]
                test_results_list.append(test_result)
            
            idx = test_config_list.index(test_cfg)
            test_result = test_results_list[idx]

            for i ,value in  enumerate(test_result):
                if value[0] == snr_db:
                    sub_idx = i
                    break

            test_result[sub_idx][1] += counts
            test_result[sub_idx][2] += failed_count
            
    
    print("polar decoder multi processing elpased time: {:6.6f}".format(time.time() - start))

    #draw the plot
    marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
    marker_count = 0
    plt.xlabel("Eb/N0")
    plt.ylabel("BLER")
    plt.title("polar decoder, N={}, K={}".format(testlist[0][2],testlist[0][1]))
    plt.yscale("log")
    plt.xlim(snr_range[0]-0.5,snr_range[-1]+1)
    plt.ylim(10**(-5),1)
    plt.grid(True)

    for idx, testcfg in enumerate(test_config_list):
        set_label = testcfg[0] + ', L=' + str(testcfg[1])
        xd = [snr for snr, total_count,failed_count in test_results_list[idx]]
        yd = [failed_count/total_count for snr, total_count,failed_count in test_results_list[idx]]
        plt.plot(xd, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)

    plt.legend(loc="upper right",fontsize=5)
    plt.savefig("polar_decoder_mp.png") #plt.show() didn't work if remotely accessing linux platform, save to picture
    plt.show()  #the cmd show plot for windows platform
    

    pass