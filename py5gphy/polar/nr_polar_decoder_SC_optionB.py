# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.polar import polar_interleaver
from py5gphy.polar import polar_construct
from py5gphy.polar import polar_path

def nr_decode_polar_SC_optionB(LLRin, E, K, nMax, iIL):
    """ SC polar decoder
    input:
        LLRin: N length input LLR demodulation data
        N: length of input data
        E: rate match length
        K: decoded data length
        (nMax, iIL): (9, 1) apply for DL and (10, 0) apply for UL
        
    output:
        decbits: L length bits

    """
    # validate data
    assert [nMax, iIL] in [[9,1], [10,0]]
    
    #get F array, PC array and other values
    F, qPC, N, nPC, nPCwm = polar_construct.construct(K, E, nMax)
    assert (N <= 2**nMax) and (N >= 2**5) #38.212 5.3.1
    assert LLRin.size == N
        
    decodedbits, status = PolarSCDecoder(LLRin, F, N)
    
    #initial a few tables
    #bit seqeucne ck is used to polar interleaving to get ckbar, ckbar map to u seq at non-frozen location
    #here need get u_seq to ckbar mapping table, 
    ckbar_indices = [idx for idx in range(N) if (F[idx]==0) and (idx not in qPC)]
    
    ckbar = decodedbits[ckbar_indices] #get information bit and CRC bits only, not including pc bits
        
    #de-interleave
    if iIL:
        ck = polar_interleaver.deinterleave(ckbar, K)
    else:
        ck = ckbar    
    return np.array(list(ck), 'i1'), status

def PolarSCDecoder(LLRin, F, N):
    """ polar SC decoder"""
    #main function
    m = int(np.ceil(np.log2(N))) #m = log2(N)
    #Bit-wise reverse LLRin to get layer0 LLR
    LLR0 = np.zeros(N)
    for branch in range(N):
        #path.setLLR(LLRin[branch], 0, branch, 0)
        #bit reverse LLRin
        br=int( '{:0{width}b}'.format(branch, width=m)[::-1],2)
        LLR0[branch] = LLRin[br]
    
    #init path
    #path = polar_path.SC_Path_no_opt(LLR0, N)
    #path = polar_path.SC_Path_opt1(LLR0, N)
    path = polar_path.SC_Path_opt2(LLR0, N)
        
    #SC main loop
    for n in range(N):
        #print("new SC in main func, phase= {}".format(n))
        recursivelyCalcLLR(path,m,0, n)
        if F[n] == 1:  #frozen bit
            path.setB(0, m, 0, n)
            #print("main func B_value set frozen bit,[{}, {}, {}]".format(m, 0, n))
        else:
            LLR = path.getLLR(m,0,n)
            if LLR > 0:
                path.setB(0, m, 0, n)
            else:
                path.setB(1, m, 0, n)
            #print("main func B_value set unfrozen bit,[{}, {}, {}], LLR= {} ".format(m, 0, n, LLR))
            
        if (n%2)==1:
            recursivelyUpdateB(path,m,0,n)

    #get decoded bits
    decodedbits = path.get_u_seq()
    
    return decodedbits, True

def recursivelyUpdateB(path,layer,branch,phase):
    #update path.B: 
    newphase = phase // 2
    
    b1 = path.getB(layer,branch,phase-1)
    b2 = path.getB(layer,branch,phase)
    #print("recursivelyUpdateB B_value get [{}, {}, {}],[{}, {}, {}]".format(layer,branch,phase-1,layer,branch,phase))

    path.setB((b1+b2)%2, layer-1, 2*branch, newphase)
    #print("recursivelyUpdateB B_value set [{}, {}, {}]".format(layer-1, 2*branch, newphase))

    if (newphase % 2):
        recursivelyUpdateB(path,layer-1,2*branch,newphase)
        
    path.setB(b2, layer-1, 2*branch+1, newphase)
    if (newphase % 2):
        recursivelyUpdateB(path,layer-1,2*branch+1,newphase)   

def recursivelyCalcLLR(path,layer, branch,phase):
    if layer == 0:
        return
    newphase = phase // 2
    #print("cal LLR_value [{}, {}, {}],need [{}, {}, {}],[{}, {}, {}]".format(layer, branch,phase,layer-1,2*branch,newphase, layer-1,2*branch+1,newphase))
    
    if (phase % 2) == 0:
        recursivelyCalcLLR(path,layer-1, 2*branch, newphase)
        recursivelyCalcLLR(path,layer-1, 2*branch+1, newphase)
    
    LLR1 = path.getLLR(layer-1, 2*branch, newphase)
    LLR2 = path.getLLR(layer-1, 2*branch+1, newphase)
    #print("recursivelyCalcLLR get LLR_value [{}, {}, {}],[{}, {}, {}]".format(layer-1,2*branch,newphase, layer-1,2*branch+1,newphase))

    if (phase % 2) == 0:
        value = np.sign(LLR1)*np.sign(LLR2)*min(abs(LLR1), abs(LLR2))
        path.setLLR(value, layer, branch, phase)
        #print("recursivelyCalcLLR set LLR_value [{}, {}, {}]".format(layer,branch,phase))
    else:
        B = path.getB(layer,branch,phase-1)
        #print("recursivelyCalcLLR B_value get [{}, {}, {}]".format(layer,branch,phase-1))
        value = LLR2 + (-1)**B * LLR1
        path.setLLR(value, layer, branch, phase)
        #print("recursivelyCalcLLR set LLR_value [{}, {}, {}]".format(layer,branch,phase))
    
if __name__ == "__main__":
    from tests.polar import test_nr_polar_decoder_SC_optionB
    import time
    indata = np.array([1,0,1,0,1,0,1,0],'i1')
    N=8
    m=3
    F=[1,1,1,0,1,0,0,0]
    start = time.time()
    decodedbits,status = PolarSCDecoder(1-2*indata, F, N)
    print("N=8 PolarSCDecoder elpased time: {:6.6f}".format(time.time() - start))

    testlists = test_nr_polar_decoder_SC_optionB.get_testvectors()
    for _ in range(2):
        for idx, testcase in enumerate(testlists):
            print("count= {}".format(idx))
            test_nr_polar_decoder_SC_optionB.test_nr_polar_SC_decoder_no_noise(testcase)

    for _ in range(2):
        for idx, testcase in enumerate(testlists):
            print("count= {}".format(idx))
            test_nr_polar_decoder_SC_optionB.test_nr_polar_SC_decoder(testcase)