# -*- coding:utf-8 -*-
import numpy as np
import scipy as sp
import time

from py5gphy.ldpc import ldpc_info
from py5gphy.ldpc import ldpc_decoder_bit_flipping
from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_encode

def decode_ldpc(LLRin, H, L, algo='min-sum', alpha=1, beta=0):
    """ LDPC decoder, support BF(bit flipping), BP(belief propagation), min-sum algorithms
    BP is also named sum-product algorithm
    input: 
        LLRin: N length LDPC decoder LLR input data
        H: LDPC matrix, 
        L: iteration size
        algo: one of ["BF", "BP", "min-sum"]
        alpha: (0:1] used for normalized min-sum. 1 means no normalized
        beta: >=0 used for offset min-sum, 0 means no offset
    output:
        ck: N length LDPC decoded sequence
        status: True or False
    """     
    if algo == "BF":
        ck, status = ldpc_decoder_bit_flipping.ldpc_decoder_BF(LLRin, H, L)
        return ck, status
    
    #for soft decision decoder
    M = H.shape[0]
    N = H.shape[1]
    
    #validate
    assert LLRin.size == N

    #generate A list and B list
    # A list contain sublist of all variable nodes index that connect to check node j
    # correspondent to each line of H
    #for examnple, A[0] is a list of variable nodes index that connect to check node 0
    A=[]
    for m in range(M):
        idxlist = list(np.where(H[m,:] == 1)[0])
        A.append(idxlist)
    
    # B list contain sublist of all check nodes index that connect to variable node i
    # correspondent to each column of H
    #for examnple, B[1] is a list of check nodes index that connect to variable node 1
    B=[]
    for n in range(N):
        idxlist = list(np.where(H[:,n] == 1)[0])
        B.append(idxlist)
    
    #init Lq, LQ, Lr
    LQ = LLRin #decoded variable bits LLR

    #Variable nodes to checking nodes LLR, Lq[m,n] = 0 if H[m,n]=0
    #m is check node index, n is variable index, 
    Lq = H*LLRin  
    
    #checking nodes to variable nodes, Lr[i,j] = 0 if H[i,j]=0
    Lr = np.zeros((M,N)) 
    
    ck = np.zeros(N,'i1') #hard coded bits

    for iter in range(L):
        #LQ to ck hard coded bit
        ck[LQ >= 0] = 0
        ck[LQ < 0] = 1

        #parity check first
        S = (H @ ck.T) % 2    
        if not np.any(S): 
            #if S is all zero sequence, decoding success, return Tue
            return ck, True

        #variable nodes to checking nodes update
        for m in range(M):
            sel_Lq = Lq[m,A[m]]
            
            if algo == 'BP':
                Lr = _BP_process(sel_Lq, A, Lr,m)
            else:
                Lr = _min_sum_process(sel_Lq, A, Lr,m, alpha, beta)
        
        #update LQ
        LQ = LLRin + Lr.sum(axis=0)

        #update Lq
        for n in range(N):
            for m in B[n]:
                Lq[m,n] = LQ[n] - Lr[m,n]
    
    #LQ to ck hard coded bit
    ck[LQ > 0] = 0
    ck[LQ <= 0] = 1

    #parity check
    S = (H @ ck.T) % 2    
    if not np.any(S): 
        #if S is all zero sequence, decoding success, return Tue
        return ck, True
    else:
        return ck, False

def _BP_process(sel_Lq, A, Lr,m):
    #calculate Lr with BP processing
    
    zero_value_list = list(np.where(sel_Lq==0)[0])
    
    if len(zero_value_list) == 0:
        #normal case, no zero value
        tanh_Lq = np.tanh(sel_Lq/2)
        #tanh_Lq[tanh_Lq==0] = 10**(-22)
        prod_v = np.prod(tanh_Lq)
        for idx, n in enumerate(A[m]):
            #tmp2 = np.prod(sel_Lq[0:idx]) * np.prod(sel_Lq[idx+1:])
            tmp2 = prod_v/tanh_Lq[idx]
            if tmp2 >= 1:
                Lr[m,n] = 2 * 19.07 #atanh(1) = infinite, set 19.07 as maximum value
            elif tmp2 <= -1:
                Lr[m,n] = -2 * 19.07 #atanh(-1) = negative infinite, set 19.07 as maximum value
            else:
                Lr[m,n] = 2 * np.arctanh(tmp2)
    elif len(zero_value_list) == 1:
        tanh_Lq = np.tanh(sel_Lq/2)
        #only one zero value, only zero value related Lr is non-zero
        for idx, n in enumerate(A[m]):
            Lr[m,n] = 0
        zero_idx = zero_value_list[0]
        Lr[m,A[m][zero_idx]] = np.prod(tanh_Lq[0:zero_idx]) * np.prod(tanh_Lq[zero_idx+1:])
    else:
        #>=2 zero values. all Lr are zero
        for idx, n in enumerate(A[m]):
            Lr[m,n] = 0
    
    return Lr

