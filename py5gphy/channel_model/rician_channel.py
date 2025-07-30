# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import rayleigh_channel
"""
    support frequency-selective multipath RicianChannel fading channel System
    the generation of RicianChannel filter 
    refer to 
    Amirhossein Alimohammad, Saeed F. Fard, Bruce F. Cockburn, Christian Schlegel
    "A Compact Rayleigh and Rician Fading Simulator Based on Random Walk Processes"
    use model I for RayleighChannel and model IV for Rician channel
    
"""
def gen_RicianChannel_filters(num_of_sample,K=0, fDo=0, fmax=0,samplerate_in_hz=245760000,num_of_sinusoids=50):
    """generate one Rayleigh filter coefficient for each sample
    if fmax =0, filter coefficient are the same for each sample
    input:
        num_of_sample: number of samples
        K: Rician factor, if K=0, the output is Rayleigh filter
        fmax: Maximum Doppler shift (Hz)
        samplerate_in_hz: Input signal sample rate (Hz)
        num_of_sinusoids: Number of sinusoids used to generate Rayleigh filter
    output:
        filter sequence with num_of_sample 
    """
    Ts = 1/samplerate_in_hz

    #first generate Rayleigh
    cm = rayleigh_channel.gen_RayleighChannel_filters(num_of_sample,fmax,samplerate_in_hz,num_of_sinusoids)
    
    #LOS path filter
    rng = np.random.default_rng()
    phase0 =  rng.uniform(-np.pi, np.pi, 1)

    #generate num_of_sinusoids X num_of_sample matrix with each line data from 0 to num_of_sample-1
    LOS = np.exp(1j*(2*np.pi*fDo*Ts*np.arange(num_of_sample) + phase0))

    rm = 1/np.sqrt(K+1)*cm + np.sqrt(K/(K+1))*LOS

    return rm  

if __name__ == "__main__":
    rm = gen_RicianChannel_filters(10)
    assert np.all(rm ==rm[0])

    fDo = 10
    rm = gen_RicianChannel_filters(10,K=1000,fDo=fDo)
    assert np.allclose(rm[1:]/rm[0:9], np.exp(1j*2*np.pi*fDo/245760000), atol=1e-5)
    pass