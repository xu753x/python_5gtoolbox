# -*- coding: utf-8 -*-
import numpy as np
import time
import pickle

from scripts.internal import sim_polar_internal

""" the script is used to simulate polar decoder performance
it support ['SC', 'SC_optionB', 'SCL', 'SCL_optionB']
'SC' and 'SC_optionB' have the same performance, just different way of implementation
'SCL' and 'SCL_optionB' also have the same performance and different implementation
the detailed polar decoder information is in docs/Detailed explanation of 5G NR Polar design and implementation of CA-SCL decoder
"""

""" below is the list of polar configuration supported in 5G
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

"""

######################## test 1: test all four algo and three L values for one test case #################
#5G polar config parameters
#testcase is one of line from above table
testcase_list = [
    #K,     N,   nMax, iIL CRCLEN,padCRC, rnti
    [64,    128,   10,   0,  11,     0,    0    ]
]

# polar decoder config
algo_list = ['SC','SC_optionB','SCL','SCL_optionB']
L_list = [8, 16, 32]

#simulation config
snr_db_list = np.arange(0.5, 4, 0.5).tolist()

filename = "out/polar_decode_result_all.pickle" #test result save to this file
figfile = "out/polar_decode_result_all.png"     #plt draw figure saveto this file
sim_flag = 0  #if 1, start simulation, if 0, no simulation, read from filename and does test result analysis

#main function, generate BLER for each decoder
if sim_flag == 1:
    sim_polar_internal.run_polar_simulation(testcase_list,algo_list,L_list,snr_db_list,filename)

with open(filename, 'rb') as handle:
    [testcase_list,snr_db_list, test_results_list] = pickle.load(handle)
sim_polar_internal.draw_polar_decoder_result(testcase_list, snr_db_list, test_results_list, figfile)

######################## test 2: test SCL only for all polar configuration and  #################
#5G polar config parameters
#testcase is one of line from above table
            #K,     N,   nMax, iIL CRCLEN,padCRC, rnti
testcase_list = [
     #K,     N,   nMax, iIL CRCLEN,padCRC, rnti,     
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
    [600,   1024,  10,   0,  11,     0,    0,         ]

]

# polar decoder config
algo_list = ['SCL']
L_list = [16,32]

#simulation config
snr_db_list = np.arange(0.5, 3.5, 0.5).tolist()

filename = "out/polar_decode_result_all_testcases.pickle" #test result save to this file
figfile = "out/polar_decode_result_all_testcases.png"     #plt draw figure saveto this file
sim_flag = 0  #if 1, start simulation, if 0, no simulation, read from filename and does test result analysis

#main function, generate BLER for each decoder
if sim_flag == 1:
    sim_polar_internal.run_polar_simulation(testcase_list,algo_list,L_list,snr_db_list,filename)

with open(filename, 'rb') as handle:
    [testcase_list,snr_db_list, test_results_list] = pickle.load(handle)
sim_polar_internal.draw_polar_decoder_result(testcase_list, snr_db_list, test_results_list, figfile)
sim_polar_internal.to_excel_polar_decoder_result(testcase_list, snr_db_list, test_results_list, figfile)

pass
