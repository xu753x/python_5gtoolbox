# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import rayleigh_channel
from py5gphy.channel_model import rician_channel

class SISO_FadingChannel():
    """generate SISO fading channel,
    fading channel could be Rayleigh or Rician
    """
    def __init__(self,num_taps, tap_config_list,samplerate_in_hz):
        """
        num_taps: number of multipath taps. each tap could be Rayleigh or Rician channel
        tap_config_list: tap configuration for each tap
        tap_config include:
            path_delay_in_ns
            path_gain_in_db
            path_type: "Rayleigh" or "Rician"
            K_factor: used for Rician channel
            fmax: Maximum Doppler shift (Hz)
            num_of_sinusoids: Number of sinusoids used to generate Rayleigh filter
        samplerate_in_hz: Input signal sample rate (Hz)
        """
        self.num_taps = num_taps
        self.tap_config_list = tap_config_list
        self.samplerate_in_hz = samplerate_in_hz

    def gen_tap_filters(self,num_of_sample):
        """ generate channel filter for all taps"""
        samplerate_in_hz = self.samplerate_in_hz
        
        tap_filters_list = np.zeros((self.num_taps,num_of_sample), 'c8')
        tap_delay_in_sample_list = np.zeros(self.num_taps, 'i2')
        for tap in range(self.num_taps):
            tap_config = self.tap_config_list[tap]
            #read config
            path_delay_in_ns = tap_config["path_delay_in_ns"]
            path_gain_in_db = tap_config["path_gain_in_db"]
            path_type = tap_config["path_type"]
            K = tap_config["K_factor"]
            fmax = tap_config["fmax"]
            num_of_sinusoids = tap_config["num_of_sinusoids"]

            if path_type == "Rayleigh":
                filter_coeff = rayleigh_channel.gen_RayleighChannel_filters(num_of_sample, fmax, samplerate_in_hz, num_of_sinusoids)
            else:
                filter_coeff = rician_channel.gen_RicianChannel_filters(num_of_sample,K, fmax,samplerate_in_hz,num_of_sinusoids)
            
            #gain update
            filter_coeff = 10**(path_gain_in_db/20)*filter_coeff
            tap_filters_list[tap,:] = filter_coeff[0:num_of_sample]

            #Tap Adjustment
            #path_delay_in_ns may not coincide with the integer multiples of the sampling period
            #it need adjust filter_coeff for discrete time data
            # two ways to do so:
            # one is rounding method to shift tap into closest sample
            # another is interpolation, linear interpolation(also used in matlab fadingchannel model) is enough
            # here support rounding method to make it simple
            tap_delay_in_sample_list[tap] = int(np.round(path_delay_in_ns * (10**-9) * samplerate_in_hz))

        return tap_filters_list,tap_delay_in_sample_list

    def filter(self, signal_in):
        """signal_in go through fading channel
        """
        num_of_sample = signal_in.size
        tap_filters_list,tap_delay_in_sample_list = self.gen_tap_filters(num_of_sample)

        #filter
        signal_out = np.zeros(num_of_sample, 'c8')
        for tap in range(self.num_taps):
            tap_delay_in_sample = tap_delay_in_sample_list[tap]
            tap_filters = tap_filters_list[tap]

            filtered = tap_filters[0:num_of_sample-tap_delay_in_sample] * signal_in[0:num_of_sample-tap_delay_in_sample]
            signal_out[tap_delay_in_sample:] += filtered
        
        return signal_out,tap_filters_list,tap_delay_in_sample_list

if __name__ == "__main__":
    #test
    num_taps = 2
    tap_config_list=[
        {"path_delay_in_ns":0,"path_gain_in_db":2,"path_type":"Rayleigh","K_factor":0, "fmax":0,"num_of_sinusoids":2},
        {"path_delay_in_ns":6,"path_gain_in_db":3,"path_type":"Rician","K_factor":1, "fmax":0,"num_of_sinusoids":2}
    ]
    samplerate_in_hz = 245760000

    sISO_FadingChannel = SISO_FadingChannel(num_taps, tap_config_list, samplerate_in_hz)
    signal_in = np.ones(20)

    signal_out,tap_filters_list,tap_delay_in_sample_list = sISO_FadingChannel.filter(signal_in)
    pass