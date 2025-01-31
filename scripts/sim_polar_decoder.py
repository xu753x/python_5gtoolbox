# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import time

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL
from py5gphy.polar import nr_polar_decoder_CA_PC_SCL_optionB
from py5gphy.polar import nr_polar_decoder_SC
from py5gphy.polar import nr_polar_decoder_SC_optionB

### this is single process polor decoder simulation
# based on simulation
# SC BLER over Eb/No relation is  70%/1.5dB, 30%/3dB
# SCL L=8 BLER over Eb/No relation is 10%/2dB, 1%/3dB
# SCL L=16 BLER over Eb/No relation is 10%/1.8dB, 1%/2.6dB
# SCL L=32 BLER over Eb/No relation is 10%/1.6dB, 1%/2.4dB

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

#config simulation parameters

#test SC and SCL
            #K,     N,   nMax, iIL CRCLEN,padCRC, rnti
testcase = [64,    128,   10,   0,  11,     0,    0    ]
K = testcase[0]
N = testcase[1]; E=N
nMax = testcase[2]
iIL = testcase[3]
CRCLEN = testcase[4]
padCRC = testcase[5]
rnti = testcase[6]   

snr_range = np.arange(0.5,3.5,0.5).tolist()
test_decoders = ['SC','SC_optionB','SCL','SCL_optionB']
L_range = [8,16,32]

#start polar decoder simulation
start = time.time()
test_results_list = [testcase]
#main function, generate BLER for each decoder
for decoder in test_decoders:
    if decoder in ['SC','SC_optionB']:
        tmp_L_range = [1]
    else:
        tmp_L_range = L_range
    for L in tmp_L_range:
        test_result = [[decoder, L]]
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
                    testcounts = 200 * process_testcount
                else:
                    testcounts = 10**3 * process_testcount

            failed_count = 0
            for count in range(testcounts):
                #run polar test with encoder and decoder
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
                #print('done  decoder={},L={},snr={},count={}'.format(decoder,L,snr_db,count))
                if not np.array_equal(decbits, blkandcrc):
                    failed_count += 1
                    #print("decoder={},L={},snr={},count={},failed, failed number = {}".format(decoder,L,snr_db,count,failed_count))
            
            #save test result
            bler = failed_count/testcounts
            test_result.append([snr_db, bler])
        
        test_results_list.append(test_result)

print("polar decoder single processing elpased time: {:6.6f}".format(time.time() - start))

#draw the plot
marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
marker_count = 0
plt.xlabel("Eb/N0")
plt.ylabel("BLER")
plt.title("polar decoder, N={}, K={}".format(N,K))
plt.yscale("log")
plt.xlim(snr_range[0]-0.5,snr_range[-1]+1)
plt.ylim(10**(-5),1)
plt.grid(True)

for test in test_results_list[1:]:
    set_label = test[0][0] + ', L=' + str(test[0][1])
    xd = [x1 for x1,y1 in test[1:]]
    yd = [y1 for x1,y1 in test[1:]]
    plt.plot(xd, yd, marker=marker_list[marker_count], label=set_label)
    marker_count =(marker_count+1) % len(marker_list)

plt.legend(loc="upper right",fontsize=5)
plt.savefig("polar_decoder.png")
plt.show()


pass