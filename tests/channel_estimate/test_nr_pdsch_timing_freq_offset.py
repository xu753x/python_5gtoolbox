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
from py5gphy.channel_estimate import nr_channel_estimation
from tests.channel_estimate import test_nr_pdsch_channel_estimation_AWGN

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
def test_nr_pdsch_timing_offset_est_and_comp_with_channel_filter(filename):
    """ test PDSCH timing offset est and compensation for each DMRS symbol
    channel filter is enabled in the test
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.empty(0)
    nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    numofslot = RM_out.shape[0]

    #add channel
    carrier_config["carrier_frequency_in_mhz"] = 3840
    Pnoise_dB = 255 # 255 means no noise
    scs = carrier_config["scs"]
    freq_offset = 0 #Hz
    
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    fft_ifft_sample_rate_in_hz = fftsize * scs*1000

    sample_rate_in_hz = fft_ifft_sample_rate_in_hz * 4
    init_timing_offset_in_sample = -2 #relative to sample_rate_in_hz

    #gen CE_config
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True}

    for slot in range(numofslot):
        timing_offset_in_sample = init_timing_offset_in_sample + slot*2
        expected_TO = -timing_offset_in_sample /sample_rate_in_hz 

        H_LS, RS_info = _nr_pdsch_process_for_H_LS(
            slot, nrPdsch,carrier_config, fft_ifft_sample_rate_in_hz,
            sample_rate_in_hz,
            Pnoise_dB, 
            freq_offset,
            timing_offset_in_sample, 
            True)

        RS_info["carrier_frequency_in_mhz"] = carrier_config["carrier_frequency_in_mhz"]

        #channel est clase
        nrChannelEstimation = \
            nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
        
        TO_est = nrChannelEstimation.timing_offset_est()

        if timing_offset_in_sample == 0:
           print(f"timing_offset_in_sample = {timing_offset_in_sample } ,np.mean(TO_est)*sample_rate_in_hz={np.mean(TO_est)*sample_rate_in_hz}")
           assert np.allclose(np.mean(TO_est)*sample_rate_in_hz, 0, atol=1e-2)
        else:
            print(f"timing_offset_in_sample = {timing_offset_in_sample } ,(1-np.mean(TO_est)/expected_TO)={(1-np.mean(TO_est)/expected_TO)}")
            assert ((1-np.mean(TO_est)/expected_TO) < 0.01).all() and ((1-np.mean(TO_est)/expected_TO).all()> -0.01).all()
        
        nrChannelEstimation.comp_H_LS_timing_offset()

        #get [rx,tx]=[0,0] and [1,1] ant pair and check H_LS value
        new_H_LS = nrChannelEstimation.H_LS
        sym_num, RE_num,Nr,Nt = new_H_LS.shape

        for m in range(sym_num):
            #after TO compensation, all H_LS value in one symbol shall be close to each other
            sel_HS00 = new_H_LS[m,:,0,0]
            assert (np.abs(1 - sel_HS00/sel_HS00[0]) < 1e-1).all()
            print(f"ant0 pass TO compsation test,max H_LS error = {np.abs(1 - sel_HS00/sel_HS00[0]).max()}")
            if Nr > 1 and Nt > 1:
                sel_HS11 = new_H_LS[m,:,1,1]
                assert (np.abs(1 - sel_HS11/sel_HS11[0]) < 1e-1).all()
                print(f"ant1 pass TO compsation test,max H_LS error = {np.abs(1 - sel_HS11/sel_HS11[0]).max()}")

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdsch_freq_offset_est_no_channel_filter(filename):
    """ test PDSCH freq offset est for each DMRS symbol
    no channel filter in the test
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.empty(0)
    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    #numofslot = RM_out.shape[0]

    numofslot = 20 #total simulated slots

    #add channel
    carrier_config["carrier_frequency_in_mhz"] = 3840
    Pnoise_dB = 255 # 255 means no noise
    scs = carrier_config["scs"]
    init_freq_offset = -400 #Hz

    sample_rate_in_hz = 245760000
    
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    fft_ifft_sample_rate_in_hz = fftsize * scs*1000

    #gen CE_config
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True}

    for test_idx in range(8):
        freq_offset = init_freq_offset + test_idx*200

        FO_est_save = np.zeros(numofslot)
        rho_save = np.zeros(numofslot)
        for m in range(numofslot):
            slot = m % (scs//15*10)
            timing_offset_in_sample = 0
            
            H_LS, RS_info = _nr_pdsch_process_for_H_LS(
                slot, nrpdsch,carrier_config, fft_ifft_sample_rate_in_hz,
                sample_rate_in_hz,
                Pnoise_dB, 
                freq_offset,
                timing_offset_in_sample, 
                False)

            RS_info["carrier_frequency_in_mhz"] = carrier_config["carrier_frequency_in_mhz"]

            #channel est class
            nrChannelEstimation = \
                nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)

            _ = nrChannelEstimation.timing_offset_est()

            status, est_FO_est = nrChannelEstimation.freq_offset_est()
            FO_est_save[m] = est_FO_est

            status_rho, rho = nrChannelEstimation.cal_carrier_relative_freq_offset()
            rho_save[m] = rho

        avg_FO_est = np.mean(FO_est_save)       
        avg_rho = np.mean(rho_save) 
        if status:
            if freq_offset == 0:
                print(f"freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f}, avg_rho={avg_rho*10**6:4f}ppm")
                assert abs(avg_FO_est) <0.1
            else:
                #check phase rotate
                if np.sign(avg_FO_est) != np.sign(freq_offset):
                    #phase larger than pi and phase rotate happen
                    print(f"skip compasiron for phase rotata,freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f}")
                else:
                    print(f"freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f},abs(1-avg_FO_est/freq_offset)={abs(1-avg_FO_est/freq_offset):6f}, avg_rho={avg_rho*10**6:4f}ppm")
                    assert abs(1-avg_FO_est/freq_offset) <0.01
        else:
            print("no freq estimation for one DMRS symbol allocation")       

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdsch_freq_offset_est_with_channel_filter(filename):
    """ test PDSCH freq error est for each DMRS symbol
    with channel filter in the test
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.empty(0)
    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    #numofslot = RM_out.shape[0]
    numofslot = 20 #total simulated slots

    #add channel
    carrier_config["carrier_frequency_in_mhz"] = 3840
    Pnoise_dB = 255 # 255 means no noise
    scs = carrier_config["scs"]
    init_freq_offset = -400 #Hz

    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    fft_ifft_sample_rate_in_hz = fftsize * scs*1000

    sample_rate_in_hz = fft_ifft_sample_rate_in_hz * 4
        
    #gen CE_config
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True}

    for test_idx in range(8):
        freq_offset = init_freq_offset + test_idx*200

        FO_est_save = np.zeros(numofslot)
        rho_save = np.zeros(numofslot)
        for m in range(numofslot):
            slot = m % (scs//15*10)
            timing_offset_in_sample = 0
            
            H_LS, RS_info = _nr_pdsch_process_for_H_LS(
                slot, nrpdsch,carrier_config, fft_ifft_sample_rate_in_hz,
                sample_rate_in_hz,
                Pnoise_dB, 
                freq_offset,
                timing_offset_in_sample, 
                True)

            RS_info["carrier_frequency_in_mhz"] = carrier_config["carrier_frequency_in_mhz"]

            #channel est class
            nrChannelEstimation = \
                nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)

            _ = nrChannelEstimation.timing_offset_est()

            status, est_FO_est = nrChannelEstimation.freq_offset_est()
            FO_est_save[m] = est_FO_est

            status_rho, rho = nrChannelEstimation.cal_carrier_relative_freq_offset()
            rho_save[m] = rho

        avg_FO_est = np.mean(FO_est_save)        
        avg_rho = np.mean(rho_save) 
        if status:
            if freq_offset == 0:
                print(f"freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f}, avg_rho={avg_rho*10**6:4f}ppm")
                assert abs(avg_FO_est) <0.1
            else:
                #check phase rotate
                if np.sign(avg_FO_est) != np.sign(freq_offset):
                    #phase larger than pi and phase rotate happen
                    print(f"skip compasiron for phase rotata,freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f}")
                else:
                    print(f"freq_offset = {freq_offset}, avg_FO_est={avg_FO_est:4f},abs(1-avg_FO_est/freq_offset)={abs(1-avg_FO_est/freq_offset):6f}, avg_rho={avg_rho*10**6:4f}ppm")
                    assert abs(1-avg_FO_est/freq_offset) <0.01
        else:
            print("no freq estimation for one DMRS symbol allocation")       
                

def _nr_pdsch_process_for_H_LS(slot, nrpdsch,carrier_config, fft_ifft_sample_rate_in_hz,
                               sample_rate_in_hz,Pnoise_dB, freq_offset,timing_offset_in_sample, 
                               en_channel_filter):
    """handle PDSCH TX and Rx processing, 
    """ 
     
    num_of_ant = nrpdsch.carrier_config["num_of_ant"]
    
    carrier_prb_size = nrpdsch.carrier_prb_size
    fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)

    #pdsch processing
    fd_slot_data, RE_usage_inslot = nrpdsch.process(fd_slot_data,RE_usage_inslot, slot)

    #low phy
    td_slot = tx_lowphy_process.Tx_low_phy(fd_slot_data,carrier_config)         

    #channel filter
    if en_channel_filter:
        dl_waveform = tx_lowphy_process.channel_filter(td_slot, carrier_config,sample_rate_in_hz)   
    else:
        dl_waveform = td_slot

    new_dl_waveform = np.zeros((dl_waveform.shape),'c8')
    #add timing error
    if timing_offset_in_sample >=0:
        new_dl_waveform[:,timing_offset_in_sample:dl_waveform.shape[1]] = dl_waveform[:,0:dl_waveform.shape[1]-timing_offset_in_sample]
    else:
        new_dl_waveform[:,0: dl_waveform.shape[1]+timing_offset_in_sample] = dl_waveform[:,-timing_offset_in_sample:dl_waveform.shape[1]]
    
    #add freq error
    rng = np.random.default_rng()
    phase0 =  rng.uniform(-np.pi, np.pi, 1)
    #phase0 = 0
    #LOS is time domain phase shift per sample caused by freq error
    if en_channel_filter:
        LOS = np.exp(1j*(2*np.pi*freq_offset / sample_rate_in_hz*np.arange(new_dl_waveform.shape[1]) + phase0))
    else:
        LOS = np.exp(1j*(2*np.pi*freq_offset / fft_ifft_sample_rate_in_hz*np.arange(new_dl_waveform.shape[1]) + phase0))

    new_dl_waveform *= LOS #each sample multiple with phase offset

    #add noise
    if Pnoise_dB != 255:
        new_dl_waveform += np.random.normal(0, 10**(Pnoise_dB/20)/np.sqrt(2), new_dl_waveform.shape) + \
          1j * np.random.normal(0, 10**(Pnoise_dB/20)/np.sqrt(2), new_dl_waveform.shape)
    
    #rx channel filter
    if en_channel_filter:
        rx_td_waveform = rx_lowphy_process.channel_filter(new_dl_waveform, carrier_config,sample_rate_in_hz)
    else:
        rx_td_waveform = new_dl_waveform

    #rx low phy        
    rx_fd_slot =  rx_lowphy_process.Rx_low_phy(rx_td_waveform, carrier_config)     
    
    H_LS,RS_info = nrpdsch.H_LS_est(rx_fd_slot,slot)

    return H_LS, RS_info

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pdsch_freq_offset_comp_no_channel_filter(filename):
    """ test PDSCH timing offset compensation for each DMRS symbol
    no channel filter in the test
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.empty(0)
    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    numofslot = RM_out.shape[0]

    #add channel
    carrier_config["carrier_frequency_in_mhz"] = 3840
    Pnoise_dB = 255 # 255 means no noise
    scs = carrier_config["scs"]
    init_freq_offset = -200 #Hz

    sample_rate_in_hz = 245760000
    timing_offset_in_sample = 0 #relative to sample_rate_in_hz

    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, carrier_config["BW"])
    fftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
    fft_ifft_sample_rate_in_hz = fftsize * scs*1000

    #gen CE_config
    CE_config = {
        "enable_TO_comp": True, "enable_FO_est": True,
        "enable_FO_comp": True, "enable_carrier_FO_est": False,
        "enable_carrier_FO_TO_comp": False,
        "CE_algo": "DFT", "enable_rank_PMI_CQI_est": True}

    for slot in range(numofslot):
        freq_offset = init_freq_offset + slot*200

        H_LS, RS_info = _nr_pdsch_process_for_H_LS(
            slot, nrpdsch,carrier_config, fft_ifft_sample_rate_in_hz,
            sample_rate_in_hz,
            Pnoise_dB, 
            freq_offset,
            timing_offset_in_sample, 
            False)

        RS_info["carrier_frequency_in_mhz"] = carrier_config["carrier_frequency_in_mhz"]

        #channel est class
        nrChannelEstimation = \
            nr_channel_estimation.NrChannelEstimation(H_LS,RS_info, CE_config)
        
        status, est_FO_est = nrChannelEstimation.freq_offset_est()

        if status == True:                    
            nrChannelEstimation.comp_H_LS_freq_offset()

            #get [rx,tx]=[0,0] and [1,1] ant pair and check H_LS valur
            new_H_LS = nrChannelEstimation.H_LS
            sym_num, RE_num,Nr,Nt = new_H_LS.shape

            #after freq compensation, all H_LS symbol data shall close to each other
            for m in range(sym_num-1):
                diff00 = new_H_LS[m+1,:,0,0]/new_H_LS[m,:,0,0] #diff shall be close to 1+0j
                assert np.allclose(diff00, 1, atol=1e-1)
                if Nr > 1 and Nt > 1:
                    diff11 = new_H_LS[m+1,:,1,1]/new_H_LS[m,:,1,1] #diff shall be close to 1+0j
                    assert np.allclose(diff11, 1, atol=1e-1)
    
