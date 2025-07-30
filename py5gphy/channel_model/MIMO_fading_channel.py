# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import rayleigh_channel
from py5gphy.channel_model import rician_channel

def gen_mimo_channel(Nt, Nr, R_spat, N, samplerate_in_hz,channel, K, fDo,fmax=0,num_of_sinusoids=50):
    """ generate MIMO channel response
    input:
        R_spat: spatial_correlation_matrix
        Nt: number of Tx antenna
        Nr: number of Rx antenna
        N: num_of_sample
        channel: Rayleign or Rician
        K in dB for Rician， 
        fDo(doppler freq in hz) for Rician
        samplerate_in_hz: Input signal sample rate (Hz)
        fmax: Maximum Doppler shift (Hz)
        num_of_sinusoids: Number of sinusoids used to generate Rayleigh filter
    """
   
    #step 1, generate Nt X Nr Rayleign or Rician with size = N
    vec_channel = np.zeros((Nt*Nr, N), 'c8')
    for m in range(Nt*Nr):
        if channel == "Rayleign":
            vec_channel[m,:] = rayleigh_channel.gen_RayleighChannel_filters(N,fmax,samplerate_in_hz,num_of_sinusoids)
        else:
            vec_channel[m,:] = rician_channel.gen_RicianChannel_filters(N,K, fDo,fmax,samplerate_in_hz,num_of_sinusoids)

    #step 2 generate MIMO channel
    if R_spat.shape[0] > 1:
        #cholesky only support 2-D dimension
        L = np.linalg.cholesky(R_spat)
    else:
        L = R_spat

    MIMO_channel = np.zeros((N, Nr, Nt), 'c8')
    for m in range(N):
        vec_H = L @ vec_channel[:,m]
        # reshape vec_H to Nr X Nt matrix
        H = vec_H.reshape((Nr, Nt), order='F')
        MIMO_channel[m] = H
    
    return MIMO_channel


if __name__ == "__main__":
    Nt = 1
    Nr = 1
    R_spat = np.diag(np.ones(Nt*Nr,'c8'))
    MIMO_channel = gen_mimo_channel(Nt, Nr, R_spat, N=10, samplerate_in_hz=245760000,channel="Rayleign", K=0, fDo=0,fmax=0,num_of_sinusoids=50)
    np.allclose(MIMO_channel[0],MIMO_channel[6],atol=1e-7)

    Nt = 2
    Nr = 4
    R_spat = np.diag(np.ones(Nt*Nr,'c8'))
    MIMO_channel = gen_mimo_channel(Nt, Nr, R_spat, N=10, samplerate_in_hz=245760000,channel="Rayleign", K=0, fDo=0,fmax=0,num_of_sinusoids=50)
    np.allclose(MIMO_channel[0],MIMO_channel[6],atol=1e-7)
    
    Nt = 2
    Nr = 4
    R_spat = np.diag(np.ones(Nt*Nr,'c8'))
    MIMO_channel = gen_mimo_channel(Nt, Nr, R_spat, N=10, samplerate_in_hz=245760000,channel="Rician", K=0, fDo=0,fmax=0,num_of_sinusoids=50)
    np.allclose(MIMO_channel[0],MIMO_channel[6],atol=1e-7)
    
    pass
