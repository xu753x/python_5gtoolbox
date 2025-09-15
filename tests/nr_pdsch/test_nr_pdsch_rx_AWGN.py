# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json
import copy
import time

from tests.nr_pdsch import nr_pdsch_testvectors
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.common import nr_slot
from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.nr_pdsch import nr_pdsch_dmrs
from py5gphy.channel_estimate import nr_channel_estimation
from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.channel_model import nr_channel_model
from py5gphy.channel_model import AWGN_channel_model
from py5gphy.channel_model import nr_spatial_correlation_matrix

def get_pdsch_carrier_testvectors_list():
    """ generate test vectors"""
    BW_scs_map = {15:[20],
                  30:[40]}
            
    Nt_Nr_list = [[1,1],[1,2],[1,4],[2,2],[2,4],[4,4]]
    #Nt_Nr_list = [[1,1],[2,2],[4,4]]
    mcs_index_list = [1,5,11,20] #QPSK,16QAM,64QAM,256QAM

    carrier_freq = 3840 * 1e6 #3840MHz
    
    #gen default waveform_config
    waveform_config = {}
    waveform_config["numofslots"] = 1 #one slot only waveform
    waveform_config["startSFN"] = 0
    
    #default carrier config:
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["carrier_frequency_in_mhz"] = carrier_freq* 1e-6 # with phase compensation
        
    #default pdsch : 2 aDMRS symbol, occupy from sym 2 to 13
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    pdsch_config['mcs_table'] = "256QAM"
    pdsch_config['DMRS']['nNIDnSCID'] = 1
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 1
    pdsch_config['DMRS']['DMRSAddPos'] = 1
    pdsch_config["precoding_matrix"] = np.empty(0)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["rv"] = [0]

    pdsch_config['StartSymbolIndex'] = 2
    pdsch_config['NrOfSymbols'] = 12
    pdsch_config['ResAlloType1']['RBStart'] = 0    

    pdsch_carrier_testvectors_list = []
    slot = 0
    for scs  in [30, 15]:
        BW_list = BW_scs_map[scs]
        for BW in BW_list:
            carrier_config["scs"] = scs
            carrier_config["BW"] = BW
            
            carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW )
            ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)

            no_HB_sample_rate_in_hz = ifftsize * scs * 1000 #sample rate without HB filter
            sample_rate_in_hz = no_HB_sample_rate_in_hz * 2 #sample rate after HB filter

            waveform_config["samplerate_in_mhz"] = sample_rate_in_hz/(10**6)
            waveform_config["startslot"] = slot
            slot = (slot+1) % int(10*scs/15) #slot rotate in [0:19]

            for Nt,Nr in Nt_Nr_list:
                carrier_config["num_of_ant"] = Nt
                carrier_config["Nr"] = Nr
                pdsch_config['num_of_layers'] = carrier_config["num_of_ant"]
                if Nt >2 and Nr > 2:
                    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 2
                else:
                    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = 1

                for mcs_index in mcs_index_list:
                    pdsch_config['mcs_index'] = mcs_index                    #for RBSize in [carrier_prb_size//4,carrier_prb_size//2, carrier_prb_size]:
                    for RBSize in [20]:
                        pdsch_config['ResAlloType1']['RBSize'] = RBSize                                            
                        pdsch_carrier_testvectors_list.append([
                            copy.deepcopy(waveform_config),
                            copy.deepcopy(carrier_config),
                            copy.deepcopy(pdsch_config)])
    
    return pdsch_carrier_testvectors_list

def get_channel_parameter_list():
    channel_model_list = [
    #model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] for MIMO spat
        ["AWGN",     0,          0,    0,      0,         0,       [0,0]],
        ["AWGN",     1000,        0,    0,      0,         0,       [0,0]],
        ["AWGN",     200,        0,    0,      200,       0,       [0,0]], #low correlation
        ["AWGN",     1,        0,    0,      0,       0,       [0.3,0.9]], #medium
        ["AWGN",     2,        0,    0,      0,       0,       [0.9,0.9]], #high
        ]
    Pnoise_dB_list = [-30] #
    
    channel_parameter_list = []
    for channel_model in channel_model_list:
        for Pnoise_dB in Pnoise_dB_list:
            channel_parameter_list.append([copy.deepcopy(channel_model),Pnoise_dB])
    
    return channel_parameter_list

def get_channel_equ_config_list():
    CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]
    #CEQ_algo_list = ["ML-soft"]
    return CEQ_algo_list

