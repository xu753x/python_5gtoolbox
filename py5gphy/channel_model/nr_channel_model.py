# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import MIMO_fading_channel
from py5gphy.channel_model import nr_TDL_channel
from py5gphy.channel_model import nr_spatial_correlation_matrix

class NrChannelModel():
    """ 5G channel model
        refer to docs\algorithm\5g_channel_model.md
    """
    def __init__(self, channel_model_config, Pnoise_dB,fi_inHz,fs_inHz,scs):
        """
        """
        self.Nt = channel_model_config["Nt"] #Tx antenna number
        self.Nr = channel_model_config["Nr"] #Rx antenna number
        self.Timeoff_ns = channel_model_config["Timeoff_ns"] #Tx to Rx timing offset in ns
        self.rho = channel_model_config["rho"] #transmitter relative frequency offset
        self.fm_inHz = channel_model_config["fm_inHz"] #maximum doppler frequency offset in Hz
        self.Rspat = channel_model_config["Rspat"] #MIMO correlation matrix
        self.Pnoise_dB = Pnoise_dB #noise power in dB
        
        #multi-path list
        #"delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician",
        self.multi_paths = channel_model_config["multi_paths"]
        self.fi_inHz = fi_inHz #carrier frequency in Hz
        self.fs_inHz = fs_inHz #time domain data sample rate in Hz,
        self.scs = scs #subcarrier bandwidth, 15 or 30

        self.num_of_sinusoids = channel_model_config["num_of_sinusoids"] #used for Rayleigh or Rician channel

        #validate
        assert fs_inHz in np.array([1,2,4,8,16,32])*30720000
        assert self.Nt in [1,2,4,8]
        assert self.Nr in [1,2,4,8]
        if self.Rspat.shape[0] == 1:
            assert self.Rspat.shape[0]==self.Nt*self.Nr
        else:
            assert len(self.Rspat.shape)==2 and self.Rspat.shape[0]==self.Rspat.shape[1] and self.Rspat.shape[0]==self.Nt*self.Nr
        assert scs in [15,30]

        self.gen_info() #generate necessary info
        
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
    
    def gen_Dm(self,numofslots):
        # return the timing error for each symbol in the waveform
        # timing error is timing offset * rho - fractional TA 
        
        Dm = np.zeros((numofslots, 14)) #
        Terror = 0
        for slot in range(numofslots):
            Dm[slot] = self.symbols_offset_list * 1e-9 * self.rho + Terror - self.TA_frac

            #update error,self.Terror point to next slot timing error
            if self.scs == 15:
                Terror += 10**(-3) * self.rho #1ms timing error
            else:
                Terror += 10**(-3)/2 * self.rho #0.5ms timing error
        
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
        if self.multi_paths:
            tap_sum = np.zeros((self.Nr,N),'c8')
            for path in self.multi_paths:
                #get "delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for    Rician"
                tap_delay = path[0]*10**(-9)
                tap_power_db = path[1]
                tap_channel = path[2] #Rayleigh or Rician
                K = path[3]
                fDo = path[4]

                #generate MIMO channel response
                tap_MIMO_response = MIMO_fading_channel.gen_mimo_channel(self.Nt, self.Nr,  self.Rspat, N, self.fs_inHz,tap_channel, K, fDo,self.fm_inHz,self.num_of_sinusoids)

                tap_o = np.zeros((self.Nr,N),'c8')
                for n in range(N):
                    tap_o[:,n] = tap_MIMO_response[n] @ tx_o2[:,n]

                tap_o *= 10**(tap_power_db/20)
                tap_delay_normalize = int(np.round(tap_delay*self.fs_inHz))
                if tap_delay_normalize >= 0:
                    tap_sum[:,tap_delay_normalize:] += tap_o[:,0:N-tap_delay_normalize]
                else:
                    tap_sum[:,0:N-tap_delay_normalize] += tap_o[:,tap_delay_normalize]
        else:
            #no taps
            tap_sum = tx_o2    

        # step 4: add noise if Pnoise_dB!= 255
        if self.Pnoise_dB != 255:
            tap_sum += np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_sum.shape) + \
                1j * np.random.normal(0, 10**(self.Pnoise_dB/20)/np.sqrt(2), tap_sum.shape)
        
        return tap_sum

def gen_channel_model_config(model_format="AWGN", Rspat_config=["customized","uniform","DL",[0,0]],Nt=1,Nr=1, Timeoff_ns=0,rho=0,fm_inHz=0,multi_paths=[[0,0,"Rayleigh",0,0]], fDo_in_Hz=0,Rspat_in=np.empty(0),DSdesired=100):
    """ generate channel model config which is used to create NrChannelModel class
    input:
        model_format:["AWGN", "TDL-A", "TDL-B", "TDL-C", "TDL-D", "TDL-E", "customized"]
            "AWGN" is the simplest channel, with Timeoff_ns and freq offset  fDo, and identity Rspat
            "TDL-A", "TDL-B", "TDL-C", "TDL-D" are based on 3GPP spec, refer to nr_TDL_channel.py
            "customized": multipaths infor comes from multi_paths input
        Rspat_config: used to generate MIMO Channel Correlation Matrices, refer to nr_spatial_correlation_matrix.py, the list values are:[MIMOCorrelation, Polarization,direction,parameters]
        
        Nt, Nr: tx and rx antenna number,
        
        Timeoff_ns: timing offset in ns
        
        rho: transmitter relative frequency offset
        
        fm_inHz: maximum doppler frequency offset in Hz
        
        multi_paths: list that contain taps info:[delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician",]

        fDo: doppler freq offset

        Rspat_in: if Rspat_config is empty, use this MIMO Channel Correlation Matrices

        DSdesired: 7.7.3 Scaling of delays in ns
            DS_desired_in_ns_Table_7_7_3_1 = {
            "Very short":10, "Short":30, "Nominal":100, "Long":300, "Very long":1000 
            }

    output:
        channel_model_config
    """
    #default_channel_model.json define channel_model_config format
    channel_model_config = {}
    channel_model_config["num_of_sinusoids"] = 30
    
    channel_model_config["Nt"] = Nt
    channel_model_config["Nr"] = Nr
    channel_model_config["Timeoff_ns"] = Timeoff_ns
    channel_model_config["rho"] = rho
    channel_model_config["fm_inHz"] = fm_inHz
    channel_model_config["fDo_in_Hz"] = fDo_in_Hz
    
    if model_format == "AWGN":
        channel_model_config["multi_paths"] = []
    elif model_format in ["TDL-A", "TDL-B", "TDL-C", "TDL-D", "TDL-E"]:
        channel_model_config["multi_paths"] = nr_TDL_channel.get_TDL_model_config(model_format,DSdesired,fm_inHz)
    elif model_format == "customized":
        #may need add code to check multi_paths parameters
        channel_model_config["multi_paths"] = multi_paths
    else:
        assert 0
    
    if Rspat_config:
        MIMOCorrelation, Polarization,direction,parameters = Rspat_config
        Rspat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt, Nr,Polarization,direction,MIMOCorrelation,parameters)
    else:
        if Rspat_in.size == 0: #empty
            Rspat = np.identity(Nt*Nr, 'c8')
        else:
            assert Rspat_in.shape[0] == Rspat_in[1] and Rspat_in.shape[0] == Nt*Nr
            Rspat = Rspat_in
    
    if model_format == "AWGN":
        #this AWGN Rspat is useless
        channel_model_config["Rspat"] = np.identity(Nt*Nr,'c8')
    else:
        channel_model_config["Rspat"] = Rspat

    return channel_model_config

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
    
