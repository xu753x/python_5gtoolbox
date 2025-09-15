# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrModulation
from py5gphy.channel_equalization import ML
from py5gphy.channel_equalization import nr_channel_eq

def opt_rank2_ML_IRC(Y, H,  cov, modtype,demod_decision="soft"):
    """optimized ML to reduce complexity from N^2 to N
    and it works for rank=2 only
    refer to docs\algorithm\optimized_rank2_ML_channel_equalization.md
    """
    Nr, NL = H.shape
    if NL != 2:
        return ML.ML_IRC(Y, H,  cov, modtype)
    
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

    return opt_rank2_ML(newY, newH,  np.identity(Nr), modtype,demod_decision)

def opt_rank2_ML(Y, H,  cov, modtype,demod_decision="soft"):
    """optimized ML to reduce complexity from N^2 to N
    and it works for rank=2 only
    refer to docs\algorithm\optimized_rank2_ML_channel_equalization.md
    """
    Nr, NL = H.shape
    if NL != 2:
        return ML.ML(Y, H,  cov, modtype)
    
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
    
    #get x or y value array
    x_mod_array = np.array(list(set(mod_array.real)))

    #generate coefficient values, YH.shape=(1,2)
    YH = Y.conj().T @ H
    a0i,a0q,a1i,a1q = [YH[0,0].real,YH[0,0].imag,YH[0,1].real,YH[0,1].imag]
    
    HH = H.conj().T @ H
    a2, a3, a4i, a4q = [HH[0,0].real,HH[1,1].real,HH[0,1].real,HH[0,1].imag]
    
    #do ML search based on L2 equation
    L2_min = float('inf')
    for s0 in mod_array:
        x0, y0 = [s0.real, s0.imag]
        
        L21 = a2*(x0**2+y0**2)-2*a0i*x0+2*a0q*y0

        #get x1 that is closest to x1_hat
        x1_hat = -(-a1i + a4i*x0 + a4q*y0)/a3
        distance = np.abs(x_mod_array - x1_hat)
        sorted_indices = np.argsort(distance)
        if a3 > 0:
            #closest to x1_hat is min value
            cx1 = x_mod_array[sorted_indices[0]]
        else:
            #farest to x1_hat is min value
            cx1 = x_mod_array[sorted_indices[-1]]

        L22_min = a3*cx1*cx1 + 2*(-a1i + a4i*x0 + a4q*y0)*cx1

        #get y1 that is closest to y1_hat
        y1_hat = -(a1q + a4i*y0 - a4q*x0)/a3
        distance = np.abs(x_mod_array - y1_hat)
        sorted_indices = np.argsort(distance)
        if a3 > 0:
            #closest to y1_hat is min value
            cy1 = x_mod_array[sorted_indices[0]]
        else:
            #farest to y1_hat is min value
            cy1 = x_mod_array[sorted_indices[-1]]
        
        L23_min = a3*cy1*cy1 + 2*(a1q + a4i*y0 - a4q*x0)*cy1

        L2 = L21 + L22_min + L23_min
        if L2 < L2_min:
            L2_min = L2
            L2_s0_min = s0
            L2_s1_min = cx1 + 1j*cy1
    
    #do ML search based on L3 equation
    L3_min = float('inf')
    for s1 in mod_array:
        x1, y1 = [s1.real, s1.imag]
        
        L31 = a3*(x1**2+y1**2)-2*a1i*x1+2*a1q*y1

        #get x0 that is closest to x0_hat
        x0_hat = -(-a0i + a4i*x1 - a4q*y1)/a2
        distance = np.abs(x_mod_array - x0_hat)
        sorted_indices = np.argsort(distance)
        if a2 > 0:
            #closest to x0_hat is min value
            cx0 = x_mod_array[sorted_indices[0]]
        else:
            #farest to x0_hat is min value
            cx0 = x_mod_array[sorted_indices[-1]]
        
        L32_min = a2*cx0*cx0 + 2*(-a0i + a4i*x1 - a4q*y1)*cx0

        #get y0 that is closest to y0_hat
        y0_hat = -(a0q + a4i*y1 + a4q*x1)/a2
        distance = np.abs(x_mod_array - y0_hat)
        sorted_indices = np.argsort(distance)
        if a2 > 0:
            #closest to y1_hat is min value
            cy0 = x_mod_array[sorted_indices[0]]
        else:
            #farest to y1_hat is min value
            cy0 = x_mod_array[sorted_indices[-1]]
        
        L33_min = a2*cy0*cy0 + 2*(a0q + a4i*y1 + a4q*x1)*cy0

        L3 = L31 + L32_min + L33_min
        
        if L3 < L3_min:
            L3_min = L3
            L3_s0_min = cx0 + 1j*cy0
            L3_s1_min = s1
    
    assert L2_s0_min == L3_s0_min and L2_s1_min == L3_s1_min

    s_est = np.array([L2_s0_min,L2_s1_min],'c8')
    
    noise_var= ((Y.conj().T @ Y)[0][0].real+L2_min)/sigma_2*np.ones(2)

    NL = 2
    #get hardbits sequence 
    de_hardbits = np.zeros((NL*bitwidth),'i8')
    for nl in range(NL):
        sel_s = s_est[nl]
        idx = np.where(mod_array == sel_s)[0][0]
        sel_hardbits = inbits_array[idx,:]
        de_hardbits[nl*bitwidth : (nl+1)*bitwidth] = sel_hardbits
    
    if demod_decision == "hard":
        LLR_a = 1-2*de_hardbits
    else:
        LLR_a = ML.ML_soft_LLR_est(Y,H,noise_var,s_est,de_hardbits,modtype,sigma_2)
    
    return s_est, noise_var,de_hardbits, LLR_a