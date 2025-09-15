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
from tests.nr_pdsch import test_nr_pdsch_rx_AWGN

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
        ["AWGN",     0,        0,    0,      1500,       0,       [0,0]], #medium
        ["AWGN",     200,        0,    0,      200,       0,       [0,0]], #low correlation
        ["AWGN",     0,        0,    0,      1500,       0,       [0.3,0.3]], #medium
        ["AWGN",     0,        1e-7,    0,      0,       0,       [0.3,0.9]], #medium
        ["AWGN",     0,        0,    0,      0,       0,       [0.9,0.9]], #high
        ]
    Pnoise_dB_list = [-20] #
    
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
def test_nr_pdsch_channel_est_AWGN_no_TO_FO(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config):
    """ test PDSCH channel estimation 
     AWGN channel
    """                
    #read input and generate configurations
    [waveform_config,carrier_config,pdsch_config] = pdsch_carrier_testvectors

    model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
    ref_Pnoise_dB = channel_parameter[1]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    mcs_index = pdsch_config['mcs_index']
    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    
    #default LDPC decoder
    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    #[alpha,beta]=[0.8,0.3] is the best pair I searched in the simulation
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    #default CE config
    CE_config["enable_FO_est"] = False
    CE_config["enable_FO_comp"] = False
    CE_config["enable_carrier_FO_est"] = False
    CE_config["enable_carrier_FO_TO_comp"] = False
    
    
    CEQ_config = {}
    CEQ_config["algo"] = CEQ_algo

    #select conditions that bypass the test
    ##if Timeoff_ns !=0 or rho !=0 or fDo_in_Hz != 0:
    #    return

    if fDo_in_Hz != 0:
        return
    
    if Nt==1 and Nr == 1 and alpha > 0:
        return
    
    if mcs_index != 1:
        return

    #if [Nt,Nr] !=[2,4]:
    #   return
    
    #if CEQ_algo in ["ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard"]:
    #    return

    if CEQ_algo in ["opt-rank2-ML","opt-rank2-ML-IRC"] and Nt != 2:
        return
    
    ###############first test no TO compemsation############
    CE_config["enable_TO_comp"] = False
    CE_algo = CE_config["CE_algo"]
    freq_intp_method = CE_config["freq_intp_method"]

    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = test_nr_pdsch_rx_AWGN.pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    TO_est = np.mean(nrChannelEstimation.TO_est)
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))

    if status:
        print(f"pass no TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method}, Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    else:
        print(f"failed no TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method}, Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")

    ############### second test en TO compemsation ############
    CE_config["enable_TO_comp"] = True
    CE_algo = CE_config["CE_algo"]
    freq_intp_method = CE_config["freq_intp_method"]

    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = test_nr_pdsch_rx_AWGN.pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    TO_est = np.mean(nrChannelEstimation.TO_est)
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))

    if status:
        print(f"pass en TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method}, Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    else:
        print(f"failed en TO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method}, Timeoff_ns{Timeoff_ns},fDo_in_Hz{fDo_in_Hz},alpha{alpha},beta{beta},Elapsed Time: {elapsed_time:.2f} seconds,TO_est{TO_est*10**9:.2f}ns,H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    print("---")        

@pytest.mark.parametrize('pdsch_carrier_testvectors', get_pdsch_carrier_testvectors_list())
@pytest.mark.parametrize('channel_parameter', get_channel_parameter_list())
@pytest.mark.parametrize('CEQ_algo', get_channel_equ_config_list())
@pytest.mark.parametrize('CE_config', get_CE_config_list())
def test_nr_pdsch_channel_est_AWGN_FO(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config):
    """ test PDSCH channel estimation 
     AWGN channel
    """                
    #read input and generate configurations
    [waveform_config,carrier_config,pdsch_config] = pdsch_carrier_testvectors

    model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
    ref_Pnoise_dB = channel_parameter[1]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    mcs_index = pdsch_config['mcs_index']
    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    
    #default LDPC decoder
    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    #[alpha,beta]=[0.8,0.3] is the best pair I searched in the simulation
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    #default CE config
    CE_config["enable_TO_comp"] = True
    
    CE_config["enable_carrier_FO_est"] = False
    CE_config["enable_carrier_FO_TO_comp"] = False
    
    
    CEQ_config = {}
    CEQ_config["algo"] = CEQ_algo
        
    #select conditions that bypass the test
    ##if Timeoff_ns !=0 or rho !=0 or fDo_in_Hz != 0:
    #    return

    if fDo_in_Hz == 0 or rho != 0:
        return
    
    if Nt==1 and Nr == 1 and alpha > 0:
        return
    
    if mcs_index != 11:
        return

    #if [Nt,Nr] !=[2,4]:
    #   return
    
    #if CEQ_algo in ["ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard"]:
    #    return

    if CEQ_algo in ["opt-rank2-ML","opt-rank2-ML-IRC"] and Nt != 2:
        return
    
    ###############first test no FO est and compemsation############
    CE_config["enable_FO_est"] = True
    CE_config["enable_FO_comp"] = False

    CE_algo = CE_config["CE_algo"]
    freq_intp_method = CE_config["freq_intp_method"]

    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = test_nr_pdsch_rx_AWGN.pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    FO_est = nrChannelEstimation.FO_est
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))

    if status:
        print(f"pass no FO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,fDo_in_Hz{fDo_in_Hz}, FO_est{FO_est:.2f},H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    else:
        print(f"failed no FO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,fDo_in_Hz{fDo_in_Hz}, FO_est{FO_est:.2f},H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")

    ############### second test en TO compemsation ############
    CE_config["enable_FO_comp"] = True

    CE_algo = CE_config["CE_algo"]
    freq_intp_method = CE_config["freq_intp_method"]

    start_time = time.time()
        
    status,tbblk, new_LLr_dns,nrChannelEstimation = test_nr_pdsch_rx_AWGN.pdsch_tx_and_lowphy_rx_processing(pdsch_carrier_testvectors,channel_parameter,CE_config,CEQ_config,LDPC_decoder_config)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #printout
    FO_est = nrChannelEstimation.FO_est
    H_est_power = 20*np.log10(np.abs(nrChannelEstimation.H_result[2,10,:,:].reshape(Nt*Nr)))
    cov_m_power = 10*np.log10(np.abs(nrChannelEstimation.cov_m[0,0,:,:].reshape(Nr*Nr)))

    if status:
        print(f"pass en FO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,fDo_in_Hz{fDo_in_Hz}, FO_est{FO_est:.2f},H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    else:
        print(f"failed en FO comp,mcsidx{mcs_index},Nt{Nt},Nr{Nr}, {CE_algo}, {freq_intp_method},alpha{alpha},beta{beta},ref_Pnoise_dB={ref_Pnoise_dB},Elapsed Time: {elapsed_time:.2f} seconds,fDo_in_Hz{fDo_in_Hz}, FO_est{FO_est:.2f},H_est_power={H_est_power}dB, cov_m_power={cov_m_power}dB")
    print("---")        

@pytest.mark.parametrize('pdsch_carrier_testvectors', get_pdsch_carrier_testvectors_list())
@pytest.mark.parametrize('channel_parameter', get_channel_parameter_list())
@pytest.mark.parametrize('CEQ_algo', get_channel_equ_config_list())
@pytest.mark.parametrize('CE_config', get_CE_config_list())
def test_nr_pdsch_channel_est_AWGN_rho(pdsch_carrier_testvectors, channel_parameter,CEQ_algo,CE_config):
    """ test rho"""
    """ below is the output
    rho = 1e-07, rho_est=2.7932929276946297e-07,numofslots = 10
    rho = 1e-07, rho_est=-2.2105265132762945e-08,numofslots = 20
    rho = 1e-07, rho_est=1.0433530203341799e-07,numofslots = 40
    rho = 1e-07, rho_est=9.734279193723019e-08,numofslots = 80
    rho = 1e-07, rho_est=6.602879989435442e-08,numofslots = 10
    rho = 1e-07, rho_est=1.2302398795685433e-07,numofslots = 20
    rho = 1e-07, rho_est=1.350579115750119e-07,numofslots = 40
    rho = 1e-07, rho_est=9.766697946675567e-08,numofslots = 80
    rho = 1e-07, rho_est=-5.442948746120623e-08,numofslots = 10
    rho = 1e-07, rho_est=-7.939416143315522e-08,numofslots = 20
    rho = 1e-07, rho_est=1.341457178703129e-07,numofslots = 40
    rho = 1e-07, rho_est=1.0700987175581948e-07,numofslots = 80
    """
    
    #read input and generate configurations
    [waveform_config,carrier_config,pdsch_config] = pdsch_carrier_testvectors

    model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
    ref_Pnoise_dB = channel_parameter[1]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    mcs_index = pdsch_config['mcs_index']
    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    
    #default LDPC decoder
    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    #[alpha,beta]=[0.8,0.3] is the best pair I searched in the simulation
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    #default CE config
    CE_config["enable_TO_comp"] = False
    CE_config["enable_FO_est"] = False
    CE_config["enable_FO_comp"] = False
    CE_config["enable_carrier_FO_est"] = False
    CE_config["enable_carrier_FO_TO_comp"] = False
    
    
    CEQ_config = {}
    CEQ_config["algo"] = CEQ_algo
        
    #for AWGN channel
    multi_paths = []
    Rspat_in = np.empty(0)

    #select conditions that bypass the test
    if rho == 0:
        return
    
    if Nt==1 and Nr == 1 and alpha > 0:
        return
    
    if mcs_index != 1:
        return
    
    scs = carrier_config["scs"]   
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    
    startSFN = waveform_config["startSFN"]
    startslot = waveform_config["startslot"]
    
    #get DMRS sym number and time offset of each RS symbol to the beginning of the slot
    #below code is for Ld = 14 and DMFS config type 1 only
    num_rs_sym = pdsch_config['DMRS']['DMRSAddPos'] + 1
    if pdsch_config['DMRS']['DMRSAddPos'] ==0:
        DMRS_symlist = [2]
    elif pdsch_config['DMRS']['DMRSAddPos']  == 1:
        DMRS_symlist = [2, 11]
    elif pdsch_config['DMRS']['DMRSAddPos']  == 2:
        DMRS_symlist = [2, 7, 11]
    elif pdsch_config['DMRS']['DMRSAddPos']  == 3:
        DMRS_symlist = [2, 5, 8, 11]
    symbols_timing_offset_list, _ = nr_slot.get_symbol_timing_offset(scs)
    RS_sym_timing_offset = symbols_timing_offset_list[DMRS_symlist]

    #common processing, go through Tx low phy, Tx channel filter, wireless channel model, Rx channel filter, Rx low phy
    for numofslots in [10,20,40,80]:
        waveform_config["numofslots"] = numofslots #rho estimation need multiple slot data to make the estimation accurate

        rx_fd_waveform, nrPdsch, waveform_config,carrier_config,pdsch_config,channel_parameter,ref_Pnoise_dB = \
        _pdsch_low_phy_tx_rxprocessing(waveform_config,carrier_config,pdsch_config,channel_parameter,multi_paths,Rspat_in)
           
        TO_values = np.zeros(waveform_config["numofslots"]*num_rs_sym) # 2 RS symbol
        timing_durations= np.zeros(waveform_config["numofslots"]*num_rs_sym) # 2 RS symbol
        for idx in range(waveform_config["numofslots"]):
            #get sfn and slot
            sfn = startSFN + int((startslot+idx)//(scs/15*10))
            slot = (startslot+idx) % int(scs/15*10)

            rx_fd_slot = rx_fd_waveform[:,idx*carrier_prb_size*12*14:(idx+1)*carrier_prb_size*12*14]

            #PDSCH channel LS estimation
            H_LS,RS_info = nrPdsch.H_LS_est(rx_fd_slot,slot)
        
            #channel est
            #channel est class
            nrChannelEstimation = \
                nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
    
            #timing offset estimate and compensation
            TO_est = nrChannelEstimation.timing_offset_est()
        
            TO_values[idx*2:idx*2+2] = TO_est
            if scs == 30:
                timing_durations[idx*2:idx*2+2] = 0.0005*idx + RS_sym_timing_offset
            else:
                timing_durations[idx*2:idx*2+2] = 0.001*idx + RS_sym_timing_offset
    
        rho_est = nr_channel_estimation.cal_carrier_relative_freq_offset(TO_values,timing_durations)
        print(f"rho = {rho}, rho_est={rho_est},numofslots = {numofslots}")
    #assert abs((rho_est-rho)/rho) < 0.2
    
def _pdsch_low_phy_tx_rxprocessing(waveform_config,carrier_config,pdsch_config,channel_parameter,multi_paths,Rspat_in):
    #read parameters
    model_format, Timeoff_ns, rho, fm_inHz, fDo_in_Hz,DSdesired,[alpha,beta] = channel_parameter[0]
    ref_Pnoise_dB = channel_parameter[1]
    
    
    scs = carrier_config["scs"]
    carrier_freq = carrier_config["carrier_frequency_in_mhz"] * 1e6
    fs_inHz = waveform_config["samplerate_in_mhz"] * 1e6
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)

    Nt, Nr =[carrier_config["num_of_ant"],carrier_config["Nr"]]
    Rspat_config=["customized","uniform","DL",[alpha,beta]]

    #generate PDSCH class
    nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    nrPdsch_list=[]
    nrPdsch_list.append(nrPdsch)
    
    #channel model
    channel_model_config = nr_channel_model.gen_channel_model_config(model_format,Rspat_config,Nt, Nr,Timeoff_ns,rho,fm_inHz,multi_paths,fDo_in_Hz,Rspat_in,DSdesired)

    nrChannelModel = AWGN_channel_model.AWGNChannelModel(channel_model_config,ref_Pnoise_dB,carrier_freq,fs_inHz,scs,fDo_in_Hz)

    Dm = nrChannelModel.gen_Dm(waveform_config["numofslots"])

    #gen DL waveform
    _, _, dl_waveform,td_waveform_sample_rate_in_hz = \
        nr_dl_waveform.gen_dl_waveform(waveform_config,carrier_config,
                                       nrPdsch_list=nrPdsch_list,Dm=Dm)

    #go through channel model
    rx_waveform = nrChannelModel.filter(dl_waveform)

    #Rx channel filter and low phy processing
    _,rx_fd_waveform = rx_lowphy_process.waveform_rx_processing(rx_waveform, carrier_config,fs_inHz)

    return rx_fd_waveform, nrPdsch, waveform_config,carrier_config,pdsch_config,channel_parameter,ref_Pnoise_dB

    