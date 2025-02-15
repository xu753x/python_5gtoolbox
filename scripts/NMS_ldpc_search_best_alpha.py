# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pickle

from scripts.internal import sim_ldpc_internal

""" the script is to search best alpha value for normalized min-sum LDPC decoder
"""

#5G LDPC config, Zc and bgn
Zc_list = [8, 12 ,28, 40, 72, 176, 208,384]  # Z value in 38.211 Table 5.3.2-1: Sets of LDPC lifting size Z
bgn_list =[1, 2]  #bgn in [1,2]
crcpoly = '24A'  #default value, no need change in the simulation

#LDPC decoder config
algo_list = [ 'NMS']

search_alpha_list = [0.1,0.3,0.5,0.7,0.9] #used for NMS only

L_list = [32] #ldpc decoder iteration number

#simulation config
snr_db_list = [-0.5]

filename_pre = "out/NMS_search_alpha_" #test result save to this file
figfile_pre = "out/NMS_search_alpha_"     #plt draw figure saveto this file

sim_flag = 1  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis

########################## main function ############################
beta_list = []  #used for OMS only
mixed_list = [] #used for mixed-min-sum, provide [alpha,beta] pair
for Zc in Zc_list:
    for bgn in bgn_list:
        filename = filename_pre + "ZC{}_bgn{}.pickle".format(Zc, bgn)
        figfile = figfile_pre + "ZC{}_bgn{}.png".format(Zc, bgn)
        if sim_flag == 1:
            sim_ldpc_internal.run_ldpc_simulation(Zc, bgn, crcpoly, algo_list,search_alpha_list,beta_list,mixed_list,
                        L_list, snr_db_list,filename)
        with open(filename, 'rb') as handle:
            [sim_config, test_config_list,test_results_list] = pickle.load(handle)

        sim_ldpc_internal.draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)

pass