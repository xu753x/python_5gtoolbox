# -*- coding:utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import time
import pickle

from py5gphy.ldpc import nr_ldpc_decode

def run_ldpc_simulation(Zc, bgn, crcpoly, algo_list,alpha_list,beta_list,mixed_list,L_list,
                        snr_db_list,filename):
    """ run ldpc simulation
    """
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
                    test_count = 0
                    failed_count = 0
                
                    while 1:
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
                        test_count += 1
                        
                        #terminate check
                        #if (test_count >= max_count) or (failed_count >= failed_limit):
                        test_limit_list = [200,400,800,2000] 
                        if test_count in test_limit_list:
                            if (test_count == test_limit_list[0]) and (failed_count >= 10):
                                break
                            if (test_count == test_limit_list[1]) and (failed_count >= 5):
                                break
                            if (test_count == test_limit_list[2]) and (failed_count >= 2):
                                break
                            if (test_count == test_limit_list[3]):
                                break
                    
                    #save test result
                    bler = failed_count/test_count
                    bler_result.append(bler) #add bler value
                    print("finish test {}, Zc {}, bgn{},snr_db={}, bler={:2.5f},elpased time: {:6.2f}".format(test_flag, Zc, bgn,snr_db,bler,time.time() - start))
                            
                test_results_list.append(bler_result) #test_results_list save bler list for each algo
    
    #dump results to pickle file after simulation for post-processing

    sim_config = {'Zc':Zc, 'bgn':bgn }
    with open(filename, 'wb') as handle:
        pickle.dump([sim_config, test_config_list,test_results_list], handle, protocol=pickle.HIGHEST_PROTOCOL)

def draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile):
    #test is done, draw the picture
    fig = plt.figure()
    marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
    marker_count = 0
    plt.xlabel("Eb/N0")
    plt.ylabel("BLER")
    plt.title("ldpc decoder, Zc={}, bgn={}".format(sim_config['Zc'],sim_config['bgn']))
    plt.yscale("log")
    plt.xlim(snr_db_list[0],snr_db_list[-1])
    plt.ylim(10**(-4),1)
    plt.grid(True)

    for idx, testcfg in enumerate(test_config_list):
        
        set_label = "{}".format(testcfg)
        
        yd = test_results_list[idx]
        plt.plot(snr_db_list, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)

    plt.legend(loc="upper right",fontsize=5)
    plt.savefig(figfile) #plt.show() didn't work if remotely accessing linux platform, save to picture
    plt.close(fig)
    plt.pause(0.01)
