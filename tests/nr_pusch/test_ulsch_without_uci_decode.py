# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 

from tests.nr_pusch import nr_pusch_testvectors
from py5gphy.nr_pusch import nr_pusch_dmrs
from py5gphy.nr_pusch import nr_pusch
from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch_precoding
from py5gphy.nr_pusch import nrpusch_resource_mapping
from py5gphy.nr_pusch import nr_ulsch
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch_uci_decode

def get_testvectors():
    
    path = "tests/nr_pusch/testvectors_ulsch_without_uci"
    if len(os.listdir(path)) < 1000: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)
    
    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrULSCH_without_uci_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_ulsch_without_uci_decode(filename):
    """
    """
    #read data
    matfile = io.loadmat(filename)
    effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out_ref, \
              layermap_out, fd_slot_data_ref, waveform, pusch_tvcfg = \
        nr_pusch_testvectors.read_ulsch_testvec_matfile(matfile)
    
    carrier_config, pusch_config = nr_pusch_testvectors.gen_pusch_testvec_config(pusch_tvcfg)
    pusch_config["data_source"] = [1,0,0,1]
    
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    rvlist = pusch_config['rv']
        
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    
    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    HARQ_on = True

    snr_db = 30
    ulsch_new_LLr_dns = np.array([])
    slot_num = codeword_out_ref.shape[0]                
    for slot in range(slot_num):
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(nNrOfAntennaPorts, carrier_prbsize)

        fd_slot_data, RE_usage_inslot, DMRSinfo = nr_pusch_dmrs.process(fd_slot_data,RE_usage_inslot, pusch_config, slot)
        DMRS_symlist = DMRSinfo['DMRS_symlist'] 

        tmp1 = 1 - 2*codeword_out_ref[slot,:].astype('f')
        fn = tmp1 + np.random.normal(0, 10**(-snr_db/20), tmp1.size) #add noise
        #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
        noise_power = 10**(-snr_db/10)
        LLr = 2*fn/noise_power
        
        ulsch_status, tbblk,ulsch_new_LLr_dns = nr_pusch_uci_decode.ULSCHandUCIDecodeProcess(LLr,pusch_config, rvlist[slot], LDPC_decoder_config,HARQ_on,ulsch_new_LLr_dns)

        if ulsch_status:
            print("pass")
        else:
            print("failed")