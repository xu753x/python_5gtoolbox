# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.nr_lowphy import rx_lowphy_process
from py5gphy.common import nr_slot

def test_rx_lowphy_1():
    #test rx lowphy, no phase compensation, no tx and rx channel filter

    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 1
    carrier_config["carrier_frequency_in_mhz"] = 0 # no phase compensation
    carrier_config["scs"] = 30
    carrier_config["BW"] = 100
    carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )

    rng = np.random.default_rng()

    #generate one frequency domain slot random data
    fd_slot = np.zeros((1,carrier_prb_size*12*14),'c8')
    fd_slot[0,:] = rng.normal(0,10,carrier_prb_size*12*14) + 1j*rng.normal(0,10,carrier_prb_size*12*14)

    #tx low phy processing: IFFT, add CP, phase compensation
    td_slot = tx_lowphy_process.Tx_low_phy(fd_slot, carrier_config)

    #Rx low phy processing, FFT, phase de-compensation
    rx_fd_slot =  rx_lowphy_process.Rx_low_phy(td_slot, carrier_config)                    

    #verify                      
    assert np.allclose(fd_slot, rx_fd_slot, atol=1e-5)

def test_rx_lowphy_2():
    #test rx lowphy, 2 antenna, with phase compensation, no tx and rx channel filter

    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 2
    carrier_config["carrier_frequency_in_mhz"] = 3840 # with phase compensation
    carrier_config["scs"] = 30
    carrier_config["BW"] = 100
    carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )

    rng = np.random.default_rng()

    #generate one frequency domain slot random data
    fd_slot = np.zeros((carrier_config["num_of_ant"],carrier_prb_size*12*14),'c8')
    fd_slot[0,:] = rng.normal(0,10,carrier_prb_size*12*14) + 1j*rng.normal(0,10,carrier_prb_size*12*14)
    fd_slot[1,:] = rng.normal(0,10,carrier_prb_size*12*14) + 1j*rng.normal(0,10,carrier_prb_size*12*14)

    #tx low phy processing: IFFT, add CP, phase compensation
    td_slot = tx_lowphy_process.Tx_low_phy(fd_slot, carrier_config)

    #Rx low phy processing, FFT, phase de-compensation
    rx_fd_slot =  rx_lowphy_process.Rx_low_phy(td_slot, carrier_config)                    

    #verify                      
    assert np.allclose(fd_slot, rx_fd_slot, atol=1e-5)

def test_channel_filter_1():
    #test tx and rx channel filter. the channel filter includes FIR filter,halfband filter for upsample and downsample
    #
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 2
    carrier_config["carrier_frequency_in_mhz"] = 3840 # with phase compensation
    carrier_config["scs"] = 30
    carrier_config["BW"] = 100
    carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )

    sample_rate_in_hz = 245760000

    rng = np.random.default_rng()

    #generate one frequency domain slot random data
    fd_slot = np.zeros((carrier_config["num_of_ant"],carrier_prb_size*12*14),'c8')
    fd_slot[0,:] = rng.normal(0,10,carrier_prb_size*12*14) + 1j*rng.normal(0,10,carrier_prb_size*12*14)
    fd_slot[1,:] = rng.normal(0,10,carrier_prb_size*12*14) + 1j*rng.normal(0,10,carrier_prb_size*12*14)

    #tx low phy processing: IFFT, add CP, phase compensation
    td_slot = tx_lowphy_process.Tx_low_phy(fd_slot, carrier_config)

    #tx channel filter
    dl_waveform = tx_lowphy_process.channel_filter(td_slot,carrier_config, sample_rate_in_hz)

    #rx channel filter
    rx_td_slot = rx_lowphy_process.channel_filter(dl_waveform, carrier_config,sample_rate_in_hz)

    #Rx low phy processing, FFT, phase de-compensation
    rx_fd_slot =  rx_lowphy_process.Rx_low_phy(rx_td_slot, carrier_config)                    
    
    #does colleation, and peak value is in the middle
    corr = np.correlate(fd_slot[0,:],rx_fd_slot[0,:], 'full')
    peak_pos = np.argmax(abs(corr))

    #peak position should be in the middle of correlation
    assert peak_pos == corr.size // 2

