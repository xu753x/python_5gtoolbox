# -*- coding:utf-8 -*-
import numpy as np
import copy
import matplotlib.pyplot as plt

from  py5gphy.channel_model import nr_channel_model
from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.common import nr_slot
from py5gphy.nr_pdsch import nr_pdsch
from tests.nr_pdsch import test_nr_pdsch_rx_AWGN
from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.channel_model import nr_channel_model
from py5gphy.channel_model import AWGN_channel_model
from py5gphy.channel_estimate import nr_channel_estimation

def pdsch_before_CEQ_processing(waveform_config,carrier_config,pdsch_config,channel_parameter,CE_config,Pnoise_dB):
    """include:
    PDSCH tx processing, tx low-phy, go through channel,rx low-phy, PDSCH channel estimation
    """

    #read parameters
    model_format = channel_parameter[0]
    if model_format == "customized":
        model_format,channel, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,K,[alpha,beta] = channel_parameter
        DSdesired = 0
        #for one tap channel
        #"delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician",
        multi_paths = [[0,0,channel,K,fDo_in_Hz]]
        Rspat_in = np.empty(0)
    else:
        model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter
        multi_paths = []
        Rspat_in = np.empty(0)

    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    Nt = carrier_config["num_of_ant"] 
    Nr = carrier_config["Nr"] 
    scs = carrier_config["scs"]
    carrier_freq = carrier_config["carrier_frequency_in_mhz"] * 1e6
    fs_inHz = waveform_config["samplerate_in_mhz"] * 1e6
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    numofslot = waveform_config["numofslots"]
    startslot = waveform_config["startslot"]

    #generate channel model config
    channel_model_config = nr_channel_model.gen_channel_model_config(model_format,Rspat_config,Nt, Nr,Timeoff_ns,rho,fm_inHz,multi_paths,fDo_in_Hz,Rspat_in,DSdesired)
    
    
    #generate PDSCH class
    nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    nrPdsch_list=[]
    nrPdsch_list.append(nrPdsch)
    
    #channel model
    if model_format == "AWGN":
        nrChannelModel = AWGN_channel_model.AWGNChannelModel(channel_model_config,Pnoise_dB,carrier_freq,fs_inHz,scs,fDo_in_Hz)
    else:
        nrChannelModel = nr_channel_model.NrChannelModel(channel_model_config, Pnoise_dB,carrier_freq,fs_inHz,scs)
    
    Dm = nrChannelModel.gen_Dm(waveform_config["numofslots"])

    #gen DL waveform
    _, _, dl_waveform,td_waveform_sample_rate_in_hz = \
        nr_dl_waveform.gen_dl_waveform(waveform_config,carrier_config,
                                       nrPdsch_list=nrPdsch_list,Dm=Dm)

    #go through channel model
    rx_waveform = nrChannelModel.filter(dl_waveform)

    #Rx channel filter and low phy processing
    _,rx_fd_waveform = rx_lowphy_process.waveform_rx_processing(rx_waveform, carrier_config,fs_inHz)

    slot = startslot
    
    rx_fdslot_data = rx_fd_waveform[:,0:carrier_prb_size*12*14]

    #PDSCH channel LS estimation
    H_LS,RS_info = nrPdsch.H_LS_est(rx_fdslot_data,slot)
    
    #channel est class
    nrChannelEstimation = \
        nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
    
    H_result, cov_m = nrChannelEstimation.channel_est(fDo_in_Hz)
    
    return nrPdsch,rx_fdslot_data,slot,H_result,cov_m,nrChannelEstimation
        

def pdsch_CEQ_processing(nrPdsch,rx_fdslot_data,slot,H_result,cov_m,LDPC_decoder_config,nrChannelEstimation,CEQ_config):
    status,tbblk, new_LLr_dns = \
        nrPdsch.RX_process(rx_fdslot_data,slot,CEQ_config,H_result, cov_m,LDPC_decoder_config,nrChannelEstimation)

    return status,tbblk, new_LLr_dns,nrChannelEstimation

def draw_pdsch_throughput_result(bler_results, SNR_dB_list,CEQ_algo_list,waveform_config,carrier_config,pdsch_config,channel_parameter,CE_config, figfile):
    #get info
    model_format = channel_parameter[0]
    Nt, Nr = [carrier_config["num_of_ant"],carrier_config["Nr"]]
    mcs_index = pdsch_config["mcs_index"]
    CE_algo = CE_config["CE_algo"]

    #draw the picture
    fig = plt.figure()
    marker_list = [".","o","v","<",">","P","*","+","x","D","d"]
    marker_count = 0
    plt.xlabel("SNR")
    plt.ylabel("BLER")
    plt.title(f"PDSCH throughpuy, {model_format}, [Nt,Nr]={[Nt, Nr]},mcs_index={mcs_index},CE_algo={CE_algo} ")
    
    plt.yscale("log")
    plt.xlim(SNR_dB_list[0],SNR_dB_list[-1])
    plt.ylim(10**(-4),1)
    plt.grid(True)

    for idx, CEQ_algo in enumerate(CEQ_algo_list):
        
        set_label = "{}".format(CEQ_algo)
        
        yd = bler_results[idx,:]
        plt.plot(SNR_dB_list, yd, marker=marker_list[marker_count], label=set_label)
        marker_count =(marker_count+1) % len(marker_list)

    plt.legend(loc="upper right",fontsize=5)
    plt.savefig(figfile) #plt.show() didn't work if remotely accessing linux platform, save to picture
    plt.close(fig)
    plt.pause(0.01)