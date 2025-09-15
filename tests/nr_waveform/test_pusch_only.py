# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 
import json

from tests.nr_pusch import nr_pusch_testvectors
from py5gphy.common import nr_slot
from py5gphy.nr_waveform import nr_ul_waveform

def get_pusch_testvectors():
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

@pytest.mark.parametrize('filename', get_pusch_testvectors())
def test_nr_pusch_only(filename):
    """ the main pupose this this test is to test PUSCH scrambling, modulation and resurce mapping
     
     """
    #read data
    matfile = io.loadmat(filename)
    effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out, \
              layermap_out, ref_fd_slot_data, waveform, pusch_tvcfg = \
        nr_pusch_testvectors.read_ulsch_testvec_matfile(matfile)
    
    carrier_config, pusch_config = nr_pusch_testvectors.gen_pusch_testvec_config(pusch_tvcfg)
    pusch_config["data_source"] = [1,0,0,1]
    NumCDMGroupsWithoutData = pusch_config['DMRS']["NumCDMGroupsWithoutData"]
    #following to 38.214 Table 6.2.2-1: The ratio of PUSCH EPRE to DM-RS EPRE, get PUSCH DMRS scaling factor
    #matlab toolbox didn;t select DMRS_scaling, need compensation 
    if NumCDMGroupsWithoutData == 1:
        DMRS_scaling = 1 #0db EPRE ratio
    else:
        DMRS_scaling = 10 ** (-3/20) #-3db EPRE ratio

    path = "py5gphy/nr_default_config/"
    with open(path + "default_UL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config['numofslots'] = int(2*carrier_config['scs']/15)
    waveform_config['samplerate_in_mhz'] = 122.88
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    pusch_config_list = []
    pusch_config_list.append(pusch_config)

    srs_config_list = []
    pucch_format0_config_list = []
    pucch_format1_config_list = []
    pucch_format2_config_list = []
    pucch_format3_config_list = []
    pucch_format4_config_list = []

    BW = carrier_config['BW']
    scs = carrier_config['scs']
    if scs == 30:
        numofslot = 4
    else:
        numofslot = 2
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    slot_size = carrier_prbsize*12*14
    num_of_ant = ref_fd_slot_data.shape[0]

    fd_waveform, td_waveform, ul_waveform = nr_ul_waveform.gen_ul_waveform(waveform_config, 
                    carrier_config, pusch_config_list, srs_config_list,
                    pucch_format0_config_list,pucch_format1_config_list,pucch_format2_config_list,
                    pucch_format3_config_list,pucch_format4_config_list)
    
    #matlab code didn;t process DMRS_scaling on DMRS data,here I would like only compare sym3(non-DMRS symbol) of each slot
    #test_nr_pusch.py would compensate DMRS_scaling on DMRS and then compare the whole slot data
    for m in range(num_of_ant):
        tmp1 = fd_waveform[m,:].reshape((numofslot,slot_size))
        sel_sym3 = tmp1[:,carrier_prbsize*12*3 : carrier_prbsize*12*4]

        tmp1 = ref_fd_slot_data[m,:].reshape((numofslot,slot_size))
        ref_sel_sym3 = tmp1[:,carrier_prbsize*12*3 : carrier_prbsize*12*4]
        assert np.allclose(sel_sym3, ref_sel_sym3, atol=1e-5)