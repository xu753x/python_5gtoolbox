# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy import interpolate

from py5gphy.common import nr_slot
from py5gphy.channel_estimate import nr_channel_estimation

def DFT_DCT_channel_estimate(H_LS,RS_info,CE_config,model):
    """ 
    DFT or DCT channel estimation
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
                H_LS_with_extra = HLS_extra(sel_HLS, eK,right_eK, RE_distance)
                                    
                #2. ifft or DCT to time domain
                if model == "DFT":
                    #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
                    h_sym = fft.ifft(fft.ifftshift(H_LS_with_extra))*np.sqrt(H_LS_with_extra.size)
                else:
                    h_sym = fft.dct(H_LS_with_extra,norm="ortho")

                #sample rate of h_sym 
                h_sym_sample_rate_in_hz = scs * 1000 * RE_distance * H_LS_with_extra.size
                
                #L_left and L_right indicate noise window
                L_left = int(L_symm_left_in_ns * 1e-9 * h_sym_sample_rate_in_hz)
                L_right = int(L_symm_right_in_ns * 1e-9 * h_sym_sample_rate_in_hz)
                
                #3. first noise power est
                first_noise_power = np.mean(np.abs(h_sym[L_left:h_sym.size-L_right])**2)

                #4 remove noise in h_sym 
                #(1) all the signals that 30dB lower than peak signal is regarded as noise -has issue
                # (2) all the signals that are lower than first noise power is regarded as noise 
                # (3)h_sym[L_left:-L_right] is regarded as noise
                #peak_p = np.max(np.abs(h_sym))
                #h_sym[np.abs(h_sym) < peak_p*10**(-30/20)] = 0
                h_sym[np.abs(h_sym) < np.sqrt(first_noise_power/2)] = 0
                h_sym[L_left:h_sym.size-L_right] = 0

                #5. dft or idct to freq 
                if model == "DFT":
                    dft_o = fft.fftshift(fft.fft(h_sym))/np.sqrt(h_sym.size)
                else:
                    dft_o = fft.idct(h_sym,norm="ortho")

                #6. frequency interpolate to all RE
                intp_H = freq_interpolate(dft_o,RE_distance,freq_intp_method)

                #7， remove extra interpolation points and get H estimation for each RE
                H_est_result =intp_H[eK*RE_distance : eK*RE_distance + RE_distance*RE_num] 
                
                H_est[m,:,nr,nt] = H_est_result                    
    
    #time domain interpolation to gen 14 symbol channel est result
    H_result = timing_interpolate_to_14_symbol(H_est,RS_info["RSSymMap"])
    
    #estimate noise and interference covariance matrix
    extended_cov_m = cov_m_estimate(H_LS, H_est,RE_distance, RS_info["NumCDMGroupsWithoutData"],RS_info["RSSymMap"])
    
    return H_result, extended_cov_m

def HLS_extra(sel_HLS, eK,right_eK, RE_distance):
    """linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
    """
    RE_num = sel_HLS.size
    
    #2RB RS data on each side are used for extra interpolation
    xp_left = range(2*12//RE_distance)
    xp_right = range(RE_num - 2*12//RE_distance,RE_num)
        
    H_LS_with_extra = np.zeros(RE_num+eK+right_eK,'c8')

    #get left side extra interpolation at point [.., -4,-3,-2,-1]
    #np.interp repeate the leftest value for extrapolating point,which is not we expect,
    #left_extra = np.interp(list(range(-eK,0)),xp_left,sel_HLS[xp_left])
    #use polyfit
    coeff = np.polyfit(xp_left,sel_HLS[xp_left],1)
    fit_func = np.poly1d(coeff)
    left_extra = fit_func(range(-eK,0))
                        
    #get right side extra interpolation at point [RE_num,RE_num+1,RE_num+2,..]
    coeff = np.polyfit(xp_right,sel_HLS[xp_right],1)
    fit_func = np.poly1d(coeff)
    right_extra = fit_func(range(RE_num,RE_num+right_eK))
    
    #fill new H_LS with extra points
    H_LS_with_extra[0:eK] = left_extra
    H_LS_with_extra[eK : RE_num+eK] = sel_HLS
    H_LS_with_extra[RE_num+eK:] = right_extra

    return H_LS_with_extra

def freq_interpolate(dft_o,RE_distance,freq_intp_method):
    """ freqeuency interpolation
    """
    size = dft_o.size * RE_distance

    xnew = np.arange(size)
    
    x = xnew[::RE_distance]
    y = dft_o

    if freq_intp_method == "linear":
        ynew = np.interp(xnew, x, y)
    elif freq_intp_method == "CubicSpline":
        spl = interpolate.CubicSpline(x, y)
        ynew = spl(xnew, nu=1) #1st derivative
    elif freq_intp_method == "PchipInterpolator":
        spl = interpolate.PchipInterpolator(x, y)
        ynew = spl(xnew)
    else:
        #default 
        ynew = np.interp(xnew, x, y)
    
    return ynew

def timing_interpolate_to_14_symbol(H_est,RSSymMap,timing_intp_method=None):
    """time domain interpolation H_est to to gen 14 symbol channel est result
    """
    sym_num, RE_len,Nr,Nt = H_est.shape

    H_result = np.zeros((14, RE_len,Nr,Nt),'c8')
    if sym_num > 1:
        for sc in range(RE_len):
            for nr in range(Nr):
                for nt in range(Nt):
                    #linear interpolation to [0:13] symbols
                    #H_result[:,sc,nr,nt] = np.interp(range(14), RSSymMap, H_est[:,sc,nr,nt])
                    coeff = np.polyfit(RSSymMap,H_est[:,sc,nr,nt],1)
                    fit_func = np.poly1d(coeff)
                    H_result[:,sc,nr,nt]  = fit_func(range(14))
    else:
        for m in range(14):
            H_result[m,:,:,:] = H_est[0,:,:,:]

    return H_result

def cov_m_estimate(H_LS, H_est,RE_distance, NumCDMGroupsWithoutData,RSSymMap):
    """estimate noise and interference covariance matrix cov_m and extend to 14 symbols
    cov = (HLS - H_est) @ (HLS - H_est)^H
    """
    #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
    sym_num, RE_num,Nr,Nt = H_LS.shape
    
    #MIMO reciever: Y = H*S + I+N where I +N is interference pluse noise, for RS data, we can assume S is all ones vector
    #Y is reagrded as = H_LS * S, add all column's H_LS together to get Y
    #all all column's H_est to get H*S
    #cov_matrix = cov((Y-HS)*(Y-HS)^H)
    
    nHS = H_LS - H_est[:,::RE_distance,:,:]
    
    #cov matrix is Nr X Nr dimension
    #38.214 Table 5.2.1.4-2: Configurable subband sizes shows subband size for different BW, 
    #here we just choose M PRB
    #so for every M PRB and every RS symbol, calculate one Nr X Nr cov matrix
    #then linear interpolation to get 14 symbols cov matrix 
    num_RB_for_cov_est = 16

    RE_num_per_M_RB = int(12 // RE_distance) * num_RB_for_cov_est
    num_of_M_prbs = RE_num // RE_num_per_M_RB
    residule_REs = RE_num - num_of_M_prbs * RE_num_per_M_RB
    if residule_REs:
        num_of_M_prbs -= 1
        residule_REs += RE_num_per_M_RB

    total_prbs = int(RE_num * RE_distance // 12)

    #cov_m save cov matrix in PRB level
    cov_m = np.zeros((sym_num,total_prbs,Nr,Nr),'c8')

    for m in range(sym_num):
        for idx in range(num_of_M_prbs):
            sel_nHS = nHS[m,idx*RE_num_per_M_RB:(idx+1)*RE_num_per_M_RB,:,:]
            sum_cov = np.zeros((Nr,Nr),'c8')
            for re in range(RE_num_per_M_RB):
                sel_d = sel_nHS[re,:,:]
                cov_v = sel_d @ sel_d.conj().T
                sum_cov += cov_v
            
            cov_m[m,idx*num_RB_for_cov_est:(idx+1)*num_RB_for_cov_est,:,:] = sum_cov/RE_num_per_M_RB/Nt
        if residule_REs:
            sel_nHS = nHS[m,num_of_M_prbs*RE_num_per_M_RB:,:,:]
            sum_cov = np.zeros((Nr,Nr),'c8')
            for re in range(residule_REs):
                sel_d = sel_nHS[re,:,:]
                cov_v = sel_d @ sel_d.conj().T
                sum_cov += cov_v
            
            cov_m[m,num_of_M_prbs*num_RB_for_cov_est:,:,:] = sum_cov/residule_REs/Nt
            

    #cov_m need compensation basded on NumCDMGroupsWithoutData value
    #estimated H_LS = (d0+d1)/(2*DMRS_scaling), and DMRS_scaling=-3dB for NumCDMGroupsWithoutData=2 and dB for NumCDMGroupsWithoutData = 1
    #d0 and d1 are two RS RE receiving data * ref_RS sequence,
    # in (d0+d1)/(2*DMRS_scaling) calculation, noise power is reduced by 2 for DMRS_scaling=0dB case
    #cov_m need compensate this noise reduction
    if NumCDMGroupsWithoutData == 1:
        cov_m *= 2
    
    #interpolate cov_m to get 14 symbol data
    extended_cov_m = np.zeros((14,total_prbs,Nr,Nr),'c8')
    if sym_num > 1:
        for prb in range(total_prbs):
            for nr in range(Nr):
                for nr2 in range(Nr):
                    #linear interpolation to [0:13] symbols
                    #H_result[:,sc,nr,nt] = np.interp(range(14), RSSymMap, H_est[:,sc,nr,nt])
                    coeff = np.polyfit(RSSymMap,cov_m[:,prb,nr,nr2],1)
                    fit_func = np.poly1d(coeff)
                    extended_cov_m[:,prb,nr,nr2]  = fit_func(range(14))
    else:
        for m in range(14):
            extended_cov_m[m,:,:,:] = cov_m[0,:,:,:]

    return extended_cov_m

def bak_cov_m_estimate(H_LS, H_est,RE_distance, NumCDMGroupsWithoutData,RSSymMap):
    """estimate noise and interference covariance matrix cov_m and extend to 14 symbols
    """
    #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
    sym_num, RE_num,Nr,Nt = H_LS.shape
    
    #MIMO reciever: Y = H*S + I+N where I +N is interference pluse noise, for RS data, we can assume S is all ones vector
    #Y is reagrded as = H_LS * S, add all column's H_LS together to get Y
    #all all column's H_est to get H*S
    #cov_matrix = cov((Y-HS)*(Y-HS)^H)
    

    #first to get Y and H*S
    Y = np.zeros((sym_num,RE_num,Nr),'c8')
    HS = np.zeros((sym_num,RE_num,Nr),'c8')

    for m in range(sym_num):
        for nr in range(Nr):  
            Y[m,:,nr] = np.sum( H_LS[m,:,nr,:], axis=1)
            HS[m,:,nr] = np.sum(H_est[m,::RE_distance,nr,:],axis=1)
    
    IN_est = (Y - HS)/np.sqrt(Nt)

    #cov matrix is Nr X Nr dimension
    #38.214 Table 5.2.1.4-2: Configurable subband sizes shows subband size for different BW, 
    #here we just choose M PRB
    #so for every M PRB and every RS symbol, calculate one Nr X Nr cov matrix
    #then linear interpolation to get 14 symbols cov matrix 
    num_RB_for_cov_est = 16

    RE_num_per_M_RB = int(12 // RE_distance) * num_RB_for_cov_est
    num_of_M_prbs = RE_num // RE_num_per_M_RB
    residule_REs = RE_num - num_of_M_prbs * RE_num_per_M_RB
    total_prbs = int(RE_num * RE_distance // 12)

    #cov_m save cov matrix in PRB level
    cov_m = np.zeros((sym_num,total_prbs,Nr,Nr),'c8')

    for m in range(sym_num):
        for idx in range(num_of_M_prbs):
            xm = IN_est[m,idx*RE_num_per_M_RB:(idx+1)*RE_num_per_M_RB,:]
            cov_v = np.cov(xm, rowvar=False)
            cov_m[m,idx*num_RB_for_cov_est:(idx+1)*num_RB_for_cov_est,:,:] = cov_v
        if residule_REs:
            xm = IN_est[m,num_of_M_prbs*RE_num_per_M_RB:,:]
            cov_v = np.cov(xm, rowvar=False)
            cov_m[m,num_of_M_prbs*num_RB_for_cov_est:,:,:] = cov_v

    #cov_m need compensation basded on NumCDMGroupsWithoutData value
    #estimated H_LS = (d0+d1)/(2*DMRS_scaling), and DMRS_scaling=-3dB for NumCDMGroupsWithoutData=2 and dB for NumCDMGroupsWithoutData = 1
    #d0 and d1 are two RS RE receiving data * ref_RS sequence,
    # in (d0+d1)/(2*DMRS_scaling) calculation, noise power is reduced by 2 for DMRS_scaling=0dB case
    #cov_m need compensate this noise reduction
    if NumCDMGroupsWithoutData == 1:
        cov_m *= 2
    
    #interpolate cov_m to get 14 symbol data
    extended_cov_m = np.zeros((14,total_prbs,Nr,Nr),'c8')
    if sym_num > 1:
        for prb in range(total_prbs):
            for nr in range(Nr):
                for nr2 in range(Nr):
                    #linear interpolation to [0:13] symbols
                    #H_result[:,sc,nr,nt] = np.interp(range(14), RSSymMap, H_est[:,sc,nr,nt])
                    coeff = np.polyfit(RSSymMap,cov_m[:,prb,nr,nr2],1)
                    fit_func = np.poly1d(coeff)
                    extended_cov_m[:,prb,nr,nr2]  = fit_func(range(14))
    else:
        for m in range(14):
            extended_cov_m[m,:,:,:] = cov_m[0,:,:,:]

    return extended_cov_m