def _min_sum_process(sel_Lq, A, Lr,m, alpha, beta):
    """ mixed min-sim processing
    alpha = 1, beta =0: min-sum
    alpha < 1, beta = 0: normalized min-sum
    alpha = 1, beta >0: offset min-sum
    alpha <1, beta >0: mixed min-sum
    """
    
    zero_value_list = list(np.where(sel_Lq==0)[0])
    
    if len(zero_value_list) == 0:
        #normal case, no zero value
        sign_prod = np.prod(np.sign(sel_Lq))
        sorted_abs_v = np.sort(np.abs(sel_Lq))

        first_min = sorted_abs_v[0]
        second_min = sorted_abs_v[1]
        for idx, n in enumerate(A[m]):
            if np.abs(sel_Lq[idx]) == first_min:
                minv = second_min
            else:
                minv = first_min
                
            sel_minv = max(minv - beta, 0) #offset min-sum  
            Lr[m,n] = alpha * sign_prod * np.sign(sel_Lq[idx]) * sel_minv
    elif len(zero_value_list) == 1:
        #only one zero value, only zero value related Lr is non-zero
        for idx, n in enumerate(A[m]):
            Lr[m,n] = 0
        
        zero_idx = zero_value_list[0]
        
        if zero_idx == 0:
            sign_prod = np.prod(np.sign(sel_Lq[1:]))
            min_v = np.min(np.abs(sel_Lq[1:]))
        else:
            sign_prod = np.prod(np.sign(sel_Lq[0:zero_idx]))*np.prod(np.sign(sel_Lq[zero_idx+1:]))
            min_v = min(np.min(np.abs(sel_Lq[0:zero_idx])),np.min(np.abs(sel_Lq[zero_idx+1:])))
        
        sel_minv = max(min_v - beta, 0) #offset min-sum  
        Lr[m,A[m][zero_idx]] = alpha * sign_prod *sel_minv 
    else:
        #>=2 zero values. all Lr are zero
        for idx, n in enumerate(A[m]):
            Lr[m,n] = 0
    
    return Lr

def nr_decode_ldpc(LLRin, Zc, bgn, L, algo='min-sum',alpha=1, beta=0):
    """ LDPC decode following to TS38.212 5.3.2
    ck = encode_ldpc(dn, bgn)
    input: 
        LLRin: N length LDPC decoder LLR input data
        bgn: base graph value 1 or 2
        crcpoly: one of ['24A','24B','16']
        algo: ldpc decoder algorithm
    output:
        ck: K length LDPC decoded sequence
    
    """
    assert bgn in [1,2]
    assert algo in ['BF', 'BP', 'min-sum']
    
    if bgn == 1:
        N = Zc * 66
        K = Zc * 22
    else:
        N = Zc * 50
        K = Zc * 10
    
    assert N == LLRin.size
    
    #step 1: Find the set with index iLS in Table 5.3.2-1 which contains Zc
    iLS = ldpc_info.find_iLS(Zc)
    assert iLS < 8

    #step 2 : get H
    H = ldpc_info.getH(Zc, bgn, iLS)

    #add ounctured 2*Zc information bits to get full ldpc decoder input
    newLLRin = np.concatenate([np.zeros(2*Zc), LLRin])

    ck, status =  decode_ldpc(newLLRin, H, L, algo, alpha, beta)

    blkandcrc = ck[0:K]
    
    return blkandcrc, ck, status

def for_test_ldpc_encoder(K, H, snr_db):
    ck = np.random.randint(2, size=K)
    #ldpc encoder to get parity bits
    Hrowsize = H.shape[0]
    Hcolsize = H.shape[1]
    H1 = H[:,0:Hcolsize-Hrowsize]
    H2 = H[:,Hcolsize-Hrowsize:Hcolsize]

    L1 = -H1 @ ck.T  #matrix multiply
    outd = np.linalg.solve(H2, L1) #outd = H2\L1;
    wn = np.round(outd) % 2
    wn = wn.astype('i1')

    dn = np.concatenate((ck, wn))

    en = 1 - 2*dn #BPSK modulation, 0 -> 1, 1 -> -1
    fn = en + np.random.normal(0, 10**(-snr_db/20), dn.size) #add noise
    
    #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
    noise_power = 10**(-snr_db/10)
    LLRin = 2*fn/noise_power

    return dn, LLRin

