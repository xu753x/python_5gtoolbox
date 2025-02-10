    
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
            if (not (alpha == 1)) or (not (beta == 0)):
                continue
        
        if algo == "min-sum":
            set_label = "{},alpha={},beta={},L={}}".format(algo, alpha, beta, L)
        else:
            set_label = "{},L={}}".format(algo, L)

        xd = [snr for snr, bler in test_results_list[idx]]
        yd = [bler for snr, bler in test_results_list[idx]]
        plt.plot(xd, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)

    plt.legend(loc="upper right",fontsize=5)
    plt.savefig("ldpc_decoder_mp.png") #plt.show() didn't work if remotely accessing linux platform, save to picture
    plt.show()  #the cmd show plot for windows platform