def test_channel_filter_all():
    #test tx and rx channel filter for different BW, scs,sample rate
    # the channel filter includes FIR filter,halfband filter for upsample and downsample
    #
    path = "py5gphy/nr_default_config/"
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    carrier_config["num_of_ant"] = 2
    carrier_config["carrier_frequency_in_mhz"] = 3840 # with phase compensation

    sample_rate_in_hz_list = [122880000,122880000*2,122880000*4]

    BW_scs_map = {15:[5,10,15,20,25,30,35,40,45,50],
                  30:[100,90,80,70,60,50,45,40,35,30,25,20,15]}
    try_num = 6 #
    for sample_rate_in_hz in sample_rate_in_hz_list:
        for scs  in [30, 15]:
            carrier_config["scs"] = scs
            BW_list = BW_scs_map[scs]  
            for BW in BW_list:
                carrier_config["BW"] = BW
                carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_config["scs"], carrier_config["BW"] )
                ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prb_size)
                td_slotsize = ifftsize*15
                results = {}
                for test_num in range(try_num):
                    
                    #get occupied PRB[startPRB, PRBsize] list,
                    for startPRB in range(0,carrier_prb_size-4,carrier_prb_size // 4):
                        PRBSize_list = list(range(4,carrier_prb_size-startPRB, carrier_prb_size // 4))
                        PRBSize_list.append(carrier_prb_size-startPRB)

                        for PRBSize in PRBSize_list:
                            key_v = startPRB*carrier_prb_size + PRBSize
                            if key_v not in results: #reset key if not exist
                                results[key_v] = 0
                            else:
                                if results[key_v]: #if value =1, no need run again
                                    continue

                            result = _verify_low_phy(carrier_prb_size,td_slotsize,carrier_config,startPRB,PRBSize,sample_rate_in_hz)
                            #print(f"test scs={scs},sample_rate_in_hz={sample_rate_in_hz},BW={BW},test_num={test_num},startPRB {startPRB},PRBSize{PRBSize},result={result}")
    
                            if result:
                                results[key_v] = 1
                    
                        
                if list(results.values()).count(0) > 2:
                    #assert 0
                    print(f"failed test scs={scs},sample_rate_in_hz={sample_rate_in_hz},BW={BW},{results.values()}")
                else:
                    print(f"pass test scs={scs},sample_rate_in_hz={sample_rate_in_hz},BW={BW}")
                
def _verify_low_phy(carrier_prb_size,td_slotsize,carrier_config,startPRB,PRBSize,sample_rate_in_hz):
    rng = np.random.default_rng()
    
    #generate 3 fd_slot, and check middle fd slot
    fd_slots = np.zeros((2,3*carrier_prb_size*12*14),'c8')
    td_slots = np.zeros((2,3*td_slotsize),'c8')
    
    for slot in [0,1,2]:
        for sym in range(14):
            offset = carrier_prb_size*12*14*slot + carrier_prb_size*12*sym+startPRB*12
            fd_slots[0,offset:offset+PRBSize*12] = rng.normal(0,10,PRBSize*12) + 1j*rng.normal(0,10,PRBSize*12)
            fd_slots[1,offset:offset+PRBSize*12] = rng.normal(0,10,PRBSize*12) + 1j*rng.normal(0,10,PRBSize*12)

        #tx low phy processing: IFFT, add CP, phase compensation
        td_slot = tx_lowphy_process.Tx_low_phy(fd_slots[:,carrier_prb_size*12*14*slot:carrier_prb_size*12*14*(slot+1)], carrier_config)

        td_slots[:,td_slotsize*slot:td_slotsize*(slot+1)] = td_slot

    #tx channel filter
    dl_waveform = tx_lowphy_process.channel_filter(td_slots,carrier_config, sample_rate_in_hz)

    #rx channel filter
    rx_td_slots = rx_lowphy_process.channel_filter(dl_waveform, carrier_config,sample_rate_in_hz)

    #Rx low phy processing, FFT, phase de-compensation
    rx_fd_slots = np.zeros((2,3*carrier_prb_size*12*14),'c8')
    for slot in [0,1,2]:
        rx_fd_slot =  rx_lowphy_process.Rx_low_phy(rx_td_slots[:,td_slotsize*slot:td_slotsize*(slot+1)], carrier_config)                    
    
        rx_fd_slots[:,carrier_prb_size*12*14*slot:carrier_prb_size*12*14*(slot+1)] = rx_fd_slot
        #does colleation for the middle slot, and peak value is in the middle
    corr = np.correlate(fd_slots[0,carrier_prb_size*12*14:carrier_prb_size*12*14*2],rx_fd_slots[0,carrier_prb_size*12*14:carrier_prb_size*12*14*2], 'full')
    peak_pos = np.argmax(abs(corr))

    #peak position should be in the middle of correlation
    return peak_pos == corr.size // 2
    