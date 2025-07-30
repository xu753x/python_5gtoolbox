# -*- coding:utf-8 -*-
import numpy as np

"""
    support frequency-selective multipath Rayleigh fading channel System
    the generation of Rayleigh filter 
    refer to 
    Amirhossein Alimohammad, Saeed F. Fard, Bruce F. Cockburn, Christian Schlegel
    "A Compact Rayleigh and Rician Fading Simulator Based on Random Walk Processes"
    use model I for RayleighChannel and model IV for Rician channel
    
"""
def gen_RayleighChannel_filters(num_of_sample,fmax=0,samplerate_in_hz=245760000,num_of_sinusoids=50):
    """generate one Rayleigh filter coefficient for each sample
    if fmax =0, filter coefficient are the same for each sample
    input:
        num_of_sample: number of samples
        fmax: Maximum Doppler shift (Hz)
        samplerate_in_hz: Input signal sample rate (Hz)
        num_of_sinusoids: Number of sinusoids used to generate Rayleigh filter
    output:
        filter sequence with num_of_sample 
    """
    Ts = 1/samplerate_in_hz

    #model I
    #ci[m] = sqrt(2/N)sum(cos(2*pi*fD*Ts*m*cos(alpha[n])) + phase1[n])
    #cq[m] = sqrt(2/N)sum(cos(2*pi*fD*Ts*m*sin(alpha[n])) + phase2[n])
    #where alpha[n] = (2*pi*n-pi+seta)/4N , seta is uniformly distributed over [-pi,pi]
    #phase1[n],phase2[n] are uniformly distributed over [-pi,pi]
    rng = np.random.default_rng()
    phase1 = rng.uniform(-np.pi, np.pi, (num_of_sinusoids,1))
    phase2 = rng.uniform(-np.pi, np.pi, (num_of_sinusoids,1))
    seta = rng.uniform(-np.pi, np.pi, (num_of_sinusoids,1))

    #repeate to get num_of_sinusoids X num_of_sample matrix
    phase1_m = np.repeat(phase1, num_of_sample, axis=1)
    phase2_m = np.repeat(phase2, num_of_sample, axis=1)
    seta_m = np.repeat(seta, num_of_sample, axis=1)

    #generate num_of_sinusoids X num_of_sample matrix with each line data from 0 to num_of_sample-1
    samples = np.ones((num_of_sinusoids,1)) @ np.arange(num_of_sample).reshape((1,num_of_sample))
    
    ci = np.sqrt(2/num_of_sinusoids)*np.sum(np.cos(2*np.pi*fmax*Ts*samples*np.cos(seta_m) + phase1_m), axis=0)
    cq = np.sqrt(2/num_of_sinusoids)*np.sum(np.cos(2*np.pi*fmax*Ts*samples*np.sin(seta_m) + phase2_m), axis=0)

    return ci + 1j*cq    

if __name__ == "__main__":
    cm = gen_RayleighChannel_filters(10)
    assert np.all(cm ==cm[0])
    pass