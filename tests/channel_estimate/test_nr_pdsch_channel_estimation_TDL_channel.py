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
from tests.nr_pdsch import test_nr_pdsch_rx_AWGN
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
        ["TDL-A",     0,           0,   0,      0,       100,       [0,0] ],
        ["TDL-B",     0,           0,   0,      0,       100,       [0,0] ],
        ["TDL-C",     0,           0,   0,      0,       100,       [0,0] ],
        ["TDL-D",     0,           0,   400,      0,       100,       [0,0] ],
        ["TDL-E",     0,           0,   400,      0,       100,       [0,0] ],
        ["TDL-A",     1000,           0,   0,      0,       100,       [0,0] ],
        ["TDL-B",     0,           0,   0,      0,       200,       [0.3,0.9] ],
        ["TDL-C",     0,           0,   0,      0,       400,       [0.9,0.9] ],
        ["TDL-B",     250,           0,   400,      0,       10,       [0,0] ],
        ["TDL-C",     25,           0,   400,      0,       200,       [0.3,0.3] ],
        ["TDL-D",     25,           0,   400,      0,       400,       [0.3,0.9] ],
        ["TDL-E",     125,        1e-7,   400,     0,       1000,       [0.9,0.9] ],
        ]
    Pnoise_dB_list = [-30] #[-30] #
    
    channel_parameter_list = []
    for channel_model in channel_model_list:
        for Pnoise_dB in Pnoise_dB_list:
            channel_parameter_list.append([copy.deepcopy(channel_model),Pnoise_dB])
    
    return channel_parameter_list

def get_channel_equ_config_list():
    #CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]
    CEQ_algo_list = ["MMSE-IRC"]
    return CEQ_algo_list

def get_CE_config_list():
    """generate channel estimation config list
    """
    CE_config_para_list1 = [
        #CE_algo
        "DFT", "DFT_symmetric","DCT", "DCT_symmetric",
    ]
    CE_config_para_list2 = [
        #L_symm_left_in_ns, L_symm_right_in_ns,eRB
        [1400,                 1200,              4],
        [2800,                 2400,              4],
        
    ]
    CE_config_para_list3 = [
        #freq_intp_method
        "linear","PchipInterpolator"
    ]

    CE_config_para_list4 = [
        #timing_intp_method
        "linear"
    ]

    CE_config_list = []
    for algo in CE_config_para_list1:
        CE_config={}
        CE_config["CE_algo"] = algo
        for para2 in CE_config_para_list2:
            CE_config["L_symm_left_in_ns"] = para2[0]
            CE_config["L_symm_right_in_ns"] = para2[1]
            CE_config["eRB"] = para2[2]
            for para3 in CE_config_para_list3:
                CE_config["freq_intp_method"] = para3
                for para4 in CE_config_para_list4:
                    CE_config["timing_intp_method"] = para4
                    CE_config_list.append(copy.deepcopy(CE_config))
    
    return CE_config_list

@pytest.mark.parametrize('pdsch_carrier_testvectors', get_pdsch_carrier_testvectors_list())
@pytest.mark.parametrize('channel_parameter', get_channel_parameter_list())
@pytest.mark.parametrize('CEQ_algo', get_channel_equ_config_list())
@pytest.mark.parametrize('CE_config', get_CE_config_list())
def test_nr_pdsch_channel_est_TDL_basic(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config):
    """ test PDSCH channel estimation 
     low correlation, [alpha,beta]==[0,0], no timing offset, maximum doppler freq = 0, ,no rho
    """
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

    ##if Nt==1 and Nr == 1 :
    #    return
    
    #if [Nt,Nr] ==[1,2]: #or CEQ_algo not in ["MMSE-ML-IRC"]:
    #    return
    
    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = test_nr_pdsch_rx_AWGN.pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    #printout
    CE_algo = CE_config["CE_algo"]
    freq_intp_method = CE_config["freq_intp_method"]
    TO_est = np.mean(nrChannelEstimation.TO_est)
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))

    if status:
        print(f"pass en TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method}, model_format{model_format},Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    else:
        print(f"failed en TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method},model_format{model_format}, Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")