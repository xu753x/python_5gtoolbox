# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time
import os
import pickle

from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import nr_ldpc_decode

def gen_pool_list():
    """ generate testlist for pool mapping
    """
    #algo_list = ["BF", "BP", "min-sum"]
    algo_list = ["BF"]

    #for min-sum
    #alpha_range = [0.1,0.3,0.5,0.7,0.9,1]
    alpha_range = [1, 0.8, 0.5, 0.3]
    #beta_range = [0, 0.2, 0.4, 0.6, 1, 2]
    beta_range = [0, 0.3, 0.6, 1, 2]

    L_list = [16,32,64] #max itererate size
    
    #snr_range = np.arange(-1, 1.2, 0.2).tolist()
    snr_range = np.arange(2, 6, 0.5).tolist()

    N = 660
    bgn = 1

    H, K, Zc = ldpc_info.gen_ldpc_para(N, bgn)
    M = H.shape[0]

    #gen testcases
    testlist = []
    for algo in algo_list:
        if algo in ["BF"]:
            for L in L_list:
                for snr in snr_range:
                    tmp = 200
                    if snr < 3.5:
                        max_count = tmp
                    elif snr < 5:
                        max_count = tmp*5
                    else:
                        max_count = tmp*10
                    testlist.append([H, K, Zc, algo, 1, 0, L, snr, max_count])
        elif algo in ["BP"]:
            for L in L_list:
                for snr in snr_range:
                    tmp = 200
                    if snr < 0:
                        max_count = tmp
                    else:
                        max_count = tmp*5
                    testlist.append([H, K, Zc, algo, 1, 0, L, snr, max_count])
        else:
            #first add beta=0 only
            beta = 0
            for alpha in alpha_range:
                for L in L_list:
                    for snr in snr_range:
                        tmp = 200
                        if snr < 0:
                            max_count = tmp
                        else:
                            max_count = tmp*5
                        testlist.append([H, K, Zc, algo, alpha, beta, L, snr, max_count])
            
            #first add alpha=1 only
            alpha = 1
            for beta in beta_range[1:]:
                for L in L_list:
                    for snr in snr_range:
                        tmp = 200
                        if snr < 0:
                            max_count = tmp
                        else:
                            max_count = tmp*5
                        testlist.append([H, K, Zc, algo, alpha, beta, L, snr, max_count])

    return testlist, snr_range, N, M

def verify_ldpc_decoder(H, K, Zc, algo, alpha, beta, L, snr, max_count):
    if algo in ["BF", "BP"]:
        print("process pid is {}, algo={}, L={},snr={}".format(os.getpid(), algo, L, snr))
    else:
        print("process pid is {}, algo={}, alpha={}, bets={},L={},snr={}".format(os.getpid(), algo, alpha, beta,L, snr))
    
    #main code
    failed_count = 0
    for count in range(max_count):
        dn, LLRin = nr_ldpc_decode.for_test_ldpc_encoder(K, H, snr)
        dn_decoded, status = nr_ldpc_decode.decode_ldpc(LLRin, H, L, algo, alpha, beta)
        if not np.array_equal(dn,dn_decoded):
            failed_count += 1

    if algo in ["BF", "BP"]:
        print("done process pid is {}, algo={}, L={},snr={},bler={:3.2f}%".format(os.getpid(), algo, L, snr,failed_count/max_count*100))
    else:
        print("done process pid is {}, algo={}, alpha={}, bets={},L={},snr={},bler={:3.2f}%".format(os.getpid(), algo, alpha, beta,L, snr,failed_count/max_count*100))
    return [[H, K, Zc, algo, alpha, beta, L, snr, max_count], failed_count]


if __name__ == '__main__':
    testlist, snr_range, N, M = gen_pool_list()

    test_config_list = []
    test_results_list = []
    filename = 'ldpc_decoder_bf.pickle'
    if 1:
    #    for testcase in testlist:
    #        start = time.time()
                             #H, K, Zc, algo, alpha, beta, L, snr, max_count)
    #        result = verify_ldpc_decoder( testcase[0],testcase[1],testcase[2], #H, K, Zc
    #                                     testcase[3],testcase[4],testcase[5], #algo, alpha, beta
    #                                     testcase[6],testcase[7],testcase[8], #L, snr, max_count
    #                                )
        with Pool(4) as p:
          for result in p.starmap(verify_ldpc_decoder, testlist):                                     
            algo = result[0][3]
            alpha = result[0][4]
            beta =result[0][5]
            L = result[0][6]
            snr = result[0][7]
            max_count = result[0][8]
            failed_count = result[1]

            bler = failed_count/max_count

            test_cfg = [algo, alpha, beta, L]

            #add test_cfg to test_config_list and add init test_result to test_results_list
            if test_cfg not in test_config_list:
                test_config_list.append(test_cfg)
                test_result = [[snr,0] for snr in snr_range]
                test_results_list.append(test_result)
            
            #add test result into correspondent test_results_list
            idx = test_config_list.index(test_cfg)
            test_result = test_results_list[idx]

            for i ,value in  enumerate(test_result):
                if value[0] == snr:
                    sub_idx = i
                    break

            test_result[sub_idx][1] =bler
            
    #        print("ldpc decoder elpased time: {:6.6f}".format(time.time() - start))

        #dump results to pickle file for post-processing
        with open(filename, 'wb') as handle:
            pickle.dump([test_config_list,test_results_list], handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open(filename, 'rb') as handle:
        [test_config_list,test_results_list] = pickle.load(handle)

    #test is done, draw the picture
    marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
    marker_count = 0
    plt.xlabel("Eb/N0")
    plt.ylabel("BLER")
    plt.title("ldpc decoder, N={}, M={}".format(N,M))
    plt.yscale("log")
    plt.xlim(snr_range[0]-0.5,snr_range[-1]+0.5)
    plt.ylim(10**(-4),1)
    plt.grid(True)

    for idx, testcfg in enumerate(test_config_list):
        algo = testcfg[0]
        alpha = testcfg[1]
        beta = testcfg[2]
        L = testcfg[3]

        #for min-sum, plot only normalized(beta =0) or offset(alpha=1)
        
        if algo == "min-sum":
            set_label = "{},alpha={},beta={},L={}".format(algo, alpha, beta, L)
        else:
            set_label = "{},L={}".format(algo, L)

        xd = [snr for snr, bler in test_results_list[idx]]
        yd = [bler for snr, bler in test_results_list[idx]]
        plt.plot(xd, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)

    plt.legend(loc="upper right",fontsize=5)
    plt.savefig("ldpc_decoder_bf.png") #plt.show() didn't work if remotely accessing linux platform, save to picture
    plt.ion()
    plt.show(block=False)  #the cmd show plot for windows platform
    plt.pause(0.01)
    

    pass