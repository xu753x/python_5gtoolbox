# -*- coding:utf-8 -*-
import numpy as np
import copy

from py5gphy.channel_model import MIMO_fading_channel
from py5gphy.channel_model import nr_TDL_channel
from py5gphy.channel_model import nr_spatial_correlation_matrix
from py5gphy.channel_model import nr_channel_model

class AWGNChannelModel(nr_channel_model.NrChannelModel):
    """ AWGN channel model is the simplest channel model
    with one path and H matrix are the same for all symbols and all RE
    it also support timing offset, freq offset, and MIMO channel with different correlation
    the code refer to NrChannelModel class
    """
    def __init__(self, channel_model_config, Pnoise_dB,fi_inHz,fs_inHz,scs,fDo_in_Hz,H_matrix=np.empty(0)):
        """ AWGN channel can be regarded as one path only and this path is Rician channel with very high K value
        """
        
        self.fDo_in_Hz = fDo_in_Hz
        
        copied_channel_model_config = copy.deepcopy(channel_model_config)
        copied_channel_model_config["multi_paths"] = []
        super().__init__(copied_channel_model_config, Pnoise_dB,fi_inHz,fs_inHz,scs)
        
        Nt = channel_model_config["Nt"]
        Nr = channel_model_config["Nr"]
        if H_matrix.size == 0:
            self.H_matrix = np.zeros((Nr,Nt),'c8')
            for nt in range(Nt):
                self.H_matrix[nt, nt] = 1
        else:
            self.H_matrix = H_matrix
            assert H_matrix.shape[0] == Nr and H_matrix.shape[1] == Nt

    def filter(self,tx):
        """time domain data go through channel
        tx:  Nt X N input data 
        """
        
        N = tx.shape[1]
        assert tx.shape[0] == self.Nt
        #step 1: carrier frequency offset
        ferror = self.fi_inHz * self.rho #carrier freq * freq relative error
        tx_o = tx * np.exp(1j * 2 * np.pi * ferror * np.arange(N) / self.fs_inHz)
        
        #step 2: integer TA offset
        tx_o2 = np.zeros((self.Nt,N),'c8')
        if self.n_integer_TA >= 0:
            tx_o2[:,self.n_integer_TA:] = tx_o[:,0:N-self.n_integer_TA]
        else:
            tx_o2[:,0:N-self.n_integer_TA]=tx_o[:,self.n_integer_TA:]

        #step 3: generate Nr X Nt H sequence
        MIMO_channel = np.zeros((N, self.Nr, self.Nt),'c8')
        Ts = 1/self.fs_inHz #fs_inHz is sample rate

        for nr in range(self.Nr):
            for nt in range(self.Nt):
                rng = np.random.default_rng()
                phase0 =  rng.uniform(-np.pi, np.pi, 1)
       
                LOS = np.exp(1j*(2*np.pi*self.fDo_in_Hz*Ts*np.arange(N) + phase0))
                MIMO_channel[:,nr,nt] = LOS*self.H_matrix[nr,nt]

        # tx_o2 go through MIMO channel 
        tap_o = np.zeros((self.Nr,N),'c8')
        for n in range(N):
            tap_o[:,n] = MIMO_channel[n] @ tx_o2[:,n]

        # step 4: add noise if Pnoise_dB!= 255
        if self.Pnoise_dB != 255:
            tap_o += np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_o.shape) + \
                1j * np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_o.shape)
        
        return tap_o