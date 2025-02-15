# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pickle

from scripts.internal import sim_ldpc_internal

"""the script is used to simulate soft-decision LDPC decoder performance
it support [ 'BP', 'min-sum', 'NMS', 'OMS', 'mixed-min-sum] algorithms
'BP: 'belief propagation' or 'sum-product' in other name
'min-sum': 'min-sum'
'NMS': normalized min-sum with alpha in (0,1) and beta = 0
'OMS': offset min-sum, with alpha = 1 and beta in (0,1)
'mixed-MS': combination of NMS and OMS, with alpha in (0,1) and beta in (0,1)
"""
########### test 1: test different LDPC decoder algorithm ##################
# test result: mixed-min-sum performance is much close to BP and is better than other min-sum algorithms
#attn: this is just for Zc=10 and bgn=1 LDPC config, different LDPC config may have differnt result

#5G LDPC config, Zc and bgn
Zc = 10  # Z value in 38.211 Table 5.3.2-1: Sets of LDPC lifting size Z
bgn = 1 #bgn in [1,2]
crcpoly = '24A'  #default value, no need change in the simulation

#LDPC decoder config
algo_list = [ 'BP', 'min-sum', 'NMS', 'OMS','mixed-MS']
alpha_list = [0.8, 0.5] #used for NMS only
beta_list = [0.3, 0.1]  #used for OMS only
mixed_list = [[0.8, 0.3]] #used for mixed-min-sum, provide [alpha,beta] pair
L_list = [32] #ldpc decoder iteration number

#simulation config
snr_db_list = np.arange(-1, 1.5, 0.5).tolist()

#failed_limit and max_count is to define termination method of the test
#polar decoder terminate if polar decoder failed count reach failed_limit or test_count reach max_count
failed_limit = 10 
max_count = 10000

filename = "out/ldpc_decode_result_all.pickle" #test result save to this file
figfile = "out/ldpc_decode_result_all.png"     #plt draw figure saveto this file

sim_flag = 1  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis

## main function 
if sim_flag == 1:
    sim_ldpc_internal.run_ldpc_simulation(Zc, bgn, crcpoly, algo_list,alpha_list,beta_list,mixed_list,
                        L_list, snr_db_list,filename, failed_limit, max_count)

with open(filename, 'rb') as handle:
    [sim_config, test_config_list,test_results_list] = pickle.load(handle)
sim_ldpc_internal.draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)


########### test 2: test ldpc decoder iteration number L value performance ##################
# test result: L = 32 and 64 performance are very close and are much better than L=16
#attn: this is just for Zc=10 and bgn=1 LDPC config, different LDPC config may have differnt result

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

#failed_limit and max_count is to define termination method of the test
#polar decoder terminate if polar decoder failed count reach failed_limit or test_count reach max_count
failed_limit = 10 
max_count = 10000

filename = "out/ldpc_decode_result_for_L.pickle" #test result save to this file
figfile = "out/ldpc_decode_result_for_L.png"     #plt draw figure saveto this file

sim_flag = 1  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis

## main function 
if sim_flag == 1:
    sim_ldpc_internal.run_ldpc_simulation(Zc, bgn, crcpoly, algo_list,alpha_list,beta_list,mixed_list,
                        L_list, snr_db_list,filename, failed_limit, max_count)

with open(filename, 'rb') as handle:
    [sim_config, test_config_list,test_results_list] = pickle.load(handle)

sim_ldpc_internal.draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)

pass
