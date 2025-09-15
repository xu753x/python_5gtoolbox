# -*- coding:utf-8 -*-

import numpy as np
import itertools
import copy

from py5gphy.common import nrModulation
from py5gphy.channel_equalization import MMSE
from py5gphy.channel_equalization import ML
from py5gphy.channel_equalization import nr_channel_eq

def MMSE_ML_IRC(Y, H,  cov, modtype):
    """
    1. MMSE to get s_est, 
    2. select N constellation points close to s_est,then does ML estimate
    the algorithm is to reduce pure ML heavy loading
    """
    
    max_neigh_points = 4 #maxinum of points selected that is close to s_est for each layer

    #first MMSE to get s_est
    mmse_s_est, mmse_noise_var = MMSE.MMSE_IRC(Y, H, cov)

    #below processing is almost the cobination ofsame with ML_IRC function
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
    new_cov = np.identity(Nr)

    return subset_ML(newY, newH, new_cov, modtype,mmse_s_est,max_neigh_points)

def MMSE_ML(Y, H,  cov, modtype):
    """
    1. MMSE to get s_est, 
    2. select N constellation points close to s_est,then does ML estimate
    the algorithm is to reduce pure ML heavy loading
    """
    
    max_neigh_points = 4 #maxinum of points selected that is close to s_est for each layer

    #first MMSE to get s_est
    mmse_s_est, mmse_noise_var = MMSE.MMSE(Y, H, cov)

    #below processing is almost the cobination ofsame with ML_IRC function
    Nr, NL = H.shape
    if Y.shape != (Nr,1):
        #reshape
        Y= Y.reshape((Nr,1))

    assert Nr >= NL
    assert Nr == Y.size
    assert Nr == cov.shape[0] and Nr == cov.shape[1]
    
    return subset_ML(Y, H, cov, modtype,mmse_s_est,max_neigh_points)

def subset_ML(Y, H, cov, modtype,mmse_s_est,max_neigh_points):
    """ refer to ML.py to get more information"""
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

    S_set_list = []
    for estS in mmse_s_est:
        distance = np.abs(mod_array - estS)
        sorted_indices = np.argsort(distance)
        sel_S = mod_array[sorted_indices[0:min(sorted_indices.size,max_neigh_points)]]

        S_set_list.append(list(sel_S))
    
    #generate all combination of sel_S from all layers
    combine_S_set = itertools.product(*S_set_list)
    
    #ML search s_est with minimum est value
    s_est, noise_var,de_hardbits = ML.ML_searching_min_S(Y, H, cov, combine_S_set,mod_array,inbits_array)
    
    LLR_a = ML.ML_soft_LLR_est(Y,H,noise_var,s_est,de_hardbits,modtype,sigma_2)

    return s_est, noise_var,de_hardbits, LLR_a
