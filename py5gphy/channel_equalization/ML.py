# -*- coding:utf-8 -*-

import numpy as np
import itertools

from py5gphy.common import nrModulation
from py5gphy.channel_equalization import nr_channel_eq

def ML_IRC(Y, H,  cov, modtype,demod_decision="soft"):
    """ ML IRC channel equalization
    input:
        Y: Nr X 1 vector, recriving data
        H: Nr X NL matrix, channel estimation
        cov: Nr X Nr noise-interference covriance matrix
        where Nr is Rx antenna num, NL is Tx layer number
        demod_decision: 
            "soft": demodulation soft decision,output LLR,
            "hard": hard decision,output 1 for bit 0 and -1 for bit 1
    output:
        s_est: NL X 1 estimated signal vector
        noise_var:NL X 1 noise variance for each layer
        de_hardbits: NL*Qm size of [0,1] de-modulated hardbits array
        de_LLR_a: NL*Qm size of de-modulated LLR array
    """
    #make sure Y is Nr x 1 vector, if not, change it
    Nr, NL = H.shape
    if Y.shape != (Nr,1):
        #reshape
        Y= Y.reshape((Nr,1))

    assert Nr >= NL
    assert Nr == Y.size
    assert Nr == cov.shape[0] and Nr == cov.shape[1]

    #U^H @ U = inverse(cov)
    U = nr_channel_eq.cov_inverse_decompose(cov)

    #ML-IRC is to get argmin of(Y-HS)^H @ inv_com @ (Y-HS)
    #with U^H @ U = inv_com,
    #it change to (newY-newHS)^H @ (newY-newS) equation, which is ML estimation

    newY = U @ Y
    newH = U @ H

    return ML(newY, newH,  np.identity(Nr), modtype,demod_decision)

def ML(Y, H,  cov, modtype,demod_decision="soft"):
    """ ML channel equalization, hard bit decision
    input:
        Y: Nr X 1 vector, recriving data
        H: Nr X NL matrix, channel estimation
        cov: Nr X Nr noise-interference covriance matrix
        where Nr is Rx antenna num, NL is Tx layer number
        where Nr is Rx antenna num, NL is Tx layer number
        modtype:["pi/2-bpsk", "bpsk", "qpsk", "16qam", "64qam", "256qam", "1024qam"]
        demod_decision: 
            "soft": demodulation soft decision,output LLR,
            "hard": hard decision,output 1 for bit 0 and -1 for bit 1
    output:
        s_est: NL X 1 estimated signal vector
        noise_var:NL X 1 noise variance for each layer
        de_hardbits: NL*Qm size of [0,1] de-modulated hardbits array
        de_LLR_a: NL*Qm size of de-modulated LLR array
    """

    Nr, NL = H.shape
    if Y.shape != (Nr,1):
        #reshape
        Y= Y.reshape((Nr,1))

    assert Nr >= NL
    assert Nr == Y.size
    assert Nr == cov.shape[0] and Nr == cov.shape[1]

    sigma_2 = np.mean(np.diagonal(cov))    
    sigma_2 = sigma_2.real
    
    #mod_array is all modulation data, inbits_array is bit sequence for each modulation data
    mod_array,inbits_array= nrModulation.get_mod_list(modtype)
    num_qam_values,bitwidth = inbits_array.shape
    
    #generate combine_S_set which includa all combination of NL layer's S set
    S_set_list = []
    for nl in range(NL):
        S_set_list.append(list(mod_array))
    
    #generate all combination of sel_S from all layers
    combine_S_set = itertools.product(*S_set_list)

    #ML search s_est with minimum est value
    s_est, noise_var,de_hardbits = ML_searching_min_S(Y, H, cov, combine_S_set,mod_array,inbits_array)
    
    if demod_decision == "hard":
        LLR_a = 1-2*de_hardbits
    else:
        LLR_a = ML_soft_LLR_est(Y,H,noise_var,s_est,de_hardbits,modtype,sigma_2)

    return s_est, noise_var,de_hardbits, LLR_a

def ML_soft_LLR_est(Y,H,noise_var,s_est,de_hardbits,modtype,sigma_2):
    """ ML soft LLR est"""
    
    Nr, NL = H.shape
    total_size= de_hardbits.size
    bitwidth = total_size // NL
    LLR_a = np.zeros(total_size)
    offset = 0

    for nl in range(NL):
        #estimate min_S[nl] LLR bits while keeping other min_S value no change
        inbits = de_hardbits[nl*bitwidth:(nl+1)*bitwidth]

        #find Symbo list with opposite bit value for each bit,
        # for example, QAM16 symbol A with bits "1111" 
        #the symbol with first bit=0 and closest to symbol A is symbol with bits 0101
        #the symbol with second bit=0 and closest to symbol A is symbol with bits 1010
        #the symbol with third bit=0 and closest to symbol A is symbol with bits 1101
        #the symbol with forth bit=0 and closest to symbol A is symbol with bits 1110
        #the slection is related to QAM constellation
        opposite_syms = nrModulation.get_oppisite_syms(inbits,modtype)

        for m in range(bitwidth):
            #get the nl-th layer m-th bit LLR
            new_S = s_est.copy()
            new_S = new_S.reshape((NL,1))
            new_S[nl] = opposite_syms[m]

            dis_v = (Y - H @ new_S).conj().T @ (Y - H @ new_S) / sigma_2

            #LLR = -(b=0 value) + (b=1 value)
            if inbits[m] == 0:
                LLR = -noise_var[nl] + dis_v.real
            else:
                LLR = noise_var[nl] - dis_v.real
            
            LLR_a[offset] = LLR
            offset += 1
    
    return LLR_a

def ML_searching_min_S(Y, H, cov, combine_S_set,mod_array,inbits_array):
    """ML search S array and hardbits array from combine_S_set
    """
    Nr, NL = H.shape
    num_qam_values,bitwidth = inbits_array.shape
    
    sigma_2 = np.mean(np.diagonal(cov))    
    sigma_2 = sigma_2.real
    
    #min value, and related S array,hardbits array
    min_v = float('inf')
    min_S = np.array([0])
    
    S = np.zeros((NL,1), 'c8')
    
    for combine_S in combine_S_set:
        S[:,0] = combine_S #make it column array

        #cal(Y-HS)^H @ (Y-HS)
        delta = Y - H @ S
        v = delta.conj().T @ delta / sigma_2

        #v is (1,1) shape array, 
        realv = v[0][0].real
        #update min value
        if realv < min_v:
            min_v = realv
            min_S = S.copy() #really need copy of S
            
    s_est = min_S.reshape(min_S.size)

    #noise_var is NL element array with each value = min_v
    noise_var= min_v*np.ones(NL)

    #get hardbits sequence 
    de_hardbits = np.zeros((NL*bitwidth),'i8')
    for nl in range(NL):
        sel_s = s_est[nl]
        idx = np.where(mod_array == sel_s)[0][0]
        sel_hardbits = inbits_array[idx,:]
        de_hardbits[nl*bitwidth : (nl+1)*bitwidth] = sel_hardbits

    return s_est, noise_var,de_hardbits