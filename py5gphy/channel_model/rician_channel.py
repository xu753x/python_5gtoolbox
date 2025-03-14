# -*- coding:utf-8 -*-
import numpy as np

"""
    support frequency-selective multipath RicianChannel fading channel System
    the generation of RicianChannel filter 
    refer to 
    Amirhossein Alimohammad, Saeed F. Fard, Bruce F. Cockburn, Christian Schlegel
    "A Compact Rayleigh and Rician Fading Simulator Based on Random Walk Processes"
    use model I for RayleighChannel and model IV for Rician channel
    
"""
def gen_RicianChannel_filters(num_of_sample,K=0, fmax=0,samplerate_in_hz=245760000,num_of_sinusoids=50):
    """generate one Rayleigh filter coefficient for each sample
    if fmax =0, filter coefficient are the same for each sample
    input:
        num_of_sample: number of samples
        K: Rician factor, if K=0, the output is Rayleigh filter
        fmax: Maximum Doppler shift (Hz)
        samplerate_in_hz: Input signal sample rate (Hz)
        num_of_sinusoids: Number of sinusoids used to generate Rayleigh filter
    output:
        filter sequence with num_of_sample + additonal_samples (add additonal_samples to be used for interpolation)
    """
    additonal_samples = 0 #generate addiitonal samples which are used for interpolation 
    total_samples = num_of_sample + additonal_samples
    N = num_of_sinusoids
    fD = fmax
    Ts = 1/samplerate_in_hz

    #first generate Rayleigh
    #model I
    #ci[m] = sqrt(2/N)sum(cos(2*pi*fD*Ts*m*cos(alpha[n])) + phase1[n])
    #cq[m] = sqrt(2/N)sum(cos(2*pi*fD*Ts*m*sin(alpha[n])) + phase2[n])
    #where alpha[n] = (2*pi*n-pi+seta)/4N , seta is uniformly distributed over [-pi,pi]
    #phase1[n],phase2[n] are uniformly distributed over [-pi,pi]
    rng = np.random.default_rng()
    phase1 = rng.uniform(-np.pi, np.pi, (N,1))
    phase2 = rng.uniform(-np.pi, np.pi, (N,1))
    seta = rng.uniform(-np.pi, np.pi, (N,1))

    #repeate to get N X total_samples matrix
    phase1_m = np.repeat(phase1, total_samples, axis=1)
    phase2_m = np.repeat(phase2, total_samples, axis=1)
    seta_m = np.repeat(seta, total_samples, axis=1)

    #generate N X total_samples matrix with each line data from 0 to total_samples-1
    samples = np.ones((N,1)) @ np.arange(total_samples).reshape((1,total_samples))
    
    ci = np.sqrt(2/N)*np.sum(np.cos(2*np.pi*fD*Ts*samples*np.cos(seta_m) + phase1_m), axis=0)
    cq = np.sqrt(2/N)*np.sum(np.cos(2*np.pi*fD*Ts*samples*np.sin(seta_m) + phase2_m), axis=0)

    #LOS path filter
    seta0 =  rng.uniform(-np.pi, np.pi, 1)
    phase0 =  rng.uniform(-np.pi, np.pi, 1)

    LOS = np.exp(1j*(2*np.pi*fD*Ts*samples[0,:]*np.cos(seta0) + phase0))

    rm = 1/np.sqrt(K+1)*(ci + 1j*cq) + np.sqrt(K/(K+1))*LOS

    return rm  

if __name__ == "__main__":
    rm = gen_RicianChannel_filters(10)

    pass