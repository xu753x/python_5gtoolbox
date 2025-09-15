# -*- coding:utf-8 -*-
import numpy as np
import copy
import time
import pickle

from scripts.internal import sim_pdsch_throughput_internal
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.common import nr_slot
from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.nr_pdsch import nr_pdsch_dmrs

##################### #parameters selected for the test ##################
#test channel equaliztion algorithm performance , no channel estimation, no low-phy processing,

Nt, Nr = [1,1] #number of Tx antenna and Rx antenna
mcs_idx = 2 #[1,5,11,20] for QPSK,16QAM,64QAM,256QAM
pdsch_prb_size = 40 #

SNR_dB_list = np.arange(-2, 6, 0.5).tolist() #SNR power

#channel equalization parameters
#totally_supported_CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]

CEQ_algo_list = ["ZF-IRC","MMSE-IRC","ML-IRC-soft","MMSE-ML-IRC"]
#CEQ_algo_list = ["MMSE-IRC","ML-soft"]

#some general parameters
carrier_freq= 3840 * 1e6 #3840MHz
BW,scs = [40,30] #40MHz, 30KHz scs

# Simulation configuration ######
num_of_sim = 1 #number of simulation

#this test takes very long time, we usually run the test once, then save the test results, then analyze the result.
# 1 means run the test, after the test, set it to 0 to analyze the result
sim_flag = 1 

#test result dump to file
save_filename = "out/nr_pdsch_throughput_2.pickle"
figfile = "out/nr_pdsch_throughput_2.png" 
####################

########## generate configurations used for the test ###################
carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW )
ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)

no_HB_sample_rate_in_hz = ifftsize * scs * 1000 #sample rate without HB filter
sample_rate_in_hz = no_HB_sample_rate_in_hz * 2 #sample rate after HB filter

# read default configuration
from scripts.internal import default_config_files
default_DL_config = default_config_files.read_DL_default_config_files()
waveform_config = default_DL_config["DL_waveform_config"]
carrier_config = default_DL_config["DL_carrier_config"]
pdsch_config = default_DL_config["pdsch_config"]  

#### waveform and carrier  configuration ######
#set waveform config
waveform_config["numofslots"] = 1 #waveform length in 1ms subframe
waveform_config["startSFN"] = 0
waveform_config["startslot"] = 0
waveform_config["samplerate_in_mhz"] = sample_rate_in_hz/(1e6)

#set carrier config
carrier_config["BW"] = BW #bandwidth in MHz
carrier_config["scs"] = scs #15khz or 30KHz
carrier_config["PCI"] = 1 #physical layer cell identity in range 0 - 1007
carrier_config["carrier_frequency_in_mhz"] = carrier_freq/(1e6) #carrier central freq
carrier_config["num_of_ant"] = Nt #number of Tx antenna
carrier_config["Nr"] = Nr #number of Rx antenna
carrier_config["maxMIMO_layers"] = Nt

## PDSCH configuration ########
#set PDSCH config, pdsch_config_list contain one PDSCH config
pdsch_config["mcs_index"] = mcs_idx #[1,5,11,20] maps to [QPSK,16QAM,64QAM,256QAM]
pdsch_config["num_of_layers"] = carrier_config["num_of_ant"]
pdsch_config['ResAlloType1']['RBSize'] = pdsch_prb_size #make sure it is smaller than carrier_prb_size

pdsch_config['mcs_table'] = "256QAM"
pdsch_config['DMRS']['nNIDnSCID'] = 1
if pdsch_config["num_of_layers"] >2:
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 2 #should be 2 if pdsch_config["num_of_layers"] > 2
else:
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 1 #should be 2 if pdsch_config["num_of_layers"] > 2
pdsch_config['DMRS']['DMRSAddPos'] = 1
pdsch_config["precoding_matrix"] = np.empty(0)
pdsch_config["data_source"] = [1,0,0,1]
pdsch_config["rv"] = [0]
pdsch_config['StartSymbolIndex'] = 2
pdsch_config['NrOfSymbols'] = 12
pdsch_config['ResAlloType1']['RBStart'] = 0    
#PDSCh codebook
pdsch_config["codebook"]["enable"] = "False" # no codebook based precoding

#### LDPC decoder configuration #######
LDPC_decoder_config = {
    "L":32, "algo":"min-sum", "alpha":0.8, "beta":0.3
}

################# main procedure ###############
#generate PDSCH class
nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
nrPdsch_list=[]
nrPdsch_list.append(nrPdsch)

num_of_ant = carrier_config["num_of_ant"]

#generate identity H_result and identitycov_m
RE_num = pdsch_config["ResAlloType1"]["RBSize"] * 12
H_result = np.zeros((14,RE_num,num_of_ant,num_of_ant),'c8')
cov_m = np.zeros((14,RE_num,num_of_ant,num_of_ant),'c8')

for nr in range(num_of_ant):
    H_result[:,:,nr,nr] = 1
    
if sim_flag:
    failed_counts = np.zeros((len(CEQ_algo_list),len(SNR_dB_list)),'i2')
    for m1,SNR_dB in enumerate(SNR_dB_list):
        Pnoise_dB = -SNR_dB
        for nr in range(num_of_ant):
            cov_m[:,:,nr,nr] = 10**(Pnoise_dB/10)

        for sim in range(num_of_sim):
            fd_waveform, td_waveform, dl_waveform,td_waveform_sample_rate_in_hz = \
                nr_dl_waveform.gen_dl_waveform(waveform_config,carrier_config,
                                       nrPdsch_list=nrPdsch_list)

            rx_fdslot_data = fd_waveform + np.random.normal(0, 10**(Pnoise_dB/20)/np.sqrt(2), fd_waveform.shape) + \
                1j * np.random.normal(0, 10**(Pnoise_dB/20)/np.sqrt(2), fd_waveform.shape)
            
            for m2, CEQ_algo in enumerate(CEQ_algo_list):
                CEQ_config={"algo":CEQ_algo}

                start_time = time.time()
                status,tbblk, new_LLr_dns = \
                    nrPdsch.RX_process(rx_fdslot_data,waveform_config["startslot"],CEQ_config,H_result, cov_m,LDPC_decoder_config)
                end_time = time.time()
                elapsed_time = end_time - start_time

                #check result
                mean_llr = np.mean(np.abs(new_LLr_dns))
                if status:
                    print(f"pass, sim={sim},{CEQ_algo}, SNR_dB={SNR_dB},Elapsed Time: {elapsed_time:.2f} seconds,mean_llr={mean_llr:.2f}")
                else:
                    failed_counts[m2,m1] += 1
                    print(f"failed, sim={sim},{CEQ_algo}, SNR_dB={SNR_dB},Elapsed Time: {elapsed_time:.2f} seconds,mean_llr={mean_llr:.2f}")
                
    #get BLER
    bler_results = failed_counts / num_of_sim

    #save results
    with open(save_filename, 'wb') as handle:
        pickle.dump([bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pdsch_config,channel_parameter,CE_config], handle, protocol=pickle.HIGHEST_PROTOCOL)

with open(save_filename, 'rb') as handle:
    [bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pdsch_config,channel_parameter,CE_config] = pickle.load(handle)

    sim_pdsch_throughput_internal.draw_pdsch_throughput_result(bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pdsch_config,channel_parameter,CE_config, figfile)


    