# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import MIMO_fading_channel

class NrChannelModel():
    """ 5G channel model
        refer to docs\algorithm\5g_channel_model.md
    """
    def __init__(self, Nt, Nr, Timeoff_ns, rho, fm_inHz, Rspat, Pnoise_dB, multi_paths, fi_inHz,fs_inHz, scs,num_of_sinusoids=50):
        """
        """
        self.Nt = Nt #Tx antenna number
        self.Nr = Nr #Rx antenna number
        self.Timeoff_ns = Timeoff_ns #Tx to Rx timing offset in ns
        self.rho = rho #transmitter relative frequency error
        self.fm_inHz = fm_inHz #maximum doppler frequency offset in Hz
        self.Rspat = Rspat #MIMO correlation matrix
        self.Pnoise_dB = Pnoise_dB #noise power in dB
        
        #multi-path list
        #"delay in ns, power in dB, Rayleign or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician",
        self.multi_paths = multi_paths
        self.fi_inHz = fi_inHz #carrier frequency in Hz
        self.fs_inHz = fs_inHz #time domain data sample rate in Hz,
        self.scs = scs #subcarrier bandwidth, 15KHz or 30KHz

        self.num_of_sinusoids = num_of_sinusoids #used for Rayleign or Rician channel

        #validate
        assert fs_inHz in [245760000, 491520000,983040000]
        assert Nt in [1,2,4,8]
        assert Nr in [1,2,4,8]
        if Rspat.shape[0] == 1:
            assert Rspat.shape[0]==Nt*Nr
        else:
            assert len(Rspat.shape)==2 and Rspat.shape[0]==Rspat.shape[1] and Rspat.shape[0]==Nt*Nr
        assert scs in [15,30]

        self.gen_info() #generate necessary info
        self.reset_Terror()

    def gen_info(self):
        """generate info used for channel filter

        """
        #generate fractional TA and integer relative TA 
        # Timeoff = n_integer_TA / fs_inHz + TA_frac
        self.n_integer_TA = int(np.round(self.Timeoff_ns * 10**(-9) * self.fs_inHz))
        self.TA_frac = self.Timeoff_ns * 10**(-9) - self.n_integer_TA / self.fs_inHz

        #generate timing offset in second of each symbol data  to the beginning of slot
        if self.scs == 15:
            # assume sample rate = 30.72MHz
            # IFFT size = 2048, CP length per symbol = [160,[144]*6,160,[140]*6]
            scs15_cp_list = np.array([160] + [144]*6 + [160] + [144]*6 )
            symbols_sample_offset_list = np.zeros(14)
            offset = 0
            for m in range(14):
                offset += scs15_cp_list[m]
                symbols_sample_offset_list[m] = offset
                offset += 2048

            symbols_offset_list = symbols_sample_offset_list/(30.72* 10**6 )
        else:
            # assume sample rate = 122.88MHz
            # IFFT size = 4096, CP length per symbol = [352,[288]*13]
            scs30_cp_list = np.array([352] + [288]*13)
            symbols_sample_offset_list = np.zeros(14)
            offset = 0
            for m in range(14):
                offset += scs30_cp_list[m]
                symbols_sample_offset_list[m] = offset
                offset += 4096

            symbols_offset_list = symbols_sample_offset_list/(122.88* 10**6 ) * 10**9
        self.symbols_offset_list = symbols_offset_list
    
    def reset_Terror(self):
        #Terror is timing offset in second from the beginning of the slot to the beginning of the waveform
        self.Terror = 0 

    def update_Dm(self):
        # return the timing error for each symbol in the slot
        # timing error is timing offset * rho #transmitter relative frequency error
        Dm = self.symbols_offset_list * self.rho + self.Terror - self.TA_frac
        
        #update error,self.Terror point to next slot timing error
        if self.scs == 15:
            self.Terror += 10**(-3) * self.rho #1ms timing error
        else:
            self.Terror += 10**(-3)/2 * self.rho #0.5ms timing error
        
        return Dm
       
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

        #step 3: for each TAP, go through MIMO channel, add TAP TA  and power, then add all tap output together
        tap_sum = np.zeros((self.Nr,N),'c8')
        for path in multi_paths:
            #get "delay in ns, power in dB, Rayleign or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician"
            tap_delay = path[0]*10**(-9)
            tap_power_db = path[1]
            tap_channel = path[2] #Rayleign or Rician
            K = path[3]
            fDo = path[4]

            #generate MIMO channel response
            tap_MIMO_response = MIMO_fading_channel.gen_mimo_channel(self.Nt, self.Nr, self.Rspat, N, self.fs_inHz,tap_channel, K, fDo,self.fm_inHz,self.num_of_sinusoids)

            tap_o = np.zeros((self.Nr,N),'c8')
            for n in range(N):
                tap_o[:,n] = tap_MIMO_response[n] @ tx_o2[:,n]

            tap_o *= 10**(tap_power_db/20)
            tap_delay_normalize = int(np.round(tap_delay/self.fs_inHz))

            if tap_delay_normalize >= 0:
                tap_sum[:,tap_delay_normalize:] += tap_o[:,0:N-tap_delay_normalize]
            else:
                tap_sum[:,0:N-tap_delay_normalize] += tap_o[:,tap_delay_normalize]
            
        # step 4: add noise
        tap_sum += np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_sum.shape) + \
              1j * np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_sum.shape)
        
        return tap_sum

if __name__ == "__main__":
    import json
    path = "py5gphy/nr_default_config/"
    with open(path + "default_channel_model.json", 'r') as f:
        channel_model_config = json.load(f)
    
    #read parameters
    Nt = channel_model_config['Nt']
    Nr = channel_model_config['Nr']
    Timeoff_ns = channel_model_config['Timeoff_ns']
    rho = channel_model_config['rho']
    fm_inHz = channel_model_config['fm_inHz']
    Rspat = np.array(channel_model_config['Rspat'])
    Pnoise_dB = channel_model_config['Pnoise_dB']
    multi_paths = channel_model_config['multi_paths']
    fi_inHz = channel_model_config['fi_inHz']
    fs_inHz = channel_model_config['fs_inHz']
    scs = channel_model_config['scs']
    num_of_sinusoids = channel_model_config['num_of_sinusoids']

    nrChannelModel = NrChannelModel(Nt, Nr, Timeoff_ns, rho, fm_inHz, Rspat, Pnoise_dB, multi_paths, fi_inHz,fs_inHz, scs,num_of_sinusoids)

    tx = np.ones((Nt,int(fs_inHz*1*10**(-3))),'c8')
    out = nrChannelModel.filter(tx)

    Nt = 2
    Nr = 4
    Rspat = np.identity(Nt*Nr,'c8')
    nrChannelModel = NrChannelModel(Nt, Nr, Timeoff_ns, rho, fm_inHz, Rspat, Pnoise_dB, multi_paths, fi_inHz,fs_inHz, scs,num_of_sinusoids)

    tx = np.ones((Nt,int(fs_inHz*1*10**(-3))),'c8')
    out = nrChannelModel.filter(tx)
    pass
    
