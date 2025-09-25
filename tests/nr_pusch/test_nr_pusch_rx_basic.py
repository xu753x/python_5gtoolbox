# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 
import time

from tests.nr_pusch import nr_pusch_testvectors
from py5gphy.nr_pusch import nr_pusch_dmrs
from py5gphy.nr_pusch import nr_pusch
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_pusch/testvectors_pusch"
    if len(os.listdir(path)) < 100: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrPUSCH_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pusch_rx_no_channel_est(filename):
    """ the main pupose of this test is to test PUSCH Rx processing function,
    no channel estimation in the test
          
     """
    #read data
    matfile = io.loadmat(filename)
    effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out, \
              layermap_out, fd_slot_data_ref, waveform, pusch_tvcfg = \
        nr_pusch_testvectors.read_ulsch_testvec_matfile(matfile)
    
    carrier_config, pusch_config = nr_pusch_testvectors.gen_pusch_testvec_config(pusch_tvcfg)
    pusch_config["data_source"] = [1,0,0,1]
    pusch_config["rv"] = [0]
    NumCDMGroupsWithoutData = pusch_config['DMRS']["NumCDMGroupsWithoutData"]
    #following to 38.214 Table 6.2.2-1: The ratio of PUSCH EPRE to DM-RS EPRE, get PUSCH DMRS scaling factor
    #matlab toolbox didn;t select DMRS_scaling, need compensation 
    if NumCDMGroupsWithoutData == 1:
        DMRS_scaling = 1 #0db EPRE ratio
    else:
        DMRS_scaling = 10 ** (-3/20) #-3db EPRE ratio

    BW = carrier_config['BW']
    scs = carrier_config['scs']
    if scs == 30:
        numofslot = 4
    else:
        numofslot = 2
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    slot_size = carrier_prbsize*12*14
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']

    CEQ_config={}
    #CEQ_algo_list = ["ZF", "ZF-IRC", "MMSE", "MMSE-IRC","ML-soft","ML-IRC-soft","ML-hard","ML-IRC-hard","MMSE-ML","MMSE-ML-IRC","opt-rank2-ML","opt-rank2-ML-IRC"]
    CEQ_algo_list = ["ZF"]
    CEQ_algo_idx = 0

    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    noise_var = 10**(-30/10)

    nTransPrecode = pusch_config['nTransPrecode']
    EnableULSCH = pusch_config['EnableULSCH']
    if EnableULSCH == 0:
        print("EnableULSCH==0")
        return
    
    if nTransPrecode:
        print("nTransPrecode = 1")
        pass
    else:
        pass
        #return

    nrpusch = nr_pusch.NrPUSCH(carrier_config,pusch_config)
    
    #only test first slot
    slot = 0 #slot index
    for CEQ_algo in CEQ_algo_list:
        CEQ_config["algo"] = CEQ_algo
        
        num_of_ant = nrpusch.carrier_config["num_of_ant"]
        carrier_prb_size = nrpusch.carrier_prb_size

        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(nNrOfAntennaPorts, carrier_prbsize)

        #pusch processing
        fd_slot_data, RE_usage_inslot = nrpusch.process(fd_slot_data,RE_usage_inslot,slot)
                
        H_LS,RS_info = nr_pusch_dmrs.pusch_dmrs_LS_est(fd_slot_data,pusch_config,slot)                            
        
        H_result = np.zeros((14,H_LS.shape[1]*4,H_LS.shape[2],H_LS.shape[3]),'c8')
        for sym in range(14):
            H_result[sym,0::4,:,:] = H_LS[0,:,:]
            H_result[sym,1::4,:,:] = H_LS[0,:,:]
            H_result[sym,2::4,:,:] = H_LS[0,:,:]
            H_result[sym,3::4,:,:] = H_LS[0,:,:]

        cov_m = np.zeros((H_result.shape[0],H_result.shape[1],H_result.shape[2],H_result.shape[2]),'c8')
        for nr in range(cov_m.shape[2]):
            cov_m[:,:,nr,nr] = noise_var
        
        nTransPrecode = pusch_config['nTransPrecode']
        EnableULSCH = pusch_config['EnableULSCH']

        start_time = time.time()

        ulsch_status,tbblk, ulsch_new_LLr_dns = nrpusch.RX_process(fd_slot_data,slot,CEQ_config,H_result, cov_m,LDPC_decoder_config)

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if ulsch_status:
            print(f"pass for slot {slot}, {CEQ_algo},Elapsed Time: {elapsed_time:.2f} seconds")
        else:
            print(f"failed for slot {slot}, {CEQ_algo},Elapsed Time: {elapsed_time:.2f} seconds")
        
        slot = (slot+1) % numofslot