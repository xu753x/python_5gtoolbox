# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pickle

from scripts.internal import sim_ldpc_internal

""" the script is to search best [alpha,beta] pair value for mixed min-sum LDPC decoder
"""

#5G LDPC config, Zc and bgn
#Zc_list = [12 ,28, 40, 72, 176, 208,384]  # Z value in 38.211 Table 5.3.2-1: Sets of LDPC lifting size Z
Zc_list = [12 ,28]
bgn_list =[1, 2]  #bgn in [1,2]
crcpoly = '24A'  #default value, no need change in the simulation

#LDPC decoder config
algo_list = [ 'mixed-MS']

#this mixed [alpha,beta]pair candidate should come from NMS and OMS search result, 
# choose best 3 alpha value and 3 best beta values to generate [alpha,beta] candidate
search_mixed_list = [[0.7,0.5],[0.7,0.3],[0.5,0.5],[0.8,0.3]] #provide [alpha,beta] pair

L_list = [32] #ldpc decoder iteration number

#simulation config
snr_db_list = [-1, -0.5]

filename_pre = "out/mixed_MS_search_pair_" #test result save to this file
figfile_pre = "out/mixed_MS_search_pair_"     #plt draw figure saveto this file

sim_flag = 1  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis

########################## main function ############################
alpha_list = []  #used for OMS only
beta_list = [] #used for mixed-min-sum, provide [alpha,beta] pair
for Zc in Zc_list:
    for bgn in bgn_list:
        filename = filename_pre + "ZC{}_bgn{}.pickle".format(Zc, bgn)
        figfile = figfile_pre + "ZC{}_bgn{}.png".format(Zc, bgn)
        if sim_flag == 1:
            sim_ldpc_internal.run_ldpc_simulation(Zc, bgn, crcpoly, algo_list,alpha_list,beta_list,search_mixed_list,
                        L_list, snr_db_list,filename)
        with open(filename, 'rb') as handle:
            [sim_config, test_config_list,test_results_list] = pickle.load(handle)

        sim_ldpc_internal.draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)

pass