# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from tests.nr_pdsch import nr_pdsch_testvectors
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.common import nr_slot
from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.nr_pdsch import nr_pdsch_dmrs

def get_testvectors():
    path = "tests/nr_pdsch/testvectors"
    if len(os.listdir(path)) < 10: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrPDSCH_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdsch_rx_LS_channel_est(filename):
    """ the main pupose this this test is to test PDSCH Rx channel estimation, including timning error est, freq error est,DFT and DCT est
     the teste vectors contain only PDSCH channel, no SSB/PDCCH/CSI-RS channel which may have PRB resource conflict with PDSCH
     """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.array([])
    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    numofslot = RM_out.shape[0]

    #add channel
    carrier_config["carrier_frequency_in_mhz"] = 3840
    Pnoise_dB = 255 # 255 means no noise
    scs = carrier_config["scs"]
    freq_error = 0 #Hz
    sample_rate_in_hz = 245760000
    timing_error = 0 #relative to sample_rate_in_hz


    for m in range(numofslot):
        slot = m
        
        num_of_ant = nrpdsch.carrier_config["num_of_ant"]
        
        carrier_prb_size = nrpdsch.carrier_prb_size
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)

        #pdsch processing
        fd_slot_data, RE_usage_inslot = nrpdsch.process(fd_slot_data,RE_usage_inslot, slot)
        
        H_LS,DMRS_info = nr_pdsch_dmrs.pdsch_dmrs_LS_est(fd_slot_data,pdsch_config,slot)

        #H_LS shall be identity matrix
        ref_H_LS = np.zeros(H_LS.shape,'c8')
        for ant_idx in range(H_LS.shape[3]):
            ref_H_LS[:,:,ant_idx,ant_idx] = 1
        assert np.allclose(H_LS, ref_H_LS, atol=1e-5)

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdsch_rx_no_channel_est(filename):
    """test pdsch rx processing without channel est
    this is to test PDSCH Rx processing correct or not, and also partially verify that CEQ algorithm 
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.array([])

    CEQ_config={}
    CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]
    #CEQ_algo_list = ["ML-hard","ML-IRC-hard","ML-soft","ML-IRC-soft"]
    #CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC"]
    #CEQ_algo_list = ["MMSE-ML","MMSE-ML-IRC"]
    #CEQ_algo_list = ["opt-rank2-ML","opt-rank2-ML-IRC"]
    CEQ_algo_idx = 0

    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    noise_var = 10**(-30/10)

    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    numofslot = RM_out.shape[0]

    m = 0 #slot index
    for CEQ_algo in CEQ_algo_list:
        CEQ_config["algo"] = CEQ_algo
        num_of_ant = nrpdsch.carrier_config["num_of_ant"]
        carrier_prb_size = nrpdsch.carrier_prb_size

        #generate identity H_result and identitycov_m
        RE_num = pdsch_config["ResAlloType1"]["RBSize"] * 12
        H_result = np.zeros((14,RE_num,num_of_ant,num_of_ant),'c8')
        cov_m = np.zeros((14,RE_num,num_of_ant,num_of_ant),'c8')
        
        for nr in range(num_of_ant):
            H_result[:,:,nr,nr] = 1
            cov_m[:,:,nr,nr] = noise_var

        slot = m
        sel_ref_fdslot_data = ref_fd_slot_data[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]

        status,tbblk, new_LLr_dns = \
            nrpdsch.RX_process(sel_ref_fdslot_data,slot,CEQ_config,H_result, cov_m,LDPC_decoder_config)                         
        
        if status:
            print(f"pass for slot {m}, {CEQ_algo}")
        else:
            print(f"failed for slot {m}, {CEQ_algo}")
        
        m = (m+1) % numofslot