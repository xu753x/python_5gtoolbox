# -*- coding:utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import xlwt

import time
import pickle

from py5gphy.polar import nr_polar_decoder

def run_polar_simulation(testcase_list,algo_list,L_list,snr_db_list,filename):
    """ polar simulation"""
    test_results_list = []
    for testcase in testcase_list:
        K = testcase[0]
        N = testcase[1]; E=N
        nMax = testcase[2]
        iIL = testcase[3]
        CRCLEN = testcase[4]
        padCRC = testcase[5]
        rnti = testcase[6]   
    
        for algo in algo_list:
            if algo in ['SC','SC_optionB']:
                tmp_L_list = [1] #
            else:
                tmp_L_list = L_list
            
            for L in tmp_L_list:
                test_result = [[algo, L, testcase]] #first value is test related information
                
                for snr_db in snr_db_list:
                    start = time.time()
                    test_count = 0
                    failed_count = 0
                    while 1:
                        #run polar test with encoder and decoder
                        LLRin, encodedbits, blkandcrc = nr_polar_decoder.for_test_5g_polar_encoder(K, E, nMax, iIL,snr_db,CRCLEN,padCRC,rnti)
                        decbits, status = nr_polar_decoder.nr_decode_polar(algo,LLRin, E, blkandcrc.size, L, nMax, iIL, CRCLEN, padCRC, rnti)
                        
                        #check decoder result
                        #print('done  decoder={},L={},snr={},count={}'.format(decoder,L,snr_db,count))
                        if not np.array_equal(decbits, blkandcrc):
                            failed_count += 1
                        test_count += 1
                        
                        #terminate judge
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
                    test_result.append([snr_db, bler])
                    print("decoder={},K={},N={},L={},snr={},test_count={},failed_count={},bler={:2.5f}, elpased time: {:6.6f}".\
                              format(algo,K,N,L,snr_db,test_count,failed_count,bler,time.time() - start))
            
                test_results_list.append(test_result)

    with open(filename, 'wb') as handle:
        pickle.dump([testcase_list,snr_db_list, test_results_list], handle, protocol=pickle.HIGHEST_PROTOCOL)

def draw_polar_decoder_result(testcase_list, snr_db_list, test_results_list, figfile):
    #draw the plot
    fig = plt.figure()
    marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
    marker_count = 0
    plt.xlabel("Eb/N0")
    plt.ylabel("BLER")
    
    if len(testcase_list) == 1:
        K = testcase_list[0][0]
        N = testcase_list[0][1]
        plt.title("polar decoder, N={}, K={}".format(N,K))
    else:
        plt.title("polar decoder")
    plt.yscale("log")
    plt.xlim(snr_db_list[0],snr_db_list[-1])
    plt.ylim(10**(-4),1)
    plt.grid(True)

    for test in test_results_list:
        if len(testcase_list) == 1:
            set_label = "{},L={}".format(test[0][0],test[0][1])
        else:
            set_label = "{},L={},K={},N={}".format(test[0][0],test[0][1],test[0][2][0],test[0][2][1])
        xd = [x1 for x1,y1 in test[1:]]
        yd = [y1 for x1,y1 in test[1:]]
        plt.plot(xd, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)
	
    plt.legend(loc="upper right",fontsize=5)
    plt.savefig(figfile)
    plt.close(fig)
    plt.pause(0.01)

def to_excel_polar_decoder_result(testcase_list, snr_db_list, test_results_list, excelfile):