def for_test_5g_ldpc_encoder(Zc, bgn, snr_db,crcpoly='24A'):
    """ generate 5G LLRin for LDPC decoder test using BPSK modulation
    """
    assert bgn in [1, 2]
    assert crcpoly in ['24A', '24B', '16']
    if bgn == 1:
        K = Zc * 22
        N = Zc * 66
    else:
        K = Zc * 10
        N = Zc * 50

    if crcpoly in ['24A', '24B']:
        crc_len = 24
    else:
        crc_len = 16

    #generate input bit
    inbits = np.random.randint(2, size = K-crc_len)
    blkandcrc = crc.nr_crc_encode(inbits, crcpoly)
    dn = nr_ldpc_encode.encode_ldpc(blkandcrc, bgn)      

    #LLR generation
    en = 1 - 2*dn #BPSK modulation, 0 -> 1, 1 -> -1
    fn = en + np.random.normal(0, 10**(-snr_db/20), dn.size) #add noise
    
    #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
    noise_power = 10**(-snr_db/10)
    LLRin = 2*fn/noise_power
    

    return blkandcrc, dn, LLRin

if __name__ == "__main__":
    from scipy import io
    import os
    from py5gphy.crc import crc
    from py5gphy.ldpc import nr_ldpc_encode
    import pickle
    import matplotlib.pyplot as plt

    Zc = 10
    bgn = 1
    crcpoly = '24A'
    L = 32
    
    #algo_list = ['BF', 'BP', 'min-sum', 'NMS', 'OMS']
    #algo_list = [ 'BP', 'min-sum', 'NMS', 'OMS']
    #algo_list = [ 'NMS', 'OMS']
    algo_list = ['min-sum']
    #algo_list = ['BP']
    alpha_list = [0.8, 0.5]
    beta_list = [0.3, 0.1]
    snr_db_list = np.arange(-1, 1.5, 0.5).tolist()
    #snr_db_list = np.arange(-1, 1.2, 0.3).tolist()

    filename = "out/ldpc_decode_result_all.pickle"
    figfile = "out/ldpc_decode_result_all.png"

    sim_flag = 1
    
    if sim_flag == 0:
        algo_list = [] #disable long time LDPC encoder/.decoder

    test_results_list = []
    test_config_list = []
    for algo in algo_list:
        if algo in ['BP', 'BF','min-sum']:
            test_num = 1
        elif algo == 'NMS':
            test_num = len(algo_list)
        else:
            test_num = len(beta_list)
        
        for test_idx in range(test_num):
            #add to test_result
            if algo in ['BF', 'BP', 'min-sum']:
                test_flag = algo
            elif algo == 'NMS':
                test_flag = 'NMS-alpha={}'.format(alpha_list[test_idx])
            else:
                test_flag = 'OMS-beta={}'.format(beta_list[test_idx])
            
            test_config_list.append([test_flag, L])

            bler_result = []
            for snr_db in snr_db_list:
                start = time.time()
                tmp_count = 400
                if snr_db < 0:
                    total_count = tmp_count
                else:
                    total_count = tmp_count * 10
                
                failed_count = 0
                for _ in range(total_count):
                    blkandcrc, dn, LLRin = for_test_5g_ldpc_encoder(Zc, bgn, snr_db, crcpoly)
                    if algo in ['BF', 'BP', 'min-sum']:
                        blkandcrc_decoded, ck_decoded, status = nr_decode_ldpc(LLRin, Zc, bgn, L, algo,alpha=1, beta=0)
                    elif algo == 'NMS':
                        blkandcrc_decoded, ck_decoded, status = nr_decode_ldpc(LLRin, Zc, bgn, L, 'min-sum',alpha=alpha_list[test_idx], beta=0)
                    else:
                        blkandcrc_decoded, ck_decoded, status = nr_decode_ldpc(LLRin, Zc, bgn, L, 'min-sum',alpha=1, beta=beta_list[test_idx])
                    
                    #check result
                    if not np.array_equal(blkandcrc, blkandcrc_decoded):
                        failed_count += 1
                
                bler_result.append(failed_count/total_count)
                print("finish test {}, snr_db={}, bler={:2.5f},elpased time: {:6.6f}".format(test_flag, snr_db,failed_count/total_count,time.time() - start))
                            
            test_results_list.append(bler_result)

    #dump results to pickle file for post-processing
    if sim_flag == 1:
        sim_config = {'Zc':Zc, 'bgn':bgn }
        with open(filename, 'wb') as handle:
            pickle.dump([sim_config, test_config_list,test_results_list], handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    with open(filename, 'rb') as handle:
        [sim_config, test_config_list,test_results_list] = pickle.load(handle)
    
    draw_ldpc_decoder_result(snr_db_list, sim_config, test_config_list, test_results_list, figfile)

    curpath = "tests/ldpc/testvectors"
    for f in os.listdir(curpath):
            if f.endswith(".mat") and f.startswith("ldpc_encode_testvec"):
                print("LDPC decode testvector: " + f)
                matfile = io.loadmat(curpath + '/' + f)
                #read data from mat file
                ck_ref = matfile['in'][0]
                dn = matfile['dn'][0]
                Zc = matfile['Zc'][0][0]
                bgn = matfile['bgn'][0][0]
                
                start = time.time()
                ck = decode_ldpc(dn, bgn)
                print("decode_ldpc elpased time: {:6.2f}".format(time.time() - start))

                assert np.array_equal(ck, ck_ref)


    pass