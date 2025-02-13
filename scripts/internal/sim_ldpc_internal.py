# -*- coding:utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

def draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile):
    #test is done, draw the picture
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
    plt.pause(0.01)
