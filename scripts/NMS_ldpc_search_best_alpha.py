# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pickle

from scripts.internal import sim_ldpc_internal
from py5gphy.ldpc import ldpc_info

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

sim_flag = 0  #if 1, start LDPC dsimulation, if 0, no simulation, read from filename and does test result analysis

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
        #add analysis
        if bgn == 1:
            N = Zc * 66
            K = Zc * 22
        else:
            N = Zc * 50
            K = Zc * 10
    
        #step 1: Find the set with index iLS in Table 5.3.2-1 which contains Zc
        iLS = ldpc_info.find_iLS(Zc)
    
        #step 2 : get H
        H = ldpc_info.getH(Zc, bgn, iLS)
        M = H.shape[0]
        N = H.shape[1]
        line_weight=[0]*M
        for m in range(M):
            idxlist = list(np.where(H[m,:] == 1)[0])
            line_weight[m] = len(idxlist)
        v1 = [Zc,bgn,N, max(line_weight), min(line_weight),test_results_list[0][0],test_results_list[1][0],test_results_list[2][0],test_results_list[3][0],test_results_list[4][0]]
        print(v1)
        pass

pass