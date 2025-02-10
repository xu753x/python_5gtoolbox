# -*- coding:utf-8 -*-
import numpy as np
import time
import math

def ldpc_decoder_min_sum(LLRin, H, L, alpha=1, beta=0):
    """min sum algorithm
    https://www.mathworks.com/help/5g/ref/nrldpcdecode.html
    input:
            LLRin: N length LDPC decoder LLR input data
            H: M*N parity check matrix
            L: maximum iterations
            alpha: (0:1] used for normalized min-sum decoding, 1: no normalized
            beta: used for offset min-sum decoding.  0: no offset
        output:
            ck: N size of decoded bits, 
            status: True or False
    """

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
        ck[LQ > 0] = 0
        ck[LQ <= 0] = 1

        #parity check first
        S = (H @ ck.T) % 2    
        if not np.any(S): 
            #if S is all zero sequence, decoding success, return Tue
            return ck, True

        #variable nodes to checking nodes update
        for m in range(M):
            sel_Lq = Lq[m,A[m]]
            sign_prod = np.prod(np.sign(sel_Lq))
            sorted_abs_v = np.sort(np.abs(sel_Lq))

            first_min = sorted_abs_v[0]
            second_min = sorted_abs_v[1]
            for idx, n in enumerate(A[m]):
                if np.abs(sel_Lq[idx]) == first_min:
                    minv = second_min
                else:
                    minv = first_min
                
                sel_minv = max(minv-beta, 0) #offset min-sum
                
                Lr[m,n] = alpha * sign_prod * np.sign(sel_Lq[idx]) * sel_minv
                        
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



if __name__ == "__main__":
    from py5gphy.crc import crc
    from py5gphy.ldpc import nr_ldpc_encode
    from py5gphy.ldpc import ldpc_info
    from py5gphy.ldpc import nr_ldpc_decode
    import time

    #choose 5G LDPC parameters, test pure LDPC decoder
    L = 32
    N = 660
    bgn = 1
    max_count = 20
    alpha_range = [0.1,0.3,0.5,0.7,0.9,1]
    beta_range = [0, 0.2, 0.4, 0.6, 1, 2]
    H, K, Zc = ldpc_info.gen_ldpc_para(N, bgn)
    
    snr_range = np.arange(-1, 1, 0.2).tolist()  
        
    for snr_db in snr_range:
        for alpha in alpha_range:
            for beta in beta_range:
                failed_count = 0
                start = time.time()
                for m in range(max_count):
                    dn, LLRin = nr_ldpc_decode.for_test_ldpc_encoder(K, H, snr_db)
                    dn_decoded, status = ldpc_decoder_min_sum(LLRin, H, L, alpha, beta)
                    if not np.array_equal(dn,dn_decoded):
                        failed_count += 1
                
                print("elpased time: {:6.6f}".format(time.time() - start))
                print("min-sum,N={},snr={},alpha={},beta={} L= {}, BLER={:3.2f}%".format(N,snr_db, alpha, beta, L, failed_count/max_count*100))
    

    pass