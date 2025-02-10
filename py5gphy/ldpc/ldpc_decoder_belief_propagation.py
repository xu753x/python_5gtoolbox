# -*- coding:utf-8 -*-
import numpy as np
import time
import math

def ldpc_decoder_BP(LLRin, H, L):
    """Belief Prapagation(or sum product) algorithm
    https://www.mathworks.com/help/5g/ref/nrldpcdecode.html
    input:
            LLRin: N length LDPC decoder LLR input data
            H: M*N parity check matrix
            L: maximum iterations
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
            sel_Lq = np.tanh(Lq[m,A[m]]/2)
            sel_Lq[sel_Lq==0] = 10**(-12)  #set 0 to a smallest value to avoid below divid by 0
            tmp = np.prod(sel_Lq)
            for idx, n in enumerate(A[m]):
                #tmp2 = np.prod(sel_Lq[0:idx]) * np.prod(sel_Lq[idx+1:])
                tmp2 = tmp/sel_Lq[idx]
                if tmp2 >= 1:
                    Lr[m,n] = 2 * 19.07 #atanh(1) = infinite, set 19.07 as maximum value
                elif tmp2 <= -1:
                    Lr[m,n] = -2 * 19.07 #atanh(-1) = negative infinite, set 19.07 as maximum value
                else:
                    Lr[m,n] = 2 * np.arctanh(tmp2)
        
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
    max_count = 200
    
    H, K, Zc = ldpc_info.gen_ldpc_para(N, bgn)
    
    snr_range = np.arange(-2, 3, 0.5).tolist()  
        
    for snr_db in snr_range:
        failed_count = 0
        false_count = 0 # ldpc decoder status = True, but bit sequence can not match
        start = time.time()
        for m in range(max_count):
            dn, LLRin = nr_ldpc_decode.for_test_ldpc_encoder(K, H, snr_db)
            dn_decoded, status = ldpc_decoder_BP(LLRin, H, L)
            if not np.array_equal(dn,dn_decoded):
                failed_count += 1
                if status == True:
                    false_count += 1

        print("elpased time: {:6.6f}".format(time.time() - start))
        print("BP,N={},snr={} L= {},BLER={:3.2f}%,false_count = {:3.6f}%".format(N, snr_db, L, failed_count/max_count*100,false_count/max_count*100))    

    pass