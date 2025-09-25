# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json
import copy
import time

from py5gphy.common import nr_slot
from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.channel_estimate import nr_channel_estimation
from py5gphy.nr_waveform import nr_ul_waveform
from py5gphy.channel_model import nr_channel_model
from py5gphy.channel_model import AWGN_channel_model
from py5gphy.channel_model import nr_spatial_correlation_matrix
from py5gphy.nr_pusch import nr_pusch

def get_pusch_carrier_testvectors_list():
    """ generate test vectors"""
    BW_scs_map = {15:[20],
                  30:[40]}
            
    Nt_Nr_list = [[1,1],[1,2],[1,4],[2,2],[2,4]]
    #Nt_Nr_list = [[1,1],[2,2],[4,4]]
    mcs_index_list = [1,5,11,20] #QPSK,16QAM,64QAM,256QAM

    carrier_freq = 3840 * 1e6 #3840MHz
    
    #gen default waveform_config
    waveform_config = {}
    waveform_config["numofslots"] = 1 #one slot only waveform
    waveform_config["startSFN"] = 0
    
    #default carrier config:
    path = "py5gphy/nr_default_config/"
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["carrier_frequency_in_mhz"] = carrier_freq* 1e-6 # with phase compensation
    carrier_config['PCI'] = 1
        
    #default pusch : 2 aDMRS symbol, occupy from sym 2 to 13
    with open(path + "default_pusch_config.json", 'r') as f:
        pusch_config = json.load(f)
    
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
    pusch_config['StartSymbolIndex'] = 0
    pusch_config['NrOfSymbols'] = 14

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
    
    pusch_carrier_testvectors_list = []
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
                pusch_config['num_of_layers'] = carrier_config["num_of_ant"]
                pusch_config['nNrOfAntennaPorts'] = carrier_config["num_of_ant"]
                
                for mcs_index in mcs_index_list:
                    pusch_config['mcs_index'] = mcs_index                    #for RBSize in [carrier_prb_size//4,carrier_prb_size//2, carrier_prb_size]:
                    for RBSize in [20]:
                        pusch_config['ResAlloType1']['RBSize'] = RBSize                                            
                        pusch_carrier_testvectors_list.append([
                            copy.deepcopy(waveform_config),
                            copy.deepcopy(carrier_config),
                            copy.deepcopy(pusch_config)])
    
    return pusch_carrier_testvectors_list

def get_channel_parameter_list():
    channel_model_list = [
    #model_format      channel, Timeoff_ns,        rho, fm_inHz, fDo_in_Hz,      K,       [alha,beta] for MIMO spat
        ["customized", "Rayleigh",  0,           0,   0,      0,       0,       [0,0] ],
        ["customized", "Rayleigh",  1,           0,   0,      0,       0,       [0,0] ],
        ["customized", "Rayleigh",  2,           0,   0,      0,       0,       [0.3,0.3] ],
        ["customized", "Rayleigh",  3,           0,   0,      0,       0,       [0.3,0.9] ],
        ["customized", "Rayleigh",  4,           0,   0,      0,       0,       [0.9,0.9] ],
        ["customized", "Rayleigh",  20,          0,   200,    0,       0,       [0,0] ],
        ["customized", "Rayleigh",  200,         0,   400,    0,       0,       [0.3,0.3] ],
        ["customized", "Rician",    5,           0,   0,      100,     10,       [0,0] ],
        ["customized", "Rician",    6,           0,   0,      100,     10,       [0.3,0.3] ],
        ["customized", "Rician",    7,           0,   0,      100,     10,       [0.3,0.9] ],
        ["customized", "Rician",    25,          0,   300,    200,     13,       [0,0] ],
        ["customized", "Rician",    8,           0,   400,    300,     13,       [0,0] ],
        ]
    Pnoise_dB_list = [-30] #[-30] #
    
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

