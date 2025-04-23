# -*- coding: utf-8 -*-
import numpy as np
import math

from scripts.internal import default_config_files
from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.channel_model import nr_TDL_channel
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.nr_csirs import nr_csirs

"""
This example shows how to compute downlink channel state information (CSI) parameters such as 
the channel quality indicator (CQI), precoding matrix indicator (PMI), and rank indicator (RI), 
for multiple input multiple output (MIMO) scenarios, as defined in TS 38.214 Section 5.2.2, 
over a tapped delay line (TDL) channel. 
The example supports CSI parameter computation for the type I single-panel and antenna port number 2 and 4

"""
def _get_CSI_RS_cfg(row):
    """
    38.211 Table 7.4.1.5.3-1: CSI-RS locations within a slot
    """
    assert row in [1,2,3,4,5] #support at most 4 antenna port
    nrofPorts = [1,1,2,4,4][row-1]
    cdm_type=["noCDM","noCDM","fd-CDM2","fd-CDM2","fd-CDM2"][row-1]
    density = [3,[1,0.5],[1,0.5],1,1][row-1]
    return nrofPorts,cdm_type,density

#first read default configurations
default_DL_config = default_config_files.read_DL_default_config_files()
waveform_config = default_DL_config["DL_waveform_config"]
carrier_config = default_DL_config["DL_carrier_config"]
ssb_config = default_DL_config["ssb_config"]
csirs_config = default_DL_config["csirs_config"]
csirs_report_config = default_DL_config["csirs_report_config"]

ssb_config["enable"] = 'False'
pdcch_config_list = []
search_space_list = []
coreset_config_list = []
pdsch_config_list = []
csirs_config_list=[]
csirs_config_list.append(csirs_config)

#select CSI-RS report config
#'table1':64QAM, 'table2':256QAM, 'table3':64QAM with low Spectral efficient"
csirs_report_config["CQITable"] = "table1"
csirs_report_config["CQIMode"] = "Subband" #('Subband', 'Wideband')
csirs_report_config["PMIMode"] = "Subband" ##('Subband', 'Wideband')
csirs_report_config["SubbandSize"] = 8 #need match 38.214 Table 5.2.1.4-2: Configurable subband sizes
csirs_report_config["CodebookMode"] = 1 #Codebook mode according to which the codebooks are derived. The value must be 1 or 2

#select CSI-RS config
csirs_config["periodicity"] = 10
csirs_config["nrofRBs"] = 52
row_number = 3 #38.211 Table 7.4.1.5.3-1: CSI-RS locations within a slot

#update CSI-RS config and carrier config based on selected CSI-RS config
nrofPorts,cdm_type,density = _get_CSI_RS_cfg(row_number)
if row_number in [2,3]: #two density option[1,0.5]
    density = density[0] #choose density

csirs_config["frequencyDomainAllocation"]["row"] = row_number
csirs_config["nrofPorts"] = nrofPorts
csirs_config["cdm_type"] = cdm_type
csirs_config["density"] = density

carrier_config["num_of_ant"] = nrofPorts
carrier_config["maxMIMO_layers"] = nrofPorts
carrier_config["BW"] = 40 #make sure carrier PRB size >=csirs_config["nrofRBs"]

#waveform config
waveform_config["numofsubframes"] = 10

#simulation config
SNRdB_list = [0,10,20] #SNR in dB list
total_tests = 10 #total tests
nRxAnts = 4 #number of rx antenna
nrTDLChannel = nr_TDL_channel.NrTDLChannel(model='TDL-A', fD_in_Hz=0, DS_desired_in_ns = 20, direction="DL",Nt=nrofPorts, Nr=nRxAnts,
                MIMOCorrelation="high", Polarization="uniform",SampleRate_in_Hz=245760000,num_of_sinusoids=50)

#get paramteres
startSFN = waveform_config["startSFN"]
startslot = waveform_config["startslot"]

# main processing
nrCSIRS = nr_csirs.NrCSIRS(carrier_config, csirs_config)

for snr_dB in SNRdB_list:
    for test in range(total_tests):
        #generate transmission waveforma
        fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config, ssb_config, 
                    pdcch_config_list, search_space_list, coreset_config_list, 
                    csirs_config_list, pdsch_config_list)

        #go through fading channel
        signal_out,MIMO_tap_filters_list, tap_delay_in_sample_list = nrTDLChannel.filter(dl_waveform)

        #add AWGN. assume complex signal mean power = 1
        #complex noise power = 1/10^(snr_dB/10), real part and imag part of noise power = 1/(2*10^(snr_dB/10)) of complex noise power
        #standard deviation = 1/sqrt(2*10^(snr_dB/10))
        stand_var = 1/math.sqrt(2*10^(snr_dB/10))
        noise = np.random.normal(0, stand_var, size=signal_out.shape) + 1j*np.random.normal(0, stand_var, size=signal_out.shape)
        signal_out += noise

        #FIR filter and downsample
        sample_rate_in_hz = int(waveform_config["samplerate_in_mhz"]*(10**6))
        td_waveform = rx_lowphy_process.channel_filter(signal_out, carrier_config,sample_rate_in_hz)

        #low phy receiving processing for each slot
        scs = carrier_config["scs"]
        num_slots = int(waveform_config["numofsubframes"]*scs/15)
        samples_in_one_slot = int(sample_rate_in_hz/1000*15/scs)
        for idx in range(num_slots):
            #get sfn and slot
            sfn = startSFN + int((startslot+idx)//(scs/15*10))
            slot = (startslot+idx) % int(scs/15*10)

            if nrCSIRS.is_valid_slot(sfn,slot) == False:
                break #break for loop if not CSI-RS slot

            td_slot = td_waveform[:,idx*samples_in_one_slot:(idx+1)*samples_in_one_slot]
            #does phase correction,remove CP, FFT
            fd_slot = rx_lowphy_process.Rx_low_phy(td_slot, carrier_config, sample_rate_in_hz)

            #CSI-RS channel estimation

            #RI,PMI,CQI estimation

        #find CSI-RS slot
        #start CSI-RS processing


