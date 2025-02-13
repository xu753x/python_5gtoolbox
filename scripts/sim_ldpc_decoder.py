# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time
import os
import pickle

from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import nr_ldpc_decode
from scripts.internal import sim_ldpc_internal

"""the script is used to simulate soft-decision LDPC decoder performance
it support [ 'BP', 'min-sum', 'NMS', 'OMS', 'mixed-min-sum] algorithms
'BP: 'belief propagation' or 'sum-product' in other name
'min-sum': 'min-sum'
'NMS': normalized min-sum with alpha in (0,1) and beta = 0
'OMS': offset min-sum, with alpha = 1 and beta in (0,1)
'mixed-MS': combination of NMS and OMS, with alpha in (0,1) and beta in (0,1)
"""

#5G LDPC config, Zc and bgn
Zc = 10  # Z value in 38.211 Table 5.3.2-1: Sets of LDPC lifting size Z
bgn = 1 #bgn in [1,2]
crcpoly = '24A'  #default value, no need change in the simulation

#LDPC decoder config
#algo_list = [ 'BP', 'min-sum', 'NMS', 'OMS','mixed-MS']
algo_list = [ 'BP', 'NMS', 'OMS','mixed-MS']

#alpha_list = [0.8, 0.5] #used for NMS only
alpha_list = [0.5] #used for NMS only

#beta_list = [0.3, 0.1]  #used for OMS only
beta_list = [0.3]  #used for OMS only

mixed_list = [[0.8, 0.3]] #used for mixed-min-sum, provide [alpha,beta] pair
#L_list = [32] #ldpc decoder iteration number
L_list = [32, 16, 64] #ldpc decoder iteration number

#simulation config
#snr_db_list = np.arange(-1, 1.5, 0.5).tolist()
snr_db_list = np.arange(-1, 1, 0.5).tolist()

test_count_seed = 300 #used to generate total test count for each snr
filename = "out/ldpc_decode_result_for_L.pickle" #test result save to this file
figfile = "out/ldpc_decode_result_for_L.png"     #plt draw figure saveto this file
sim_flag = 1  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis


########################## main function ############################
if sim_flag == 0:
    algo_list = [] #disable long time LDPC encoder/.decoder

test_results_list = []
test_config_list = []
for algo in algo_list:

    #get number of test for the algo
    if algo in ['BP', 'BF','min-sum']:
        test_num = 1
    elif algo == 'NMS':
        test_num = len(alpha_list)
    elif algo == 'OMS':
        test_num = len(beta_list)
    else:
        test_num = len(mixed_list)
    
    #simulate each test
    for L in L_list:
        for test_idx in range(test_num):
        
            #add to test_result
            if algo in ['BF', 'BP', 'min-sum']:
                test_flag = '{} L={}'.format(algo, L)
            elif algo == 'NMS':
                test_flag = 'NMS-alpha={}-L={}'.format(alpha_list[test_idx], L)
            elif algo == 'OMS':
                test_flag = 'OMS-beta={}-L={}'.format(beta_list[test_idx], L)
            else:
                test_flag = 'mixed-MS-[alpha,beta]=[{},{}]-L={}'.format(mixed_list[test_idx][0], mixed_list[test_idx][1],L)
        
            test_config_list.append(test_flag)

            bler_result = [] #bler_result save bler value for each snr_db
            for snr_db in snr_db_list:
                start = time.time()
                #get total test count, higher snr need more simulation
                if snr_db < 0:
                    total_count = test_count_seed
                elif snr_db == 0:
                    total_count = test_count_seed*4
                else:
                    total_count = test_count_seed * 15
            
                failed_count = 0
                for _ in range(total_count):
                    blkandcrc, dn, LLRin = nr_ldpc_decode.for_test_5g_ldpc_encoder(Zc, bgn, snr_db, crcpoly)
                    if algo in ['BF', 'BP', 'min-sum']:
                        blkandcrc_decoded, ck_decoded, status = nr_ldpc_decode.nr_decode_ldpc(LLRin, Zc, bgn, L, algo,alpha=1, beta=0)
                    elif algo == 'NMS':
                        blkandcrc_decoded, ck_decoded, status = nr_ldpc_decode.nr_decode_ldpc(LLRin, Zc, bgn, L, 'min-sum',alpha=alpha_list[test_idx], beta=0)
                    elif algo == 'OMS':
                        blkandcrc_decoded, ck_decoded, status = nr_ldpc_decode.nr_decode_ldpc(LLRin, Zc, bgn, L, 'min-sum',alpha=1, beta=beta_list[test_idx])
                    else:
                        blkandcrc_decoded, ck_decoded, status = nr_ldpc_decode.nr_decode_ldpc(LLRin, Zc, bgn, L, 'min-sum',alpha= mixed_list[test_idx][0], beta= mixed_list[test_idx][1])
                
                    #check result
                    if not np.array_equal(blkandcrc, blkandcrc_decoded):
                        failed_count += 1
            
                bler_result.append(failed_count/total_count) #add bler value
                print("finish test {}, snr_db={}, bler={:2.5f},elpased time: {:6.6f}".format(test_flag, snr_db,failed_count/total_count,time.time() - start))
                        
            test_results_list.append(bler_result) #test_results_list save bler list for each algo

#dump results to pickle file after simulation for post-processing
if sim_flag == 1:
    sim_config = {'Zc':Zc, 'bgn':bgn }
    with open(filename, 'wb') as handle:
        pickle.dump([sim_config, test_config_list,test_results_list], handle, protocol=pickle.HIGHEST_PROTOCOL)

with open(filename, 'rb') as handle:
    [sim_config, test_config_list,test_results_list] = pickle.load(handle)

sim_ldpc_internal.draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)

pass
