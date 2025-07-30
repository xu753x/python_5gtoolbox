# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft
from scipy.signal import upfirdn
from scipy.signal import remez

from py5gphy.common import nr_slot

def Tx_low_phy(fd_slot, carrier_config, sample_rate_in_hz, Dm=np.zeros(14)):
    """ handle Tx data IFFT, add CP and phase compensation
    could be used for gNodeB DL and UE UL transmission
    td_slot = DL_low_phy(fd_slot)
    input:
        sample_rate_in_hz: time domain sample rate after ifft and add cp
        Dm is timing error in second for each symbol, it is used to simulate fractional timing error
              timing error is different for each symbol ifd transmitter-receiver frequency error is non-zero
    """
    
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    num_of_ant = carrier_config["num_of_ant"]
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]

    ifftsize = int(sample_rate_in_hz/(scs*1000))
    assert ifftsize in [128,256,512,1024,2048,4096,8192,8192*2]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
    
    #IFFT output data will go through FIR filter
    #below 0.85 comes from Matlab 5G toolbox and is used to provide some room for FIR filter transition width
    #IFFT size could not be too short
    min_ifftsize = (2 ** np.ceil(np.log2(carrier_prb_size*12/0.85)))
    assert ifftsize >= min_ifftsize

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
        fh_sym *= np.exp(1j*2*np.pi*np.arange(sc_size)*scs*1000*Dm[sym])

        ifftin = np.zeros((num_of_ant,ifftsize),'c8')
        ifftin[:,(ifftsize - sc_size) // 2: (ifftsize + sc_size) // 2] = fh_sym
        ifftout = fft.ifft(fft.ifftshift(ifftin))

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
    then a couple of half band filter with upsample rate = 2 to reach 245.76MHz sanmple rate
    
    the output of thr function usually go through CFR->DPD -> mixer -> D/A converter to analog RF signal
    The output of the function ACLR need be less than 45dB limit(38.104 6.6.3)
    The default filter provided in Matlab 5G toolbox provide around 35dB ACLR which is too high
    the output sample rate is usually designed as 245.6MHz for all BW
    
    """
    scs = carrier_config["scs"]
    BW = carrier_config["BW"]
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    oversample_rate = int(245.76*(10**6) / sample_rate_in_hz)

    #generate FIR coefficient
    #get Fpass and Fstop in hz
    Fpass = ((carrier_prb_size*12*scs + scs / 2) * 1000)/2
    Fstop = BW*(10**6)/2
    numtaps = 128
    filter_coeff = remez(numtaps, [0, Fpass, Fstop, sample_rate_in_hz/2], [1,0],fs=sample_rate_in_hz)

    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    numtaps = 55 #for half band filter, (numtaps+1) must be divisble by 4
    Fpass = 0.21 #should be less than 0.25
    halfband_filtercoeff = remez(numtaps, [0, Fpass, 0.5-Fpass, 0.5], [1,0])
    
    input_size = td_waveform.shape[1]

    #FIR filter with oversample rate =1, 
    outd = upfirdn(filter_coeff, td_waveform)
    offset = int(filter_coeff.size // 2 )
    outd = outd[:,offset : offset + input_size]

    #number of half band filter
    assert int(np.log2(oversample_rate)) == np.log2(oversample_rate)
    reps = int(np.log2(oversample_rate))

    for m in range(reps):
        outd = upfirdn(halfband_filtercoeff, outd, up=2)
        offset = int(halfband_filtercoeff.size // 2 )
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
    

if __name__ == "__main__":
    #verify ifft operation result is the same with 38.211 5.3operation
    verify_ifft()

    print("test nr low phy IFFt, add CP and phase compensation")
    from tests.nr_lowphy import test_nr_lowphy
    file_lists = test_nr_lowphy.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_lowphy.test_nr_lowphy(filename)




