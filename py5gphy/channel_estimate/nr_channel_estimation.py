# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft

from py5gphy.common import nr_slot
from py5gphy.channel_estimate import dft_dct_CE
from py5gphy.channel_estimate import dft_dct_symmetric_CE

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

        if "freq_intp_method" not in CE_config:
            CE_config["freq_intp_method"] = "linear"
        if "timing_intp_method" not in CE_config:
            CE_config["timing_intp_method"] = "linear"

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
            H_result, cov_m = dft_dct_CE.DFT_DCT_channel_estimate(self.H_LS,self.RS_info,self.CE_config,"DFT")
        elif self.CE_config["CE_algo"] == "DFT_symmetric":
            H_result, cov_m =  dft_dct_symmetric_CE.DFT_DCT_symmetric_channel_estimate(self.H_LS,self.RS_info,self.CE_config,"DFT")
        elif self.CE_config["CE_algo"] == "DCT":
            H_result, cov_m =  dft_dct_CE.DFT_DCT_channel_estimate(self.H_LS,self.RS_info,self.CE_config,"DCT")
        elif self.CE_config["CE_algo"] == "DCT_symmetric":
            H_result, cov_m = dft_dct_symmetric_CE.DFT_DCT_symmetric_channel_estimate(self.H_LS,self.RS_info,self.CE_config,"DCT")
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
        pdsch_carrier_testvectors_list = test_nr_pdsch_channel_estimation_AWGN.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_channel_estimation_AWGN.get_channel_parameter_list()
        CE_config_list = test_nr_pdsch_channel_estimation_AWGN.get_CE_config_list()
        CEQ_algo_list = test_nr_pdsch_channel_estimation_AWGN.get_channel_equ_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for channel_parameter in channel_parameter_list:
                for CEQ_algo in CEQ_algo_list:
                    for CE_config in CE_config_list:
                        #print(f"test channel est, count= {count}")
                        count += 1
                
                        #test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_no_TO_FO(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config)
                        #test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_FO(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config)
                        test_nr_pdsch_channel_estimation_AWGN.test_nr_pdsch_channel_est_AWGN_rho(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config)
    
    if 0:
        from tests.channel_estimate import test_nr_pdsch_channel_estimation_one_tap_channel
        pdsch_carrier_testvectors_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_channel_parameter_list()
        CE_config_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_CE_config_list()
        CEQ_algo_list = test_nr_pdsch_channel_estimation_one_tap_channel.get_channel_equ_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for channel_parameter in channel_parameter_list:
                for CEQ_algo in CEQ_algo_list:
                    for CE_config in CE_config_list:
                        #print(f"test channel est, count= {count}")
                        count += 1
                        
                        test_nr_pdsch_channel_estimation_one_tap_channel.test_nr_pdsch_channel_est_single_tap(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config)
    
    if 1:
        from tests.channel_estimate import test_nr_pdsch_channel_estimation_TDL_channel
        pdsch_carrier_testvectors_list = test_nr_pdsch_channel_estimation_TDL_channel.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_channel_estimation_TDL_channel.get_channel_parameter_list()
        CE_config_list = test_nr_pdsch_channel_estimation_TDL_channel.get_CE_config_list()
        CEQ_algo_list = test_nr_pdsch_channel_estimation_TDL_channel.get_channel_equ_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for channel_parameter in channel_parameter_list:
                for CEQ_algo in CEQ_algo_list:
                    for CE_config in CE_config_list:
                        #print(f"test channel est, count= {count}")
                        count += 1
                        
                        test_nr_pdsch_channel_estimation_TDL_channel.test_nr_pdsch_channel_est_TDL_basic(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config)
    