# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy.signal import upfirdn
from scipy.signal import remez

from py5gphy.common import nr_slot

def Rx_low_phy(td_slot, carrier_config, sample_rate_in_hz):
    """ handle TX data processing, including
    phase correction, half-CP removal, FFT and timing correction
    1. based on 38.2115.4, each symbolk need phase compensation, receiving side need phase correction
    2. half-CP removel: time domain symbol data is CP+data, while the last few samples in data domain could mix with next symbol data
        the reason could be A: (both Tx and Rx filter) B: Rx timing error
        to avoid this data interference, receiver usually choose the second half of CP data and first [N-1/2 CP size] data to do FFT
    after FFT, symbol data need phase compensation to compensate 1/2 CP timing offset

    input:
    td_slot: one slot of time domain data
    sample_rate_in_hz: input dat sample rate
    output:
    fd_slot: one slot of frequency domain data
    """
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    num_of_ant = carrier_config["num_of_ant"]
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]

    fftsize = int(sample_rate_in_hz/(scs*1000))
    assert fftsize in [128,256,512,1024,2048,4096,8192,8192*2]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

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
    phase_vec = np.exp(1j * 2 * np.pi / fftsize * np.arange(fftsize))

    fd_slot = np.zeros((num_of_ant,fftsize*14), 'c8')

    td_offset = 0
    for sym in range(14):
        # phase correction
        td_sym = td_slot[:, td_offset : td_offset+cptable[sym]+fftsize]
        if central_freq_in_hz:
            #phase compensation only when central_freq_in_hz nonzero
            delta = central_freq_in_hz / sample_rate_in_hz
            td_sym = td_sym * np.exp(1j * 2 * np.pi * delta * (td_offset + cptable[sym]))
        
        #choose last 1/2*short-CP length of CP and first (fftsize - 1/2*short-CP length) data for FFT
        sel_td_sym = td_sym[:,cptable[sym]-half_short_cp_size : cptable[sym]-half_short_cp_size+fftsize]
        fft_out = fft.fft(sel_td_sym)

        #phase compensation to compensate half_short_cp_size timing advance
        fd_slot[:, fftsize*sym:fftsize*(sym+1)] = fft_out * phase_vec
    
    return fd_slot

def channel_filter(rx_waveform, carrier_config,sample_rate_in_hz):
    """ filter and downsample
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    oversample_rate = int(245.76*(10**6) / sample_rate_in_hz)

    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    numtaps = 55 #for half band filter, (numtaps+1) must be divisble by 4
    Fpass = 0.21 #should be less than 0.25
    halfband_filtercoeff = remez(numtaps, [0, Fpass, 0.5-Fpass, 0.5], [1,0])

    #half band filter to downsaple
    #number of half band filter
    assert int(np.log2(oversample_rate)) == np.log2(oversample_rate)
    reps = int(np.log2(oversample_rate))
    offset = int(halfband_filtercoeff.size // 2 )
        
    for _ in range(reps):
        input_size = rx_waveform.shape[1]
        rx_waveform = upfirdn(halfband_filtercoeff, rx_waveform, down=2)
        rx_waveform = rx_waveform[:,offset : offset + input_size // 2]
    
    #FIR filtere
    #generate FIR coefficient
    #get Fpass and Fstop in hz
    Fpass = ((carrier_prb_size*12*scs + scs / 2) * 1000)/2
    Fstop = BW*(10**6)/2
    numtaps = 128
    filter_coeff = remez(numtaps, [0, Fpass, Fstop, sample_rate_in_hz/2], [1,0],fs=sample_rate_in_hz)

    #FIR filter with oversample rate =1, 
    input_size = rx_waveform.shape[1]
    td_waveform = upfirdn(filter_coeff, rx_waveform)
    offset = int(filter_coeff.size // 2 )
    td_waveform = td_waveform[:,offset : offset + input_size]

    return td_waveform

def waveform_rx_processing(rx_waveform, carrier_config,sample_rate_in_hz):
    """ Rx waveform processing,
    return freq domain IQ data
    """
    #FIR filter and downsample
    td_waveform = channel_filter(rx_waveform, carrier_config,sample_rate_in_hz)

    #get number of slot
    scs = carrier_config["scs"]
    samples_in_one_slot = int(sample_rate_in_hz/1000*15/scs)
    num_slots = td_waveform.shape[1] // samples_in_one_slot
    fftsize = int(sample_rate_in_hz/(scs*1000))

    fd_waveform = np.zeros((td_waveform.shape[0],num_slots*fftsize*14),'c8')
    for slot in range(num_slots):
        td_slot = td_waveform[:,slot*samples_in_one_slot:(slot+1)*samples_in_one_slot]
        fd_slot = Rx_low_phy(td_slot, carrier_config, sample_rate_in_hz)
        fd_waveform[:,slot*fftsize*14:(slot+1)*fftsize*14] = fd_slot
    
    return td_waveform,fd_waveform