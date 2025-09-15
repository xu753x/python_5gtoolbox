# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft

from py5gphy.common import nr_slot

class NrChannelEstimation():
    """ Channel estimation operation which is used for PDSCH, PUSCH, SRS,CSI-RS receiving estimation
    it include:
    (1) timing error estimation for each DMRS symbol
    (2) frequency error estimation including doppler freq error estimation and carrier freq error estimation
    (3) timing error compensation
    (4) frequency error compensation'
    (5) DFT and DCT channel estimation
    (6) rank, PMI, CQI estimate
    """

    def __init__(self, H_LS, RS_info, CE_config):
        """
        H_LS: H matrix LS estimate value, the data is (num_sym, RE_size, Nr, Nt) format matrix
          where num_sym is number of RS symbol, RE_size is number of RS RE in one symbol, 
          Nr is number of Rx antenna, Nt is number of Tx layer
        RS_info: RS information map including:
            "type": in ["nr_pdsch", "nr_pusch", "csi_rs","srs"]
            "PortIndexList" : antenna port index list
          "RSSymMap": RS symbol indexes for each RS symbol
          "RE_distance": RE distance among two RS RE, it is usually 4 for PDSCH 
          "scs": 15 or 30
          "carrier_frequency_in_mhz": carrer frequency
        CE_config:
            "enable_TO_comp": True: enable timing offset compensation
            "enable_FO_est': True: enable frequency offset est
            "enable_FO_comp" True: enable freq offset compensation
            "enable_carrier_FO_est": enable carrier freq offset estimation
            "enable_carrier_FO_TO_comp": enable timing offet compensation by carrier freq offset
            "CE_algo": channel est algorithm, "DFT" or "DCT"
            "enable_rank_PMI_CQI_est" True: enable rank, PMI, CQI estimate
            "L_left_in_ns":,
            "L_right_in_ns":
        """
        self.H_LS = H_LS
        self.RS_info = RS_info
        self.CE_config = CE_config

        self.freq_offset = None

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = H_LS.shape

        assert sym_num == len(RS_info["RSSymMap"])
        assert RS_info["scs"] in [15,30]

        self.peak_H_LS = self.find_peak_H_LS(H_LS)
        symbols_timing_offset_list, _ = nr_slot.get_symbol_timing_offset(RS_info["scs"])
        self.symbols_timing_offset_list = symbols_timing_offset_list #symbol timing offset in second to the beginning of the slot
    
    def find_peak_H_LS(self,H_LS):
        """ find [tx,rx] pair with maximum power
        """
        sym_num, RE_num,Nr,Nt = H_LS.shape
        peak_p = 0
        peak_loc = [0,0]
        for nt in range(Nt):
            for nr in range(Nr):
                LS_result = H_LS[:,:,nr, nt]
                #mean value of the entire 2D array
                mean_p  = abs(np.mean(LS_result*LS_result.conj()))
                if mean_p > peak_p:
                    peak_p = mean_p
                    peak_loc = [nr, nt]

        #choose peak [tx,rx] pair
        peak_H_LS = H_LS[:,:,peak_loc[0], peak_loc[1]]
        return peak_H_LS
    
    def channel_est(self,freq_offset=None):
        """ channel estimation"""
        self.freq_offset = freq_offset

        #1. timing offset est
        self.timing_offset_est()

        #2. timing offset compensation
        if self.CE_config["enable_TO_comp"]:
            self.comp_H_LS_timing_offset()
        
        #3. fre enable_FO_est
        if self.CE_config["enable_FO_est"]:
            FO_status,FO_est = self.freq_offset_est()
        else:
            FO_status = False
            FO_est = 0
        self.FO_status = FO_status
        self.FO_est = FO_est

        
        #4. freq offser comp
        if self.CE_config["enable_FO_comp"]:
            if freq_offset:
                #use freq offset external provided. freq offset estimation by only one slot data is usually not correct, usually it need N slots data to precisely estimate freq offset, and then provide here for compensation
                self.comp_H_LS_freq_offset(freq_offset)
            else:
                #if freq offset estimated by current slot
                if FO_status:
                    self.comp_H_LS_freq_offset(FO_est)
        
        #channel est
        if self.CE_config["CE_algo"] == "DFT":
            H_result, cov_m = self.DFT_channel_estimate()
        elif self.CE_config["CE_algo"] == "DFT_symmetric":
            H_result, cov_m = self.DFT_symmetric_channel_estimate()
        elif self.CE_config["CE_algo"] == "DCT":
            H_result, cov_m = self.DCT_channel_estimate()
        elif self.CE_config["CE_algo"] == "DCT_symmetric":
            H_result, cov_m = self.DCT_symmetric_channel_estimate()
        else:
            assert 0
        
        self.H_result = H_result
        self.cov_m = cov_m

        return H_result, cov_m

    def process_pdsch_data(self,pdsch_resource,pdsch_start_sym):
        """timing offset compensation and freq offset compensation"""
        #. timing offset compensation
        if self.CE_config["enable_TO_comp"]:
            pdsch_resource = self.comp_pdsch_timing_offset(pdsch_resource)
        
        #freq offser comp
        if self.CE_config["enable_FO_comp"]:
            if self.freq_offset:
                #use freq offset external provided. freq offset estimation by only one slot data is usually not correct, usually it need N slots data to precisely estimate freq offset, and then provide here for compensation
                pdsch_resource = self.comp_pdsch_freq_offset(pdsch_resource,pdsch_start_sym,self.freq_offset)
            else:
                #if freq offset estimated by current slot
                if self.FO_status:
                    pdsch_resource = self.comp_pdsch_freq_offset(pdsch_resource,pdsch_start_sym,self.FO_est)
        return pdsch_resource
    
    def timing_offset_est(self):
        """ timing offset in second estimate, return each RS symbol's Time_offset est result
            algo TO = mean(arg(H_LS[1:]*H_LS[0:-1]))/(2*pi)
            
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape

        TO_est = np.zeros(sym_num)
        for m in range(sym_num):
            sel_H_LS = self.peak_H_LS[m,:]
            
            #H_LS[m] * H_LS[m-1].conj() = exp(j*2*pi*scs*RE_distance*Te)
            conv_diff = sel_H_LS[1:] * sel_H_LS.conj()[0:-1]
            
            phase_diff = np.arctan2(conv_diff.imag,conv_diff.real)/(2*np.pi*RE_distance*scs*1000)
            TO_est[m] = phase_diff.mean()
        
        self.TO_est = TO_est
        return TO_est

    def comp_H_LS_timing_offset(self):
        """compensate timing offset
        phase correction formula: exp(-j2*np.pi*TO*RE_distance*k*scs*1000)
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape

        avg_TO = np.mean(self.TO_est)
        
        #if self.CE_config["enable_carrier_FO_TO_comp"]:
        if 0:
            #timing offset compensate because of carrier freq offset rho
            RSSymMap = self.RS_info["RSSymMap"]
            sym_num = len(RSSymMap)
            RS_sym_timing_offset = self.symbols_timing_offset_list[RSSymMap]

            for m in range(sym_num):
                sym_added_timingoffset = self.rho * (RS_sym_timing_offset[m] - RS_sym_timing_offset[0])
                phase_correct = np.exp(-1j*2*np.pi*(avg_TO+sym_added_timingoffset)*RE_distance*np.arange(RE_num)*scs*1000)
                for nt in range(Nt):
                    for nr in range(Nr):
                        LS_result = self.H_LS[m,:,nr, nt]
                        LS_result *= phase_correct
            
        else:
            #no timing offset compensate for carrier freq offset rho
            phase_correct = np.exp(-1j*2*np.pi*avg_TO*RE_distance*np.arange(RE_num)*scs*1000)
            for nt in range(Nt):
                for nr in range(Nr):
                    LS_result = self.H_LS[:,:,nr, nt]
                    LS_result *= phase_correct
        
    def comp_pdsch_timing_offset(self,pdsch_resource):
        """compensate PDSCH resource timing offset"""
        scs = self.RS_info["scs"]
        avg_TO = np.mean(self.TO_est)
        
        NrOfSymbols,RE_num,Nr = pdsch_resource.shape
        phase_correct = np.exp(-1j*2*np.pi*avg_TO*np.arange(RE_num)*scs*1000)

        for nr in range(Nr):
            for m in range(NrOfSymbols):
                pdsch_resource[m,:,nr] *= phase_correct
        
        return pdsch_resource


    def freq_offset_est(self):
        """freq offset est need at least two RS symbol
        alg is mean estimation
           first transfer RS symbols to time domain by IFFT
           phase diff = j*2*pi*FO*Tn 
              where FO is freq offset, Tn is timing difference between two RS symbol
            the maximum freq offset should be 2*pi*FO*Tn <pi, or the phase may rotate by 2*pi
            for example, for 15khz 2 DMRS symbol case, Tn = 0.00064271 second,
            FO should < 1/(2*Tn) = 778 Hz
        
        ATTN: frequency offset estimation using one slot data is not accurate, it need average overall multiple slots estimation to get better result
        """
        RSSymMap = self.RS_info["RSSymMap"]
        sym_num = len(RSSymMap)
        
        if sym_num == 1:
            # no freq offset estimation if only one RS symbol
            self.FO_est = 0
            return False, 0
        
        RS_sym_timing_offset = self.symbols_timing_offset_list[RSSymMap]

        #each symbol IFFT to time domain and select peak power value
        max_v = np.zeros(sym_num, 'c8')
        for m in range(sym_num):
            sel_d = self.peak_H_LS[m,:]
            ifftin = np.zeros(4096,'c8')
            ifftin[4096//2-sel_d.shape[0]//2:4096//2-sel_d.shape[0]//2+sel_d.shape[0]] = sel_d
            ifftout = fft.ifft(ifftin)

            if m == 0:
                max_loc = np.argmax(np.abs(ifftout))

            max_v[m] = ifftout[max_loc]       

        #conv_d = exp(j*2*pi*freq_error * Tn) 
        #where Tn is timing offset between two DMRS symbol
        conv_d = max_v[1:] * max_v.conj()[0:-1]
        FO_diff = np.arctan2(conv_d.imag,conv_d.real)/(2*np.pi)
        FO_est = np.mean(FO_diff/(RS_sym_timing_offset[1:]-RS_sym_timing_offset[0:-1]))
        
        self.FO_est = FO_est
        return True, FO_est
    
    def cal_carrier_relative_freq_offset(self):
        """ this function start after finishing time offset est 
        the code is to estimayt carrier relative freq offset rho based on timing offset difference among RS symbols
        """
        RSSymMap = self.RS_info["RSSymMap"]
        sym_num = len(RSSymMap)
        
        if sym_num == 1:
            # no freq error estimation if only one RS symbol
            self.rho = 0
            return False, 0
        
        RS_sym_timing_offset = self.symbols_timing_offset_list[RSSymMap]

        #estimate XO relative frequency offset rho, usually it is in range 1ppm to 0.01ppm
        # the carrier frequenc offset = rho * carrier frequency
        # timing offset for each symbol is rho * symbol timing offset
        #LLS method is used to estimate tho

        #gen X martrix used for LLS
        #assume three RS symbol  X = [[1,  1, 1, 1.........,  1];
        #                           [sym_timingoffset 0, sym_timingoffset 1, sym_timingoffset 2]]
        X = np.array([[1]*sym_num,RS_sym_timing_offset-RS_sym_timing_offset[0]])
        W = np.linalg.inv(X @ X.T) @ X #W is 2 by sym_num matrix

        rho = W[1,:] @ self.TO_est.T
        
        self.rho = rho
        return True, rho

    def b1_comp_H_LS_freq_offset(self):
        """ compensate H_LS freq offset
        freq offset compensation happen on time domain
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape

        ifftsize = RE_num #
        td_sample_rate = ifftsize * scs * 1000 * RE_distance

        RSSymMap = self.RS_info["RSSymMap"]
        RS_sym_timing_offset = self.symbols_timing_offset_list[RSSymMap]

        for m in range(sym_num):
            sym_timingoffset = RS_sym_timing_offset[m] + np.arange(ifftsize)/td_sample_rate
            phase_correct = np.exp(-1j*2*np.pi*self.FO_est*sym_timingoffset)
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_H_LS = self.H_LS[m,:,nr, nt]
                    ifftout = fft.ifft(fft.ifftshift(sel_H_LS))

                    ifftout *= phase_correct

                    fft_out = fft.fftshift(fft.fft(ifftout))
                    
                    self.H_LS[m,:,nr, nt] = fft_out

    def comp_H_LS_freq_offset(self,freq_offset):
        """ compensate H_LS freq offset
        freq offset compensation happen on time domain
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape

        ifftsize = 4096 #
        td_sample_rate = ifftsize * scs * 1000

        RSSymMap = self.RS_info["RSSymMap"]
        RS_sym_timing_offset = self.symbols_timing_offset_list[RSSymMap]

        for m in range(sym_num):
            sym_timingoffset = RS_sym_timing_offset[m] + np.arange(ifftsize)/td_sample_rate
            phase_correct = np.exp(-1j*2*np.pi*freq_offset*sym_timingoffset)
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_H_LS = self.H_LS[m,:,nr, nt]
                    start_pos = (ifftsize - RE_distance*RE_num) // 2
                    
                    ifftin = np.zeros(ifftsize, 'c8')
                    ifftin[start_pos : start_pos+RE_distance*RE_num : RE_distance] = sel_H_LS
                    ifftout = fft.ifft(fft.ifftshift(ifftin))

                    ifftout *= phase_correct

                    fft_out = fft.fftshift(fft.fft(ifftout))
                    
                    self.H_LS[m,:,nr, nt] = fft_out[start_pos : start_pos+RE_distance*RE_num : RE_distance]       

    def comp_pdsch_freq_offset(self,pdsch_resource,pdsch_start_sym,freq_offset):
        """compensate pdsch resource freq offset
        """
        scs = self.RS_info["scs"]
        NrOfSymbols,RE_num,Nr = pdsch_resource.shape

        ifftsize = 4096 #
        td_sample_rate = ifftsize * scs * 1000

        for m in range(NrOfSymbols):
            sym_timingoffset = self.symbols_timing_offset_list[m+pdsch_start_sym] + np.arange(ifftsize)/td_sample_rate
            phase_correct = np.exp(-1j*2*np.pi*freq_offset*sym_timingoffset)
            for nr in range(Nr):
                sel_data = pdsch_resource[m,:,nr]
                start_pos = (ifftsize - RE_num) // 2
                    
                ifftin = np.zeros(ifftsize, 'c8')
                ifftin[start_pos : start_pos+RE_num ] = sel_data
                ifftout = fft.ifft(fft.ifftshift(ifftin))

                ifftout *= phase_correct

                fft_out = fft.fftshift(fft.fft(ifftout))
                pdsch_resource[m,:,nr] = fft_out[start_pos : start_pos+RE_num]
        
        return pdsch_resource

    def DFT_channel_estimate(self):
        """ 
        H_LS data shall be after TA compensation to make sure master path TA = 0
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #for time domain IDFT output, path is in the range of [0:L_sym_left] and [L_sym_right:end]
        #the data in the middle is assumed to be noise
        L_symm_left_in_ns = self.CE_config["L_symm_left_in_ns"]
        L_symm_right_in_ns = self.CE_config["L_symm_right_in_ns"]
        eRB = self.CE_config["eRB"] #number of extra eRB added on each side
        eK = eRB * 12 // RE_distance #nuber of added RS RE on each side

        H_LS = self.H_LS       
        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape
        
        #after add extra points on both side, the sequence size should be even to make fft works correctly.
        right_eK = eK + (RE_num + eK) % 2
        
        if (RE_num * RE_distance // 12) == 1:
            #do not support one PRB assignment
            assert 0
        
        #init
        H_est = np.zeros((sym_num, RE_num*RE_distance,Nr,Nt),'c8')
        
        #DFT channel est and interpolation to get each subcarrier H estimation for every [nr,nt]pair and every RS symbol
        for m in range(sym_num):
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_HLS = H_LS[m,:,nr, nt]
                    #1. linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
                    H_LS_with_extra = _HLS_extra(sel_HLS, eK,right_eK, RE_distance)
                                        
                    #2. ifft to time domain
                    #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
                    h_sym = fft.ifft(fft.ifftshift(H_LS_with_extra))*np.sqrt(H_LS_with_extra.size)

                    #sample rate of h_sym 
                    h_sym_sample_rate_in_hz = scs * 1000 * RE_distance * H_LS_with_extra.size
                    
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

                    #5. (RE_distance-1) times zero padding, in this way, dft result subcarrier frequency rate = scs
                    extended_h_sym = np.concatenate((h_sym, np.zeros(h_sym.size*(RE_distance-1), 'c8')))

                    #6. dft to freq 
                    dft_o = fft.fftshift(fft.fft(extended_h_sym))/np.sqrt(extended_h_sym.size)

                    #7， remove extra interpolation points and get H estimation for each RE
                    #need multiply np.sqrt(RE_distance) to compensate sample reduction
                    H_est_result =dft_o[eK*RE_distance : eK*RE_distance + RE_distance*RE_num] * np.sqrt(RE_distance)
                    H_est[m,:,nr,nt] = H_est_result                    
        
        #time domain interpolation to gen 14 symbol channel est result
        H_result = _H_est_interpolate_to_14_symbol(H_est,self.RS_info["RSSymMap"])
        
        #estimate noise and interference covariance matrix
        extended_cov_m = _cov_m_estimate(self.H_LS, H_est,RE_distance, self.RS_info["NumCDMGroupsWithoutData"],self.RS_info["RSSymMap"])
        
        return H_result, extended_cov_m
        
    def DFT_symmetric_channel_estimate(self):
        """ based on "DFT-Based Channel Estimation with Symmetric Extension for OFDMA Systems" by Yi Wang, Lihua Li, Ping Zhang & Zemin Liu 
        https://jwcn-eurasipjournals.springeropen.com/articles/10.1155/2009/647130
        and it also need extra processing to support 5G channel estimation

        H_LS data shall be after TA compensation to make sure master path TA = 0
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #for time domain IDFT output, path is in the range of [0:L_sym_left] and [L_sym_right:end]
        #the data in the middle is assumed to be noise
        L_symm_left_in_ns = self.CE_config["L_symm_left_in_ns"]
        L_symm_right_in_ns = self.CE_config["L_symm_right_in_ns"]
        eRB = self.CE_config["eRB"] #number of extra eRB added on each side
        eK = eRB * 12 // RE_distance #nuber of added RS RE on each side
        
        H_LS = self.H_LS

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape
        
        #after add extra points on both side, the sequence size should be even to make fft works correctly.
        right_eK = eK + (RE_num + eK) % 2
        
        if (RE_num * RE_distance // 12) == 1:
            #do not support one PRB assignment
            assert 0

        #init
        H_est = np.zeros((sym_num, RE_num*RE_distance,Nr,Nt),'c8')
                
        #DFT channel est and interpolation to get each subcarrier H estimation for every [nr,nt]pair and every RS symbol
        for m in range(sym_num):
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_HLS = H_LS[m,:,nr, nt]
                    
                    #1. linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
                    H_LS_with_extra = _HLS_extra(sel_HLS, eK,right_eK, RE_distance)

                    #2. symmetric extension to H_LS_sym
                    H_LS_sym = np.zeros(2*(RE_num + eK + right_eK),'c8')                  
                    H_LS_sym[0:H_LS_with_extra.size] = H_LS_with_extra
                    H_LS_sym[H_LS_with_extra.size:] = H_LS_with_extra[-1::-1]
                    
                    #4. ifft to time domain
                    #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
                    h_sym = fft.ifft(fft.ifftshift(H_LS_sym))*np.sqrt(H_LS_sym.size)

                    #5.get L_left and L_right in sample
                    # assume all path signal could exist in [0,L_left] and [2048-L_right, 2048] range
                    # [L_left, 2048-L_right] are pure noise
                    h_sym_sample_rate_in_hz = H_LS_sym.size * scs * 1000 * RE_distance

                    L_left = int(L_symm_left_in_ns /( 10**9/h_sym_sample_rate_in_hz))
                    #for symmetric method, taps in time domain also symmetric extended on right side,
                    # L_right should be equal to L_left
                    L_left = min(h_sym.size // 3 + h_sym.size // 16,L_left)
                    L_right = L_left

                    #6. first noise power est
                    first_noise_power = np.mean(np.abs(h_sym[L_left:h_sym.size-L_right])**2)

                    #7 remove noise in h_sym 
                    #(1) all the signals that 30dB lower than peak signal is regarded as noise - it has issues
                    # (2) all the signals that are lower than first noise power is regarded as noise 
                    # (3)h_sym[L_left:2048-L_right] is regarded as noise
                    
                    h_sym[np.abs(h_sym) < np.sqrt(first_noise_power/2)] = 0
                    h_sym[L_left:h_sym.size-L_right] = 0

                    #8. -- (RE_distance-1) times zero padding, in this way, dft result subcarrier frequency rate = scs, --  has issue
                    #-- can not do zero padding interpolation for symmetric DFT
                    #extended_h_sym = np.concatenate((h_sym, np.zeros(h_sym.size*(RE_distance-1), 'c8')))

                    #9. dft to freq 
                    dft_o = fft.fftshift(fft.fft(h_sym))/np.sqrt(h_sym.size)

                    #10. symmetric combination
                    first_sample = dft_o[0:dft_o.size//2]
                    second_sample = dft_o[-1:-dft_o.size//2-1:-1]
                    
                    #combined H is final H estimation
                    H_comb = (first_sample + second_sample)/2 

                    #interpolation by idft+zero padding + dft
                    idft_o = fft.ifft(fft.ifftshift(H_comb))*np.sqrt(H_comb.size)
                    
                    extended_v = np.concatenate((idft_o, np.zeros(idft_o.size*(RE_distance-1), 'c8')))

                    dft_o2 = fft.fftshift(fft.fft(extended_v))/np.sqrt(extended_v.size) * np.sqrt(RE_distance)


                    H_est[m,:,nr,nt] = dft_o2[eK*RE_distance : eK*RE_distance + RE_num*RE_distance]
                    
        #time domain interpolation to gen 14 symbol channel est result
        H_result = _H_est_interpolate_to_14_symbol(H_est,self.RS_info["RSSymMap"])
        
        #estimate noise and interference covariance matrix
        extended_cov_m = _cov_m_estimate(self.H_LS, H_est,RE_distance, self.RS_info["NumCDMGroupsWithoutData"],self.RS_info["RSSymMap"])
        
        return H_result, extended_cov_m

    def DCT_channel_estimate(self):
        """ 
        H_LS data shall be after TA compensation to make sure master path TA = 0
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #for time domain IDFT output, path is in the range of [0:L_sym_left] and [L_sym_right:end]
        #the data in the middle is assumed to be noise
        L_symm_left_in_ns = self.CE_config["L_symm_left_in_ns"]
        L_symm_right_in_ns = self.CE_config["L_symm_right_in_ns"]
        eRB = self.CE_config["eRB"] #number of extra eRB added on each side
        eK = eRB * 12 // RE_distance #nuber of added RS RE on each side

        H_LS = self.H_LS       
        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape
        
        #after add extra points on both side, the sequence size should be even to make fft works correctly.
        right_eK = eK + (RE_num + eK) % 2
        
        if (RE_num * RE_distance // 12) == 1:
            #do not support one PRB assignment
            assert 0
        
        #init
        H_est = np.zeros((sym_num, RE_num*RE_distance,Nr,Nt),'c8')
        
        #DFT channel est and interpolation to get each subcarrier H estimation for every [nr,nt]pair and every RS symbol
        for m in range(sym_num):
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_HLS = H_LS[m,:,nr, nt]
                    #1. linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
                    H_LS_with_extra = _HLS_extra(sel_HLS, eK,right_eK, RE_distance)
                                        
                    #2. dct to time domain
                    h_sym = fft.dct(H_LS_with_extra,norm="ortho")

                    #sample rate of h_sym 
                    h_sym_sample_rate_in_hz = scs * 1000 * RE_distance * H_LS_with_extra.size
                    
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

                    #5. (RE_distance-1) times zero padding, in this way, dft result subcarrier frequency rate = scs
                    extended_h_sym = np.concatenate((h_sym, np.zeros(h_sym.size*(RE_distance-1), 'c8')))

                    #6. idct to freq 
                    dft_o = fft.idct(extended_h_sym,norm="ortho")

                    #7， remove extra interpolation points and get H estimation for each RE
                    #need multiply np.sqrt(RE_distance) to compensate sample reduction
                    H_est_result =dft_o[eK*RE_distance : eK*RE_distance + RE_distance*RE_num] * np.sqrt(RE_distance)
                    H_est[m,:,nr,nt] = H_est_result                    
        
        #time domain interpolation to gen 14 symbol channel est result
        H_result = _H_est_interpolate_to_14_symbol(H_est,self.RS_info["RSSymMap"])
        
        #estimate noise and interference covariance matrix
        extended_cov_m = _cov_m_estimate(self.H_LS, H_est,RE_distance, self.RS_info["NumCDMGroupsWithoutData"],self.RS_info["RSSymMap"])
        
        return H_result, extended_cov_m
    
    def DCT_symmetric_channel_estimate(self):
        """ based on "DFT-Based Channel Estimation with Symmetric Extension for OFDMA Systems" by Yi Wang, Lihua Li, Ping Zhang & Zemin Liu 
        https://jwcn-eurasipjournals.springeropen.com/articles/10.1155/2009/647130
        and it also need extra processing to support 5G channel estimation

        H_LS data shall be after TA compensation to make sure master path TA = 0
        """
        RE_distance = self.RS_info["RE_distance"]
        scs = self.RS_info["scs"]

        #for time domain IDFT output, path is in the range of [0:L_sym_left] and [L_sym_right:end]
        #the data in the middle is assumed to be noise
        L_symm_left_in_ns = self.CE_config["L_symm_left_in_ns"]
        L_symm_right_in_ns = self.CE_config["L_symm_right_in_ns"]
        eRB = self.CE_config["eRB"] #number of extra eRB added on each side
        eK = eRB * 12 // RE_distance #nuber of added RS RE on each side
        H_LS = self.H_LS

        #number of DMRS symbol, number of DMRS RE in one symbol, number of Rx ant, number of Tx layer
        sym_num, RE_num,Nr,Nt = self.H_LS.shape
        
        #after add extra points on both side, the sequence size should be even to make fft works correctly.
        right_eK = eK + (RE_num + eK) % 2
        
        if (RE_num * RE_distance // 12) == 1:
            #do not support one PRB assignment
            assert 0

        #init
        H_est = np.zeros((sym_num, RE_num*RE_distance,Nr,Nt),'c8')
                
        #DFT channel est and interpolation to get each subcarrier H estimation for every [nr,nt]pair and every RS symbol
        for m in range(sym_num):
            for nt in range(Nt):
                for nr in range(Nr):
                    sel_HLS = H_LS[m,:,nr, nt]
                    
                    #1. linear interpolation to generate extra points on both side of H_LS, to avoid the interference from other edge data
                    H_LS_with_extra = _HLS_extra(sel_HLS, eK,right_eK, RE_distance)

                    #2. symmetric extension to H_LS_sym
                    H_LS_sym = np.zeros(2*(RE_num + eK + right_eK),'c8')                  
                    H_LS_sym[0:H_LS_with_extra.size] = H_LS_with_extra
                    H_LS_sym[H_LS_with_extra.size:] = H_LS_with_extra[-1::-1]
                    
                    #4. ifft to time domain
                    #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
                    h_sym = fft.dct(H_LS_sym,norm="ortho")

                    #5.get L_left and L_right in sample
                    # assume all path signal could exist in [0,L_left] and [2048-L_right, 2048] range
                    # [L_left, 2048-L_right] are pure noise
                    h_sym_sample_rate_in_hz = H_LS_sym.size * scs * 1000 * RE_distance

                    L_left = int(L_symm_left_in_ns /( 10**9/h_sym_sample_rate_in_hz))
                    L_right = int(L_symm_right_in_ns /( 10**9/h_sym_sample_rate_in_hz))
                    
                    #6. first noise power est
                    first_noise_power = np.mean(np.abs(h_sym[L_left:h_sym.size-L_right])**2)

                    #7 remove noise in h_sym 
                    #(1) all the signals that 30dB lower than peak signal is regarded as noise - it has issues
                    # (2) all the signals that are lower than first noise power is regarded as noise 
                    # (3)h_sym[L_left:2048-L_right] is regarded as noise
                    
                    #h_sym[np.abs(h_sym) < np.sqrt(first_noise_power/2)] = 0
                    h_sym[L_left:h_sym.size-L_right] = 0

                    #8. -- (RE_distance-1) times zero padding, in this way, dft result subcarrier frequency rate = scs, --  has issue
                    #-- can not do zero padding interpolation for symmetric DFT
                    #extended_h_sym = np.concatenate((h_sym, np.zeros(h_sym.size*(RE_distance-1), 'c8')))

                    #9. dft to freq 
                    dft_o = fft.idct(h_sym,norm="ortho")

                    #10. symmetric combination
                    first_sample = dft_o[0:dft_o.size//2]
                    second_sample = dft_o[-1:-dft_o.size//2-1:-1]
                    
                    #combined H is final H estimation
                    H_comb = (first_sample + second_sample)/2 

                    #interpolation by idft+zero padding + dft
                    idft_o = fft.dct(H_comb,norm="ortho")
                    
                    extended_v = np.concatenate((idft_o, np.zeros(idft_o.size*(RE_distance-1), 'c8')))

                    dft_o2 = fft.idct(extended_v,norm="ortho") * np.sqrt(RE_distance)

                    H_est[m,:,nr,nt] = dft_o2[eK*RE_distance : eK*RE_distance + RE_num*RE_distance]
                    
        #time domain interpolation to gen 14 symbol channel est result
        H_result = _H_est_interpolate_to_14_symbol(H_est,self.RS_info["RSSymMap"])
        
        #estimate noise and interference covariance matrix
        extended_cov_m = _cov_m_estimate(self.H_LS, H_est,RE_distance, self.RS_info["NumCDMGroupsWithoutData"],self.RS_info["RSSymMap"])
        
        return H_result, extended_cov_m
    
def _HLS_extra(sel_HLS, eK,right_eK, RE_distance):
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

def _H_est_interpolate_to_14_symbol(H_est,RSSymMap):
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

def _cov_m_estimate(H_LS, H_est,RE_distance, NumCDMGroupsWithoutData,RSSymMap):
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

def cal_carrier_relative_freq_offset(TO_values, timing_durations):
    """ this function is to estimate transmittor and reciever relative frequecy offset rho
    non-zero rho will cause (1) timing shift on each slot and each symbol in the slot (2) frequency offset between transmittore and receiver.
    the total frequency offset between transmittore and receiver is the combination of doppler freq and carrier freq offset.
    the freq offset estimation can be differ it is doppler offset or carrier offset,
    timing shift is the only useful info to estimate rho value/
    rho value is usually in the range of 1ppm to 0.01ppm
    timing offset estimation error is high comparing with smalle rho value, so using timing difference estimation among RS symbols in the same slot to estimate rho value would get very high error.

    it is better to use multiple slot timing estimation values to estimate rho value
    input:
    TO_values: timing offset estimation values from multiple slots
    timing_durations: timing duration for each TO values to the beginning of the data

    for example, assume scs 30KHz 2 slots data, with each slot has two RS symbol(2,11)
    symbol 2 to the beginning of the slot timing duration is 7.421875e-05 second, symbol 11 is 0.0003953125 seconds
    one slot length is 0.0005 seconds
    TO_values include TO estimation for: slot 0 RS 2, slot 0 RS 11, slot 1 RS2, slot 1 RS 11
    timing_duarations are: 7.421875e-05, 0.0003953125,0.0005+7.421875e-05, 0.0005+0.0003953125

    output:
    rho: relative frequency offset
    """
    
    # timing offset for each symbol is rho * timing offset
    #LLS method is used to estimate tho

    assert TO_values.size == timing_durations.size
    N = TO_values.size

    #gen X martrix used for LLS
    #assume three RS symbol  X = [[1,  1, 1, 1.........,  1];
    #                           [sym_timingoffset 0, sym_timingoffset 1, sym_timingoffset 2]]
    X = np.array([[1]*N, timing_durations])
    W = np.linalg.inv(X @ X.T) @ X #W is 2 by N matrix

    rho = W[1,:] @ TO_values.T
    
    return rho

if __name__ == "__main__":
    #
    if 0:
        from tests.channel_estimate import test_nr_pdsch_timing_freq_offset
        file_lists = test_nr_pdsch_timing_freq_offset.get_testvectors()
        count = 1
        for filename in file_lists:
            #filename = "tests/nr_pdsch/testvectors/nrPDSCH_testvec_24_scs_15khz_BW_25_mcstable_1_iMCS.mat"
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            #test_nr_pdsch_timing_freq_offset.test_nr_pdsch_timing_offset_est_and_comp_with_channel_filter(filename)
            #test_nr_pdsch_timing_freq_offset.test_nr_pdsch_freq_offset_est_no_channel_filter(filename)
            test_nr_pdsch_timing_freq_offset.test_nr_pdsch_freq_offset_est_with_channel_filter(filename)
            #test_nr_pdsch_timing_freq_offset.test_nr_pdsch_timing_offset_comp_no_channel_filter(filename)
            #test_nr_pdsch_timing_freq_offset.test_nr_pdsch_freq_offset_comp_no_channel_filter(filename)
    
    if 0:
        from tests.channel_estimate import test_nr_pdsch_channel_estimation_AWGN
        pdsch_channel_est_testvectors_list = test_nr_pdsch_channel_estimation_AWGN.get_pdsch_channel_est_testvectors()
        CE_config_list = test_nr_pdsch_channel_estimation_AWGN.get_CE_config_list()
        count = 1
        for pdsch_channel_est_testvectors in pdsch_channel_est_testvectors_list:
            for CE_config in CE_config_list:
                CE_config = CE_config_list[0]
                print(f"test channel est, count= {count}")
                count += 1
                #if count < 217:
                #    continue
                
                test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_no_TO_FO(pdsch_channel_est_testvectors,CE_config)
                #test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_TO_FO(pdsch_channel_est_testvectors,CE_config)
                #test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_rho(pdsch_channel_est_testvectors,CE_config)
    
    if 1:
        from tests.channel_estimate import test_nr_pdsch_channel_estimation_TDL_channel
        pdsch_channel_est_testvectors_list = test_nr_pdsch_channel_estimation_TDL_channel.get_pdsch_channel_est_testvectors()
        CE_config_list = test_nr_pdsch_channel_estimation_TDL_channel.get_CE_config_list()
        count = 1
        for pdsch_channel_est_testvectors in pdsch_channel_est_testvectors_list:
            for CE_config in CE_config_list:
                CE_config = CE_config_list[0]
                print(f"test channel est, count= {count}")
                count += 1
                #if count < 86:
                #    continue
                
                #test_nr_pdsch_channel_estimation_TDL_channel.test_nr_pdsch_channel_est_TDL_low_corelation_no_TO_no_rho_no_fm(pdsch_channel_est_testvectors,CE_config)
                test_nr_pdsch_channel_estimation_TDL_channel.test_nr_pdsch_channel_est_TDL_all(pdsch_channel_est_testvectors,CE_config)
    
    if 0:
        from tests.channel_estimate import test_nr_pdsch_channel_estimation_one_tap_channel
        pdsch_channel_est_testvectors_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_pdsch_channel_est_testvectors()
        CE_config_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_CE_config_list()
        count = 1
        for pdsch_channel_est_testvectors in pdsch_channel_est_testvectors_list:
            for CE_config in CE_config_list:
                CE_config = CE_config_list[0]
                print(f"test channel est, count= {count}")
                count += 1
                #if count < 86:
                #    continue
                
                test_nr_pdsch_channel_estimation_one_tap_channel.test_nr_pdsch_channel_est_single_tap_4(pdsch_channel_est_testvectors,CE_config)
                
        