def get_CE_config_list():
    """generate channel estimation config list
    """
    CE_config_para_list1 = [
        #CE_algo
        #"DFT",
        "DFT_symmetric",
    ]
    CE_config_para_list2 = [
        #L_symm_left_in_ns, L_symm_right_in_ns,eRB
        [1400,                 1200,              4],
        #[2800,                 2400,              4],
        
    ]

    CE_config_list = []
    for algo in CE_config_para_list1:
        CE_config={}
        CE_config["CE_algo"] = algo
        for para2 in CE_config_para_list2:
            CE_config["L_symm_left_in_ns"] = para2[0]
            CE_config["L_symm_right_in_ns"] = para2[1]
            CE_config["eRB"] = para2[2]

            CE_config_list.append(copy.deepcopy(CE_config))
    
    return CE_config_list

@pytest.mark.parametrize('pdsch_carrier_testvectors', get_pdsch_carrier_testvectors_list())
@pytest.mark.parametrize('CE_config', get_CE_config_list())
@pytest.mark.parametrize('channel_parameter', get_channel_parameter_list())
@pytest.mark.parametrize('CEQ_algo', get_channel_equ_config_list())
def test_nr_pdsch_rx_AWGN_basic(pdsch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo):
    "test PDSCH Rx processing on AWGN channel, "
    
    #read input and generate configurations
    [waveform_config,carrier_config,pdsch_config] = pdsch_carrier_testvectors

    model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    mcs_index = pdsch_config['mcs_index']
    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    

    CE_config["enable_TO_comp"] = True
    CE_config["enable_FO_est"] = False
    CE_config["enable_FO_comp"] = False
    CE_config["enable_carrier_FO_est"] = False
    CE_config["enable_carrier_FO_TO_comp"] = False
    CE_config["freq_intp_method"] = "linear" 

    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    CEQ_config = {}
    CEQ_config["algo"] = CEQ_algo
    
    #select test environment
    #if Timeoff_ns !=0 or rho !=0 or fDo_in_Hz != 0:
    #    return
    
    if Nt==1 and Nr == 1 and alpha > 0:
        return
    
    #if mcs_index <20:
    #    return

    #if [Nt,Nr] !=[2,4]:
    #    return
    
    #no ML for below condition
    if mcs_index >10 and Nt > 1 and CEQ_algo in ["ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard"]:
        return
        
    if CEQ_algo in ["opt-rank2-ML","opt-rank2-ML-IRC"] and Nt != 2:
        return
    
    
    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    TO_est = np.mean(nrChannelEstimation.TO_est)
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))
    
    if status:
        print(f"pass mcsidx{mcs_index},Nt{Nt},Nr{Nr},{CEQ_algo},Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power[[0,Nt*Nr-1]]}dB, cov_m_power={cov_m_power[[0,Nr*Nr-1]]}dB")
    else:
        print(f"failed mcsidx{mcs_index},Nt{Nt},Nr{Nr},{CEQ_algo},Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power[[0,Nt*Nr-1]]}dB, cov_m_power={cov_m_power[[0,Nr*Nr-1]]}dB")

def pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config):
    """generate tx waveform, no low phy processing,identity H matrix
    """

    #read parameters
    #read input and generate configurations
    [waveform_config,carrier_config,pdsch_config] = pdsch_carrier_testvectors

    model_format = channel_parameter[0][0]
    if model_format == "customized":
        model_format,channel, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,K,[alpha,beta] = channel_parameter[0]
        DSdesired = 0
        #for one tap channel
        #"delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician",
        multi_paths = [[0,0,channel,K,fDo_in_Hz]]
        Rspat_in = np.empty(0)
    else:
        model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
        multi_paths = []
        Rspat_in = np.empty(0)

    Pnoise_dB = channel_parameter[1]
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

    for m in range(numofslot):
        slot = startslot + m       
        
        rx_fdslot_data = rx_fd_waveform[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]

        #PDSCH channel LS estimation
        H_LS,RS_info = nrPdsch.H_LS_est(rx_fdslot_data,slot)
        
        #channel est class
        nrChannelEstimation = \
            nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
    
        H_result, cov_m = nrChannelEstimation.channel_est(fDo_in_Hz)

        #add debug code to compare channel est result
        #H_result[:,1::4,:,:] = H_result[:,0::4,:,:]
        #H_result[:,2::4,:,:] = H_result[:,0::4,:,:]
        #H_result[:,3::4,:,:] = H_result[:,0::4,:,:]
        
        status,tbblk, new_LLr_dns = \
            nrPdsch.RX_process(rx_fdslot_data,slot,CEQ_config,H_result, cov_m,LDPC_decoder_config,nrChannelEstimation)

        return status,tbblk, new_LLr_dns,nrChannelEstimation
        

    

