# -*- coding:utf-8 -*-
import numpy as np
import copy
import time
import pickle

from scripts.internal import sim_pusch_throughput_internal
from py5gphy.common import nr_slot

##################### #parameters selected for the test ##################
#test channel equaliztion algorithm performance under AWGN channel,

Nt, Nr = [2,4] #number of Tx antenna and Rx antenna
#38.214 Table 5.1.3.1-2: MCS index table 2 for PUSCH if transform precoding is disabled
mcs_idx = 5 #[1,5,11,20] for QPSK,16QAM,64QAM,256QAM
pusch_prb_size = 20 #

#channel
channel_format = "customized" #"AWGN", "customized", "TDL"

if channel_format == "AWGN": #AWGN
    channel_parameter = ["AWGN",     0,          0,    0,      0,         0,       [0,0]]
    #channel_parameter = ["AWGN",     0,          0,    0,      200,         0,       [0,0]]
elif channel_format == "customized":
    channel_parameter = ["customized", "Rayleigh",  0,           0,   0,      0,       0,       [0,0] ]
    #channel_parameter = ["customized", "Rayleigh",  20,          0,   200,    0,       0,       [0,0] ]
    #channel_parameter = ["customized", "Rician",    0,           0,   0,      100,     10,       [0.3,0.9] ]
else:
    #TDL
    channel_parameter = ["TDL-A",     0,           0,   0,      0,       100,       [0,0] ]
    #channel_parameter = ["TDL-D",     0,           0,   400,      0,       200,       [0,0] ],

SNR_dB_list = np.arange(0, 8, 1).tolist() #SNR power

#channel estimation parameters
CE_config={"CE_algo":"DFT_symmetric","L_symm_left_in_ns":1400,"L_symm_right_in_ns":1200,"eRB":4,
           "enable_TO_comp": True,"enable_FO_est": False,"enable_FO_comp": False}

#channel equalization parameters
#totally_supported_CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]

#CEQ_algo_list = ["ZF", "ZF-IRC","MMSE","MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]
CEQ_algo_list = ["MMSE-IRC"]

#some general parameters
carrier_freq= 3840 * 1e6 #3840MHz
BW,scs = [40,30] #40MHz, 30KHz scs

# Simulation configuration ######
num_of_sim = 40 #number of simulation

#this test takes very long time, we usually run the test once, then save the test results, then analyze the result.
# 1 means run the test, after the test, set it to 0 to analyze the result
sim_flag =  1

#test result dump to file
save_filename = "out/nr_pusch_throughput_2_8.pickle"
figfile = "out/nr_pduch_throughput_2_8.png" 
####################

########## generate configurations used for the test ###################
carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW )
ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)

no_HB_sample_rate_in_hz = ifftsize * scs * 1000 #sample rate without HB filter
sample_rate_in_hz = no_HB_sample_rate_in_hz * 2 #sample rate after HB filter

# read default configuration
from scripts.internal import default_config_files
default_UL_config = default_config_files.read_UL_default_config_files()
waveform_config = default_UL_config["UL_waveform_config"]
carrier_config = default_UL_config["UL_carrier_config"]
pusch_config = default_UL_config["pusch_config"]  

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

## PUSCH configuration ########
#set PUSCH config,
pusch_config["mcs_index"] = mcs_idx #[1,5,11,20] maps to [QPSK,16QAM,64QAM,256QAM]
pusch_config["num_of_layers"] = carrier_config["num_of_ant"]
pusch_config['nNrOfAntennaPorts'] = carrier_config["num_of_ant"]
pusch_config['ResAlloType1']['RBSize'] = pusch_prb_size

