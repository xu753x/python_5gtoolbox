# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy.signal import upfirdn
from scipy.signal import remez
import json

from py5gphy.common import nr_slot

def waveform_rx_processing(rx_waveform, carrier_config,sample_rate_in_hz):
    """ Rx waveform processing,
    return freq domain IQ data
    """
    #FIR filter and downsample
    td_waveform = channel_filter(rx_waveform, carrier_config,sample_rate_in_hz)

    #get number of slot
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    samples_in_one_slot = int(fftsize*15)
    num_slots = td_waveform.shape[1] // samples_in_one_slot
    

    fd_waveform = np.zeros((td_waveform.shape[0],num_slots*carrier_prb_size*12*14),'c8')
    for slot in range(num_slots):
        td_slot = td_waveform[:,slot*samples_in_one_slot:(slot+1)*samples_in_one_slot]
        fd_slot = Rx_low_phy(td_slot, carrier_config)
        fd_waveform[:,slot*carrier_prb_size*12*14:(slot+1)*carrier_prb_size*12*14] = fd_slot
    
    return td_waveform,fd_waveform

def Rx_low_phy(td_slot, carrier_config):
    """ handle TX data processing, including
    phase correction, half-CP removal, FFT and timing correction
    1. based on 38.2115.4, each symbolk need phase compensation, receiving side need phase correction
    2. half-CP removel: time domain symbol data is CP+data, while the last few samples in data domain could mix with next symbol data
        the reason could be A: (both Tx and Rx filter) B: Rx timing error
        to avoid this data interference, receiver usually choose the second half of CP data and first [N-1/2 CP size] data to do FFT
    after FFT, symbol data need phase compensation to compensate 1/2 CP timing offset

    input:
    td_slot: one slot of time domain data
    output:
    fd_slot: one slot of frequency domain data
    """
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    
    Nr = carrier_config["Nr"]
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]

    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    assert fftsize in [128,256,512,1024,2048,4096]
    sample_rate_in_hz = fftsize * scs * 1000

    #get cp table
    #CP size
    ifft4096_scs30_cp_list = np.array([352] + [288]*13)
    ifft4096_scs15_cp_list = np.array([320] + [288]*6 + [320] + [288]*6 )

    if scs == 15:
        cptable = ifft4096_scs15_cp_list / (4096 / fftsize)
    else:
        cptable = ifft4096_scs30_cp_list / (4096 / fftsize)
    cptable = cptable.astype(int)
    half_short_cp_size = cptable[1] // 2
    
    #phase compensation vector to compensate half_short_cp_size timing advance
    phase_vec = np.exp(1j * 2 * np.pi * half_short_cp_size / fftsize * np.arange(fftsize))

    fd_slot = np.zeros((Nr,carrier_prb_size*12*14), 'c8')

    td_offset = 0
    for sym in range(14):
        # phase correction
        td_sym = td_slot[:, td_offset : td_offset+cptable[sym]+fftsize]
        if central_freq_in_hz:
            #phase compensation only when central_freq_in_hz nonzero
            delta = central_freq_in_hz / sample_rate_in_hz
            td_sym = td_sym * np.exp(1j * 2 * np.pi * delta * (td_offset + cptable[sym]))
        
        td_offset += cptable[sym]+fftsize
        #choose last 1/2*short-CP length of CP and first (fftsize - 1/2*short-CP length) data for FFT
        sel_td_sym = td_sym[:,cptable[sym]-half_short_cp_size : cptable[sym]-half_short_cp_size+fftsize]
        #fftshift is to move zero frequency data to the center of the array
        #FFT out power is N time higher than total FFT input power, the fftout need divide by sqrt(ifftsize)
        fft_out = fft.fftshift(fft.fft(sel_td_sym,axis=1))/np.sqrt(fftsize)

        #phase compensation to compensate half_short_cp_size timing advance
        new_fft_out = fft_out * phase_vec
        fd_slot[:, carrier_prb_size*12*sym:carrier_prb_size*12*(sym+1)] = \
            new_fft_out[:,(fftsize-carrier_prb_size*12) // 2:(fftsize-carrier_prb_size*12) // 2 + carrier_prb_size*12]
    
    return fd_slot

def channel_filter(rx_waveform, carrier_config,sample_rate_in_hz):
    """ filter and downsample
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    out_sample_rate_in_hz = fftsize * scs*1000
    oversample_rate = int(sample_rate_in_hz/out_sample_rate_in_hz)

    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    #below parameter comes from HB filter searching test by calling searching_HB_filter for different BW and scs
    HB_numtaps = 55
    HB_Fpass = 0.21
    
    halfband_filtercoeff = remez(HB_numtaps, [0, HB_Fpass, 0.5-HB_Fpass, 0.5], [1,0])
    
    #half band filter to downsaple
    #number of half band filter
    assert int(np.log2(oversample_rate)) == np.log2(oversample_rate)
    reps = int(np.log2(oversample_rate))
    #offset = int(halfband_filtercoeff.size // 2 )
    #for dowmnsample by 2, the filter output length = input len + (halfband_filtercoeff//2)
    #offset should be (halfband_filtercoeff.size+1) // 4 to make sure no sample offset movement
    offset = int((halfband_filtercoeff.size+1) // 4 )
        
    for _ in range(reps):
        input_size = rx_waveform.shape[1]
        #for both updample nu 2 tx half band filter and dowmsaple by 2 rx halfband filter, the output need multiple sqrt(2), to make H_LS and added noise power have no change
        rx_waveform = upfirdn(halfband_filtercoeff, rx_waveform, down=2) * np.sqrt(2)
        rx_waveform = rx_waveform[:,offset : offset + input_size // 2]
    
    #FIR filter
    #generate FIR coefficient
    #get Fpass and Fstop in hz
    Fpass = ((carrier_prb_size*12*scs + scs / 2) * 1000)/2
    Fstop = BW*(10**6)/2
    
    #below FIR filter numtaps comes from searching_fir_filter result
    FIR_numtaps_list = {
        #[scs,BW]:FIR_numtaps
        (30,100):287,(30,90):287,(30,80):287,(30,70):287,(30,60):287,
        (30,50):143,(30,45):143,(30,40):143,(30,35):143,(30,30):143,
        (30,25):71,(30,20):71,(30,15):87,(30,10):45,(30,5):27,
        (15,5):51,(15,10):87,(15,15):153,(15,20):143,(15,25):143,
        (15,30):287,(15,35):287,(15,40):287,(15,45):287,(15,50):287,
    }
    
    if (scs,BW) in FIR_numtaps_list:
        FIR_numtaps = FIR_numtaps_list[(scs,BW)]
    else:
        FIR_numtaps = 287

    filter_coeff = remez(FIR_numtaps, [0, Fpass, Fstop, out_sample_rate_in_hz/2], [1,0],fs=out_sample_rate_in_hz)

    #FIR filter with oversample rate =1, 
    input_size = rx_waveform.shape[1]
    td_waveform = upfirdn(filter_coeff, rx_waveform)
    offset = int(filter_coeff.size // 2 )
    td_waveform = td_waveform[:,offset : offset + input_size]

    return td_waveform

#below method is used for searching HB parameter
def HB_channel_filter(in_waveform, carrier_config,is_tx,oversample_num,HBnumtaps,HBFpass):
    """ used to find optimized halfband filter coefficient
        is_tx: True: for Tx and HB does upsample by 2, False: Rx and HB downsample by 2
        oversample_num: each halfband filter in Rx side decimate input by 2, this is the number of decimation or interpolation
        numtaps: number of HF taps
        Fpass: passband, should be less than 0.25
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    out_sample_rate_in_hz = fftsize * scs*1000
    
    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    halfband_filtercoeff = remez(HBnumtaps, [0, HBFpass, 0.5-HBFpass, 0.5], [1,0])

    if is_tx:
        #Tx,interpolation
        tx_waveform = in_waveform
        offset = int(halfband_filtercoeff.size // 2 ) - 1

        for _ in range(oversample_num):
            input_size = tx_waveform.shape[1]
            tx_waveform = upfirdn(halfband_filtercoeff, tx_waveform, up=2)*np.sqrt(2)
            tx_waveform = tx_waveform[:,offset : offset + 2*input_size]
        
        return tx_waveform
    else:
        #Rx, decimatation
        rx_waveform = in_waveform
        #half band filter to downsample
        #for dowmnsample by 2, the filter output length = input len + (halfband_filtercoeff//2)
        #offset should be (halfband_filtercoeff.size+1) // 4 to make sure no sample offset movement
        offset = int((halfband_filtercoeff.size+1) // 4 )
        
        for _ in range(oversample_num):
            input_size = rx_waveform.shape[1]
            rx_waveform = upfirdn(halfband_filtercoeff, rx_waveform, down=2)*np.sqrt(2)
            rx_waveform = rx_waveform[:,offset : offset + input_size // 2]
        
        return rx_waveform

#below method is used for searching FIR parameter
def tx_rx_FIR_filter(in_waveform, carrier_config,fir_numtaps):
    """ used to find optimized halfband filter coefficient
        decimation_number: each halfband filter in Rx side decimate input by 2, this is the number of decimation
        numtaps: number of HF taps
        Fpass: passband, should be less than 0.25
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    out_sample_rate_in_hz = fftsize * scs*1000
        
    #generate FIR coefficient
    #get Fpass and Fstop in hz
    Fpass = ((carrier_prb_size*12*scs + scs / 2) * 1000)/2
    Fstop = BW*(10**6)/2
    filter_coeff = remez(fir_numtaps, [0, Fpass, Fstop, out_sample_rate_in_hz/2], [1,0],fs=out_sample_rate_in_hz)

    #FIR filter with oversample rate =1, 
    input_size = in_waveform.shape[1]
    out_td_waveform = upfirdn(filter_coeff, in_waveform)
    offset = int(filter_coeff.size // 2 )
    out_td_waveform = out_td_waveform[:,offset : offset + input_size]

    return out_td_waveform

def searching_fir_filter(BW, scs):
    #searching FIR filter numof taps for for different BW, scs
    #method: send PDSCH data, then does H_LS estimation and timing offset measurement, noise estimation
    #test different pDSCH PRB allocation
    #the criteria to select FIR filter :
    #1. no timing shift, 2. H_LS flat enough, 3. low added noise
    
    #gen CE_config, not used for this test
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True,
        "L_symm_left_in_ns":100,"L_symm_right_in_ns":200,
        "eRB": 2}
    
    #carrier general config: 2T2R
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 2
    carrier_config["Nr"] = 2
    carrier_config["carrier_frequency_in_mhz"] = 3840 # with phase compensation
    carrier_config["scs"] = scs
    carrier_config["BW"] = BW
    carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )

    ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
        
    #pdsch general config: 2 aDMRS symbol, occupy from sym 2 to 13
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    pdsch_config['mcs_index'] = 1
    pdsch_config['num_of_layers'] = carrier_config["num_of_ant"]
    pdsch_config['DMRS']['nNIDnSCID'] = 1
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 1
    pdsch_config['DMRS']['DMRSAddPos'] = 1
    pdsch_config["precoding_matrix"] = np.empty(0)

    pdsch_config['StartSymbolIndex'] = 2
    pdsch_config['NrOfSymbols'] = 12
    pdsch_config['ResAlloType1']['RBStart'] = 0
    #pdsch_config['ResAlloType1']['RBSize'] = len(pdsch_tvcfg['PRBSet'])
   
    td_slotsize = ifftsize*15

    sample_rate_in_hz,CPs_size = nr_slot.get_sample_rate_and_CP_size(scs,BW)

    #choose FIR filter taps related to short CP size
    #FIR_numtaps_list = [CPs_size[1]//2-1, CPs_size[1]-1]
    default_FIR_numtaps = CPs_size[1] - 1 #short CP size - 1
    spec_FIR_numtaps_list = {
        # (scs,BW):taps
        (30,10):CPs_size[1]+9,(30,5):CPs_size[1]+9,(15,15):CPs_size[1]+9,
        (30,15):CPs_size[1]+15,(15,5):CPs_size[1]+15,(15,10):CPs_size[1]+15,
    }
    if (scs,BW) in spec_FIR_numtaps_list:
        FIR_numtaps = spec_FIR_numtaps_list[(scs,BW)]
    else:
        FIR_numtaps = default_FIR_numtaps

    FIR_numtaps_list = [FIR_numtaps]
    try_num = 1 #

    for FIR_numtaps in FIR_numtaps_list:
        for test_num in range(try_num):
            result = True
            for RBSize in [carrier_prb_size//4, carrier_prb_size//2, carrier_prb_size]:
                pdsch_config['ResAlloType1']['RBSize'] = RBSize
                nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)

                fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot    (carrier_config["num_of_ant"], carrier_prb_size)

                #PDSCH processing and DMRS processing
                fd_slot_data, RE_usage_inslot = nrPdsch.process(fd_slot_data,   RE_usage_inslot,0)

                #tx low phy processing: IFFT, add CP, phase compensation
                td_slot = tx_lowphy_process.Tx_low_phy(fd_slot_data,    carrier_config)

                #Tx FIR
                tx_td_waveform = tx_rx_FIR_filter(td_slot, carrier_config,FIR_numtaps)

                #RX filter
                rx_td_slot = tx_rx_FIR_filter(tx_td_waveform, carrier_config,FIR_numtaps)

                #rx low phy,FFT, phase de-compensation
                rx_fd_slot =  Rx_low_phy(rx_td_slot,carrier_config)                    

                #PDSCH channel LS estimation
                H_LS,RS_info = nrPdsch.H_LS_est(rx_fd_slot,slot=0)

                #channel est class
                nrChannelEstimation = \
                    nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)

                #timing offset est
                TO_est = nrChannelEstimation.timing_offset_est()

                #VAR est
                ant0_variance = np.var(H_LS[0,:,0,0])
                ant1_variance = np.var(H_LS[0,:,1,1])

                check_r = np.all(abs(TO_est*sample_rate_in_hz) < 1) and (10*np.log10(ant0_variance) < -32) and (10*np.log10(ant1_variance) < -32)
                if not check_r:
                    result = False
                    
                    
                    #print(f"test scs={scs},BW={BW},startPRB {startPRB},PRBSize{PRBSize},interpolation_num {interpolation_num} numtaps={numtaps},Fpass={Fpass},result={peak_pos == corr.size // 2}")
                
            #finish all PRB assignment
            if result:
                return [True,FIR_numtaps]

    return [False,0]

def searching_HB_filter(oversample_num, BW, scs):
    #searching HB filter numof taps and Fpass for for different BW, scs
    #method: send PDSCH data, then does H_LS estimation and timing offset measurement, noise estimation
    #test different pDSCH PRB allocation
    #the criteria to select FIR filter :
    #1. no timing shift, 2. H_LS flat enough, 3. low added noise
    
    #gen CE_config, not used for this test
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True,
        "L_symm_left_in_ns":100,"L_symm_right_in_ns":200,
        "eRB": 2}
    
    #carrier general config: 2T2R
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 2
    carrier_config["Nr"] = 2
    carrier_config["carrier_frequency_in_mhz"] = 3840 # with phase compensation
    carrier_config["scs"] = scs
    carrier_config["BW"] = BW
    carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )

    ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
        
    #pdsch general config: 2 aDMRS symbol, occupy from sym 2 to 13
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    pdsch_config['mcs_index'] = 1
    pdsch_config['num_of_layers'] = carrier_config["num_of_ant"]
    pdsch_config['DMRS']['nNIDnSCID'] = 1
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 1
    pdsch_config['DMRS']['DMRSAddPos'] = 1
    pdsch_config["precoding_matrix"] = np.empty(0)

    pdsch_config['StartSymbolIndex'] = 2
    pdsch_config['NrOfSymbols'] = 12
    pdsch_config['ResAlloType1']['RBStart'] = 0
    #pdsch_config['ResAlloType1']['RBSize'] = len(pdsch_tvcfg['PRBSet'])
   
    td_slotsize = ifftsize*15

    sample_rate_in_hz,CPs_size = nr_slot.get_sample_rate_and_CP_size(scs,BW)

    #choose FIR filter taps related to short CP size
    #below FIR filter numtaps comes from searching_fir_filter result
    default_FIR_numtaps = CPs_size[1] - 1 #short CP size - 1
    spec_FIR_numtaps_list = {
        # (scs,BW):taps
        (30,10):CPs_size[1]+9,(30,5):CPs_size[1]+9,(15,15):CPs_size[1]+9,
        (30,15):CPs_size[1]+15,(15,5):CPs_size[1]+15,(15,10):CPs_size[1]+15,
    }
    if (scs,BW) in spec_FIR_numtaps_list:
        FIR_numtaps = spec_FIR_numtaps_list[(scs,BW)]
    else:
        FIR_numtaps = default_FIR_numtaps

    HB_numtaps_list = [55,79]
    Fpass_maps = {
        55:[ 0.21,0.22, 0.23, 0.24],
        79:[0.21,0.225,0.23],
    }

    
    for HBnumtaps in HB_numtaps_list:
        Fpass_list = Fpass_maps[HBnumtaps]
        for HBFpass in Fpass_list:
            results = {}
            for RBSize in [carrier_prb_size//4, carrier_prb_size//2, carrier_prb_size]:
                pdsch_config['ResAlloType1']['RBSize'] = RBSize
                nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)

                fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot    (carrier_config["num_of_ant"], carrier_prb_size)

                #PDSCH processing and DMRS processing
                fd_slot_data, RE_usage_inslot = nrPdsch.process(fd_slot_data,   RE_usage_inslot,0)

                #tx low phy processing: IFFT, add CP, phase compensation
                td_slot = tx_lowphy_process.Tx_low_phy(fd_slot_data,    carrier_config)

                #Tx FIR
                tx_td_waveform = tx_rx_FIR_filter(td_slot, carrier_config,FIR_numtaps)

                #tx HB filter
                HB_waveform = HB_channel_filter(tx_td_waveform, carrier_config,True,oversample_num,HBnumtaps,HBFpass)

                #rx HB filter
                HB_out_waveform = HB_channel_filter(HB_waveform, carrier_config,False,oversample_num,HBnumtaps,HBFpass)

                #RX filter
                rx_td_slot = tx_rx_FIR_filter(HB_out_waveform, carrier_config,FIR_numtaps)

                #rx low phy,FFT, phase de-compensation
                rx_fd_slot =  Rx_low_phy(rx_td_slot,carrier_config)                    

                #PDSCH channel LS estimation
                H_LS,RS_info = nrPdsch.H_LS_est(rx_fd_slot,slot=0)

                #channel est class
                nrChannelEstimation = \
                    nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)

                #timing offset est
                TO_est = nrChannelEstimation.timing_offset_est()

                #VAR est
                ant0_variance = np.var(H_LS[0,:,0,0])
                ant1_variance = np.var(H_LS[0,:,1,1])

                check_r = np.all(abs(TO_est*sample_rate_in_hz) < 1) and (10*np.log10(ant0_variance) < -32) and (10*np.log10(ant1_variance) < -32)
                if check_r:
                    results[RBSize] = 1
                else:
                    results[RBSize] = 0
                                    
            #finish all PRB assignment
            if 0 not in results.values():
                return [True,HBnumtaps,HBFpass]

    return [False,0,0]

if __name__ == "__main__":
    from py5gphy.nr_lowphy import tx_lowphy_process
    from py5gphy.nr_pdsch import nr_pdsch
    from py5gphy.channel_estimate import nr_channel_estimation

    #search FIR taps for each BW and scs
    if 0:
        BW_scs_map = {15:[5,10,15,20,25,30,35,40,45,50],
                  30:[100,90,80,70,60,50,45,40,35,30,25,20,15,10,5]}
        #BW_scs_map = {15:[5,10],
        #          30:[15]}
        
        for scs  in [30, 15]:
            BW_list = BW_scs_map[scs]
            for BW in BW_list:
                result,FIR_numtaps = searching_fir_filter(BW, scs)
                print(f"searching_fir_filter,test scs={scs},BW={BW},result:{result} FIR_numtaps {FIR_numtaps}")
        
    # HB filter search 
    # searching result: HBnumtaps 55, HBFpass 0.21 is enough for all BW, scs
    if 0: #set to 1 to enable below code and 0 to bypass the code

        BW_scs_map = {15:[5,10,15,20,25,30,35,40,45,50],
                  30:[100,90,80,70,60,50,45,40,35,30,25,20,15,10,5]}
        for oversample_num in [8,1,2,4]:
            for scs  in [30, 15]:
                BW_list = BW_scs_map[scs]
                for BW in BW_list:
                    result,HBnumtaps,HBFpass = searching_HB_filter(oversample_num, BW, scs)

                    print(f"test scs={scs},BW={BW},oversample_num={oversample_num},result:{result} HBnumtaps {HBnumtaps}, HBFpass {HBFpass}")    
    
    if 0:
        # numTaps=55 and HBFpass=0.205 configuration is used in one of RU product, but it didn;t work for all BW and all PRB allocation
        for HBFpass in [0.205]:
            halfband_filtercoeff = remez(55, [0, HBFpass, 0.5-HBFpass, 0.5], [1,0])
            print(f"HBFpass={HBFpass},{halfband_filtercoeff[0]}, {halfband_filtercoeff[2]}")
    
    from tests.nr_lowphy import test_nr_rx_lowphy_process
    test_nr_rx_lowphy_process.test_rx_lowphy_1()
    test_nr_rx_lowphy_process.test_rx_lowphy_2()

    test_nr_rx_lowphy_process.test_channel_filter_1()

    test_nr_rx_lowphy_process.test_channel_filter_all()

    #test1: test timing offset compensation
    fft_size = 4096
    num_sc = 273*12
    
    #generate input random data
    rng = np.random.default_rng()
    in_d = rng.normal(0,10,num_sc) + 1j*rng.normal(0,10,num_sc)

    ifft_in =np.zeros((1,fft_size),'c8')
    ifft_in[0,(fft_size-num_sc) // 2:(fft_size-num_sc) // 2 + num_sc] = in_d

    ifft_out = fft.ifft(ifft_in)

    #add CP
    sym = np.zeros((1,fft_size + 288),'c8')
    sym[:,0:288] = ifft_out[:,-288:]
    sym[:,288:] = ifft_out
    
    #fft input is 140 ahead of starting of data
    offset = 288 - 140
    fft_in = sym[:,offset:offset+fft_size]

    fft_out = fft.fft(fft_in)
    
    #timing left shift by 140 = freq shift per sc
    comp = np.exp(1j*2*np.pi*140/fft_size*np.arange(fft_size))
    comp_o = fft_out * comp
    
    out_d = comp_o[0,(fft_size-num_sc) // 2:(fft_size-num_sc) // 2 + num_sc]
    assert np.allclose(in_d, out_d, atol=1e-5)
        
    pass
