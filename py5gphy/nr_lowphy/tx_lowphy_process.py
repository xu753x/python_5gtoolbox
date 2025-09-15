# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy.signal import upfirdn
from scipy.signal import remez

from py5gphy.common import nr_slot

def Tx_low_phy(fd_slot, carrier_config, Dm=[]):
    """ handle Tx data IFFT, add CP and phase compensation
    could be used for gNodeB DL and UE UL transmission
    td_slot = DL_low_phy(fd_slot)
    input:
        
        Dm is timing error in second for each symbol, it is used to simulate fractional timing error
              timing error is different for each symbol ifd transmitter-receiver frequency error is non-zero
    """
    
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    num_of_ant = carrier_config["num_of_ant"]
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
    
    #IFFT output data will go through FIR filter
    #below 0.85 comes from Matlab 5G toolbox and is used to provide some room for FIR filter transition width
    #IFFT size could not be too short
    ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    sample_rate_in_hz = ifftsize * scs * 1000

    #get cp table
    #CP size
    ifft4096_scs30_cp_list = np.array([352] + [288]*13)
    ifft4096_scs15_cp_list = np.array([320] + [288]*6 + [320] + [288]*6 )

    if scs == 15:
        cptable = ifft4096_scs15_cp_list / (4096 / ifftsize)
    else:
        cptable = ifft4096_scs30_cp_list / (4096 / ifftsize)
    cptable = cptable.astype(int)

    sc_size = fd_slot.shape[1] // 14 # sc size in one symbol

    td_slot = np.zeros((num_of_ant,cptable.sum() + ifftsize*14), 'c8')

    td_offset = 0
    for sym in range(14):
        fh_sym = fd_slot[:,sc_size*sym : sc_size*(sym+1)]
        
        #phase shift with timing error
        # phase = exp(j*2*i*k*fc*Dm)
        if len(Dm) > 0:
            fh_sym *= np.exp(1j*2*np.pi*np.arange(sc_size)*scs*1000*Dm[sym])
        
        ifftin = np.zeros((num_of_ant,ifftsize),'c8')
        ifftin[:,(ifftsize - sc_size) // 2: (ifftsize + sc_size) // 2] = fh_sym
        #fft.ifftshift is to return zero frequency data to the beginning of the array
        #which is the expected input order for inverse FFT operations
        #receiving side need do FFT first, then fftshift to move zero frequency data to the center of the array
        #IFFT out power is N time lower than total IFFT input power, the ifftout need multuply by sqrt(ifftsize)
        ifftout = fft.ifft(fft.ifftshift(ifftin),axis=1)*np.sqrt(ifftsize)

        #add cp
        td_sym = np.zeros((num_of_ant,cptable[sym] + ifftsize),'c8')
        td_sym[:, 0:cptable[sym]] = ifftout[:, -cptable[sym]:]
        td_sym[:, cptable[sym]:] = ifftout

        #phase compensation for each symbol in one slot assuming tu_start start from 0
        #phase compemsation for each slot shall be done in other place
        if central_freq_in_hz:
            #phase compensation only when central_freq_in_hz nonzero
            delta = central_freq_in_hz / sample_rate_in_hz
            td_sym = td_sym * np.exp(-1j * 2 * np.pi * delta * (td_offset + cptable[sym]))

        td_slot[:,td_offset : td_offset + cptable[sym] + ifftsize] = td_sym
        td_offset += cptable[sym] + ifftsize

    return td_slot

def channel_filter(td_waveform, carrier_config,sample_rate_in_hz):
    """ the ACLR of time domain data after IFFT is higher than 3gpp requirements.
    the data need go through channel filter to filter out out of BW signal.
    usually the data will go though FIR first with upssample rate = 1, 
    then a couple of half band filter with upsample rate = 2 to reach sample_rate_in_hz
    
    the output of thr function usually go through CFR->DPD -> mixer -> D/A converter to analog RF signal
    The output of the function ACLR need be less than 45dB limit(38.104 6.6.3)
    The default filter provided in Matlab 5G toolbox provide around 35dB ACLR which is too high
    the output sample rate is usually designed as 245.6MHz for all BW
    
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
    
    ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    in_sample_rate_in_hz = ifftsize * scs*1000
    oversample_rate = int(sample_rate_in_hz/in_sample_rate_in_hz)

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

    filter_coeff = remez(FIR_numtaps, [0, Fpass, Fstop, in_sample_rate_in_hz/2], [1,0],fs=in_sample_rate_in_hz)

    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    #below parameter comes from HB filter searching test by calling searching_HB_filter for different BW and scs
    HB_numtaps = 55
    HB_Fpass = 0.21
    halfband_filtercoeff = remez(HB_numtaps, [0, HB_Fpass, 0.5-HB_Fpass, 0.5], [1,0])
    
    input_size = td_waveform.shape[1]

    #FIR filter with oversample rate =1, 
    outd = upfirdn(filter_coeff, td_waveform)
    offset = int((filter_coeff.size) // 2 )
    outd = outd[:,offset : offset + input_size]

    #number of half band filter
    assert int(np.log2(oversample_rate)) == np.log2(oversample_rate)
    reps = int(np.log2(oversample_rate))

    for m in range(reps):
        #for both updample nu 2 tx half band filter and dowmsaple by 2 rx halfband filter, the output need multiple sqrt(2), to make H_LS and added noise power have no change
        outd = upfirdn(halfband_filtercoeff, outd, up=2) * np.sqrt(2)
        #output length = input length + halfband_filtercoeff.size -2, this is why offset = halfband_filtercoeff.size // 2 ) - 1
        offset = int(halfband_filtercoeff.size // 2 ) - 1
        outd = outd[:,offset : offset + 2*input_size]
        input_size *= 2
    
    dl_waveform = outd

    return dl_waveform

def verify_ifft():
    """ to verify ifft operation """

    #generate random data
    ifftsize = 64
    insize = 50
    
    #rng = np.random.default_rng()
    #indata = rng.random(64)
    indata = np.arange(insize) 

    #follow to 38.211 5.3.1 OFDM basebend signal generation
    outd = np.zeros(ifftsize, 'c8')
    for n in range(ifftsize):
        d1 = 0
        for k in range(insize):
            d1 += indata[k] * np.exp(1j * 2 * np.pi * (k - insize // 2) * n / ifftsize)
        outd[n] = d1
    outd = outd/ifftsize

    ifftin = np.zeros((4,ifftsize)) # assume 4 antenna
    ifftin[:,(ifftsize - insize) // 2: (ifftsize + insize) // 2] = indata # fill 4 antenna 
    #d1 = fft.ifft(ifftin)
    ifftout = fft.ifft(fft.ifftshift(ifftin))
    assert np.allclose(outd, ifftout[0,:],atol=1e-5)
    assert np.allclose(outd, ifftout[1,:],atol=1e-5)
    assert np.allclose(outd, ifftout[2,:],atol=1e-5)
    assert np.allclose(outd, ifftout[3,:],atol=1e-5)
    
def verify_ifft_fft_power():
    #check (1) FFT in and FFT out power and (2)IFFT in and IFFT out power 
    rng = np.random.default_rng()
    N = 4096
    #generate mean power = 1 complex FFT input data
    fftin = rng.normal(0,1,N)/np.sqrt(2)+1j*rng.normal(0,1,N)/np.sqrt(2)
    fftout = fft.fft(fftin)

    #fft output power is N times higher than fft input power,the FFT operation need compensate such difference
    fftout_power = np.sum(np.abs(fftout)**2)

    #ifft output power is N times lower than fft input power,the FFT operation need compensate such difference
    ifftout = fft.ifft(fftout)
    ifftout_power = np.sum(np.abs(ifftout)**2)



if __name__ == "__main__":
    verify_ifft_fft_power()
    #verify ifft operation result is the same with 38.211 5.3operation
    verify_ifft()

    print("test nr low phy IFFt, add CP and phase compensation")
    from tests.nr_lowphy import test_nr_tx_lowphy_process
    file_lists = test_nr_tx_lowphy_process.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_tx_lowphy_process.test_nr_lowphy(filename)