pusch_config['mcs_table'] = "256QAM"
pusch_config['nTpPi2BPSK'] = 0
pusch_config['nTransPrecode'] = 0
pusch_config['nTransmissionScheme'] = 1
pusch_config['DMRS']['dmrs_TypeA_Position'] = "pos2"
pusch_config['DMRS']['nSCID'] = 0
pusch_config['DMRS']['DMRSConfigType'] = 1
pusch_config['DMRS']['NrOfDMRSSymbols'] = 1
pusch_config['DMRS']['NumCDMGroupsWithoutData'] = 2
pusch_config['DMRS']['DMRSAddPos'] = 1
pusch_config['DMRS']['PUSCHMappintType'] = 'A'
pusch_config['DMRS']['transformPrecodingDisabled']['NID0'] = 10
pusch_config['DMRS']['transformPrecodingDisabled']['NID1'] = 20
pusch_config['DMRS']['transformPrecodingEnabled']["nPuschID"] = 30
pusch_config['DMRS']['transformPrecodingEnabled']["groupOrSequenceHopping"] = "neither"
pusch_config['VRBtoPRBMapping'] = "non-interleaved"
pusch_config['nPMI'] = 0
pusch_config['StartSymbolIndex'] = 2
pusch_config['NrOfSymbols'] = 8
pusch_config['ResAlloType1']['RBStart'] = 0

pusch_config["data_source"] = [1,0,0,1]
pusch_config["rv"] = [0]

pusch_config['nNid'] = 1
pusch_config['UCIScaling'] = 1
pusch_config['EnableULSCH'] = 1

pusch_config['EnableACK'] = 0
pusch_config['NumACKBits'] = 0

pusch_config['EnableCSI1'] = 0
pusch_config['NumCSI1Bits'] = 0
pusch_config['EnableCSI2'] = 0
pusch_config['NumCSI2Bits'] = 0
    

#### LDPC decoder configuration #######
LDPC_decoder_config = {
    "L":32, "algo":"min-sum", "alpha":0.8, "beta":0.3
}

################# main procedure ###############
print(channel_parameter)
if sim_flag:
    failed_counts = np.zeros((len(CEQ_algo_list),len(SNR_dB_list)),'i2')
    for m1,SNR_dB in enumerate(SNR_dB_list):
        Pnoise_dB = -SNR_dB
        for sim in range(num_of_sim):
            nrPusch,rx_fdslot_data,slot,H_result,cov_m,nrChannelEstimation = \
                sim_pusch_throughput_internal.pusch_before_CEQ_processing(waveform_config,carrier_config,   pusch_config,channel_parameter,CE_config,Pnoise_dB)

            for m2, CEQ_algo in enumerate(CEQ_algo_list):
                CEQ_config={"algo":CEQ_algo}

                start_time = time.time()
                ulsch_status,tbblk, new_LLr_dns,nrChannelEstimation = \
                    sim_pusch_throughput_internal.pusch_CEQ_processing(nrPusch,rx_fdslot_data,slot, H_result,cov_m,LDPC_decoder_config,nrChannelEstimation,CEQ_config)
                end_time = time.time()
                elapsed_time = end_time - start_time

                #check result
                mean_llr = np.mean(np.abs(new_LLr_dns))
                if ulsch_status:
                    print(f"pass, sim={sim},{CEQ_algo}, SNR_dB={SNR_dB},Elapsed Time: {elapsed_time:.2f} seconds,mean_llr={mean_llr:.2f}")
                else:
                    failed_counts[m2,m1] += 1
                    print(f"failed, sim={sim},{CEQ_algo}, SNR_dB={SNR_dB},Elapsed Time: {elapsed_time:.2f} seconds,mean_llr={mean_llr:.2f}")
            
            print("----------------")
    #get BLER
    bler_results = failed_counts / num_of_sim

    #save results
    with open(save_filename, 'wb') as handle:
        pickle.dump([bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pusch_config,channel_parameter,CE_config], handle, protocol=pickle.HIGHEST_PROTOCOL)

with open(save_filename, 'rb') as handle:
    [bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pusch_config,channel_parameter,CE_config] = pickle.load(handle)

    sim_pusch_throughput_internal.draw_pusch_throughput_result(bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pusch_config,channel_parameter,CE_config, figfile)
