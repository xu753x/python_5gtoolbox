# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import nr_TDL_channel_model
from py5gphy.channel_model import nr_TDL_channel_info
from py5gphy.channel_model import MIMO_fading_channel

class NrTDLChannel():
    """TR 38.901 Tapped Delay Line (TDL) channel
    it is used to create TDL MIMO fading channel System object, and filter inpput signal through TDL MIMO channel
    following aspects of TR 38.901 are implemented:
   * Section 7.7.2 Tapped Delay Line (TDL) models
   * Section 7.7.3 Scaling of delays 
   * Section 7.7.5.2 TDL extension: Applying a correlation matrix
    """
    def __init__(self, model='TDL-A', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50):
        """
        model: TDL model
        fD: maximum Doppler shift in Hz
        DS_desired: wangted delay spread in ns by 7.7.3
            typical value is in Table 7.7.3-2. Scenario specific scaling factors - for information only
        direction: "DL" or "UL"
        Nt: Number of transmit antennas
        Nr: Number of receive antennas
        MIMOCorrelation: 
          DL and "uniform": ["high", "medium", "mediumA", "mediumB","low"]
          DL and "cross-polar": ["high", "mediumA", "low"]
          UL and "uniform": ["high", "medium","low"]
          UL and "cross-polar": ["high", "mediumA", "low"]
        Polarization: "uniform" or "cross-polar"
        SampleRate_in_Hz: Input signal sample rate (Hz)
        """
        self.model = model
        assert model in self.get_model_list()
        self.TDL_tap_config = self.get_tap_config()

        self.fD_in_Hz = fD_in_Hz
        self.DS_desired_in_ns = DS_desired_in_ns
        self.direction = direction
        self.Nt = Nt
        self.Nr = Nr
        self.MIMOCorrelation = MIMOCorrelation
        self.Polarization = Polarization
        self.SampleRate_in_Hz = SampleRate_in_Hz
        self.num_of_sinusoids = num_of_sinusoids

        #validate
        assert direction in ["DL", "UL"]                                        
        assert Polarization in ["uniform", "cross-polar"]

        #get R_spat
        if direction == "DL":
            self.R_spat = nr_TDL_channel_info.gen_DL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
        else:
            self.R_spat = nr_TDL_channel_info.gen_UL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
        
        self.mimo_FadingChannel = self.gen_MIMO_channel()

    def get_model_list(self):
        return ['TDL-A', 'TDL-B', 'TDL-C', 'TDL-D', 'TDL-E']

    def get_tap_config(self):
        """ get [Rayleigh_config, K, LOS_config]
        """
        TDL_tap_config =  nr_TDL_channel_model.get_TDL_model_config(self.model)
        return TDL_tap_config

    def gen_MIMO_channel(self):
        """generate MIMO fading channel
        """
        TDL_tap_config = self.TDL_tap_config
        
        num_taps = len(TDL_tap_config)
        tap_config_list = []
        for TDL_tap in TDL_tap_config:
            normalized_delay = TDL_tap[0]
            path_gain_in_db = TDL_tap[1]
            path_type = TDL_tap[2]
            
            K_factor = 0 if path_type=="Rayleigh" else TDL_tap[3]

            tap_config={
                "path_delay_in_ns" : normalized_delay * self.DS_desired_in_ns,
                "path_gain_in_db" : path_gain_in_db,
                "path_type" : path_type,
                "K_factor" : K_factor, 
                "fmax" : self.fD_in_Hz,
                "num_of_sinusoids":self.num_of_sinusoids
            }
            tap_config_list.append(tap_config)

        self.tap_config_list = tap_config_list

        mimo_FadingChannel = MIMO_fading_channel.MIMO_FadingChannel( \
            num_taps, tap_config_list, self.SampleRate_in_Hz,self.R_spat,self.Nt,self.Nr)
        return mimo_FadingChannel

    def filter(self, signal_in):
        """filter input signal through a TDL MIMO fading channel and returns the channel-impaired signal.
        """
        signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = self.mimo_FadingChannel.filter(signal_in)
        return signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list
    


if __name__ == "__main__":
    signal_in = np.ones((2, 400))

    nrTDLChannel = NrTDLChannel(model='TDL-A', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)
    
    signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(signal_in)

    nrTDLChannel = NrTDLChannel(model='TDL-B', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)
    
    signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(signal_in)

    nrTDLChannel = NrTDLChannel(model='TDL-C', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)
    
    signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(signal_in)

    nrTDLChannel = NrTDLChannel(model='TDL-D', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)
    
    signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(signal_in)

    nrTDLChannel = NrTDLChannel(model='TDL-E', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=2, Nr=2,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)
    
    signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(signal_in)
    pass