@pytest.mark.parametrize('pusch_carrier_testvectors', get_pusch_carrier_testvectors_list())
@pytest.mark.parametrize('CE_config', get_CE_config_list())
@pytest.mark.parametrize('channel_parameter', get_channel_parameter_list())
@pytest.mark.parametrize('CEQ_algo', get_channel_equ_config_list())
def test_nr_pusch_rx_one_tap_basic(pusch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo):
    """ test PUSCH Rx processing on one tap channel, 
    no UCI,ULSCH only
    """
    
    #read input and generate configurations
    [waveform_config,carrier_config,pusch_config] = pusch_carrier_testvectors

    model_format,channel, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,K,[alpha,beta] = channel_parameter[0]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    mcs_index = pusch_config['mcs_index']
    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    

    CE_config["enable_TO_comp"] = True
    CE_config["enable_FO_est"] = False
    CE_config["enable_FO_comp"] = False
    CE_config["enable_carrier_FO_est"] = False
    CE_config["enable_carrier_FO_TO_comp"] = False

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
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = pusch_tx_and_lowphy_rx_processing(pusch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    TO_est = np.mean(nrChannelEstimation.TO_est)
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))
    if status:
        print(f"pass mcsidx{mcs_index},Nt{Nt},Nr{Nr},{CEQ_algo},model_format{model_format},Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power[[0,Nt*Nr-1]]}dB, cov_m_power={cov_m_power[[0,Nr*Nr-1]]}dB ")
    else:
        print(f"failed mcsidx{mcs_index},Nt{Nt},Nr{Nr},{CEQ_algo},model_format {model_format},Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power[[0,Nt*Nr-1]]}dB, cov_m_power={cov_m_power[[0,Nr*Nr-1]]}dB ")
    

def pusch_tx_and_lowphy_rx_processing(pusch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config):
    """
    """
    #read input and generate configurations
    [waveform_config,carrier_config,pusch_config] = pusch_carrier_testvectors

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
    
    #generate PUSCH class
    nrPusch = nr_pusch.NrPUSCH(carrier_config,pusch_config)
    nrPusch_list=[]
    nrPusch_list.append(nrPusch)
    
    #channel model
    if model_format == "AWGN":
        nrChannelModel = AWGN_channel_model.AWGNChannelModel(channel_model_config,Pnoise_dB,carrier_freq,fs_inHz,scs,fDo_in_Hz)
    else:
        nrChannelModel = nr_channel_model.NrChannelModel(channel_model_config, Pnoise_dB,carrier_freq,fs_inHz,scs)
    
    #Dm = nrChannelModel.gen_Dm(waveform_config["numofslots"])

    #gen UL waveform
    fd_waveform, td_waveform, ul_waveform = \
        nr_ul_waveform.gen_ul_waveform(waveform_config,carrier_config,
                                       nrPusch_list=nrPusch_list)

    #go through channel model
    rx_waveform = nrChannelModel.filter(ul_waveform)

    #Rx channel filter and low phy processing
    _,rx_fd_waveform = rx_lowphy_process.waveform_rx_processing(rx_waveform, carrier_config,fs_inHz)

    for m in range(numofslot):
        slot = startslot + m       
        
        rx_fdslot_data = rx_fd_waveform[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]

        #PUSCH channel LS estimation
        H_LS,RS_info = nrPusch.H_LS_est(rx_fdslot_data,slot)
        
        #channel est class
        nrChannelEstimation = \
            nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
    
        H_result, cov_m = nrChannelEstimation.channel_est(fDo_in_Hz)

        #add debug code to compare channel est result
        #H_result[:,1::4,:,:] = H_result[:,0::4,:,:]
        #H_result[:,2::4,:,:] = H_result[:,0::4,:,:]
        #H_result[:,3::4,:,:] = H_result[:,0::4,:,:]
        
        pusch_status,tbblk, new_LLr_dns = \
            nrPusch.RX_process(rx_fdslot_data,slot,CEQ_config,H_result, cov_m,LDPC_decoder_config,nrChannelEstimation)

        return pusch_status,tbblk, new_LLr_dns,nrChannelEstimation