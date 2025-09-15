# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy import interpolate

from py5gphy.common import nr_slot
from py5gphy.channel_estimate import nr_channel_estimation
from py5gphy.channel_estimate import dft_dct_CE

def DFT_DCT_symmetric_channel_estimate(H_LS,RS_info,CE_config,model):
    """ based on "DFT-Based Channel Estimation with Symmetric Extension for OFDMA Systems" by Yi Wang, Lihua Li, Ping Zhang & Zemin Liu 
    https://jwcn-eurasipjournals.springeropen.com/articles/10.1155/2009/647130
    and it also need extra processing to support 5G channel estimation
    input:
        H_LS: LS H estimation,the data may have go though timing compensation and frequency offset compensation
        RS_info:RS related info
        model: "DFT" or "DCT
    output:
        H_result: 14 symbol PDSCH channel estimation for each RE
        extended_cov_m:14 symbol cov for each RB
    """
    RE_distance = RS_info["RE_distance"]
    scs = RS_info["scs"]
    
    #for time domain IDFT output, path is in the range of [0:L_sym_left] and [L_sym_right:end]
    #the data in the middle is assumed to be noise
    L_symm_left_in_ns = CE_config["L_symm_left_in_ns"]
    L_symm_right_in_ns = CE_config["L_symm_right_in_ns"]
    eRB = CE_config["eRB"] #number of extra eRB added on each side
    eK = eRB * 12 // RE_distance #nuber of added RS RE on each side
    
    freq_intp_method = CE_config["freq_intp_method"]
    timing_intp_method = CE_config["timing_intp_method"]

    #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
    sym_num, RE_num,Nr,Nt = H_LS.shape
    
    #after add extra points on both side, the sequence size should be even to make fft works correctly.
    right_eK = eK + (RE_num + eK) % 2
    
    if (RE_num * RE_distance // 12) == 1:
        #do not support one PRB assignment
        assert 0
    
    #init
    H_est = np.zeros((sym_num, RE_num*RE_distance,Nr,Nt),'c8')
            
    #DFT/DCT channel est and interpolation to get each subcarrier H estimation for every [nr,nt]pair and every RS symbol
    for m in range(sym_num):
        for nt in range(Nt):
            for nr in range(Nr):
                sel_HLS = H_LS[m,:,nr, nt]
                
                #1. linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
                H_LS_with_extra = dft_dct_CE.HLS_extra(sel_HLS, eK,right_eK, 
                RE_distance)

                #2. symmetric extension to H_LS_sym
                H_LS_sym = np.zeros(2*(RE_num + eK + right_eK),'c8')                  
                H_LS_sym[0:H_LS_with_extra.size] = H_LS_with_extra
                H_LS_sym[H_LS_with_extra.size:] = H_LS_with_extra[-1::-1]
                
                #3. ifft or dct to time domain
                if model == "DFT":
                    #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
                    h_sym = fft.ifft(fft.ifftshift(H_LS_sym))*np.sqrt(H_LS_sym.size)
                else:
                    h_sym = fft.dct(H_LS_sym,norm="ortho")
                
                #4.get L_left and L_right in sample
                # [L_left, 2048-L_right] are pure noise
                h_sym_sample_rate_in_hz = H_LS_sym.size * scs * 1000 * RE_distance
                
                L_left = int(L_symm_left_in_ns /( 10**9/h_sym_sample_rate_in_hz))
                #for symmetric method, taps in time domain also symmetric extended on right side,
                # L_right should be equal to L_left
                L_left = min(h_sym.size // 3 + h_sym.size // 16,L_left)
                L_right = L_left
                
                #5. first noise power est
                first_noise_power = np.mean(np.abs(h_sym[L_left:h_sym.size-L_right])**2)
                
                #6 remove noise in h_sym 
                #(1) all the signals that 30dB lower than peak signal is regarded as noise - it has issues
                # (2) all the signals that are lower than first noise power is regarded as noise 
                # (3)h_sym[L_left:2048-L_right] is regarded as noise
                h_sym[np.abs(h_sym) < np.sqrt(first_noise_power/2)] = 0
                h_sym[L_left:h_sym.size-L_right] = 0
                
                #7. dft or idct to freq 
                if model == "DFT":
                    dft_o = fft.fftshift(fft.fft(h_sym))/np.sqrt(h_sym.size)
                else:
                    dft_o = fft.idct(h_sym,norm="ortho")
                
                #8. symmetric combination
                first_part = dft_o[0:dft_o.size//2]
                second_part = dft_o[-1:-dft_o.size//2-1:-1]
                
                #combined H is final H estimation
                H_comb = (first_part + second_part)/2 

                #9.frequency interpolate to all RE
                intp_H = dft_dct_CE.freq_interpolate(dft_o,RE_distance,freq_intp_method)
                
                #10 remove extra interpolation points and get H estimation for each RE
                H_est_result =intp_H[eK*RE_distance : eK*RE_distance + RE_distance*RE_num] 
                
                H_est[m,:,nr,nt] = H_est_result                    
                
    #time domain interpolation to gen 14 symbol channel est result
    H_result = dft_dct_CE.timing_interpolate_to_14_symbol(H_est,RS_info["RSSymMap"])
    
    #estimate noise and interference covariance matrix
    extended_cov_m = dft_dct_CE.cov_m_estimate(H_LS, H_est,RE_distance, RS_info["NumCDMGroupsWithoutData"],RS_info["RSSymMap"])
    
    return H_result, extended_cov_m
