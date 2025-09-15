# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_ssb import nr_ssb
from tests.nr_ssb import nr_ssb_testvectors
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_ssb/testvectors"
    if len(os.listdir(path)) < 20: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrSSB_waveform_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_ssb_waveform(filename):
    matfile = io.loadmat(filename)
    
    waveform_ref, fd_slot_data_ref, ssb_tvcfg = nr_ssb_testvectors.read_ssb_testvec_matfile(matfile)

    carrier_config,ssb_config = nr_ssb_testvectors.gen_ssb_testvec_config(ssb_tvcfg)
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    waveform_config["numofslots"] = int(10*carrier_config['scs']/15)
    waveform_config["startSFN"] = 0
    waveform_config["startslot"] = 0
    
    nrssb = nr_ssb.NrSSB(carrier_config, ssb_config)
    carrier_prb_size = nrssb.carrier_prb_size
    scs = carrier_config['scs']
    
    #get sample rate SampleRate = scs*2^(ceil(log2(carrier_prb_size*12/0.85)))*1000;
    samplerate_in_mhz = (scs * (2 ** np.ceil(np.log2(carrier_prb_size*12/0.85))) * 1000)/(10 ** 6)
    waveform_config["samplerate_in_mhz"] = samplerate_in_mhz

    td_waveform = nrssb.waveform_gen(waveform_config)
    scs = carrier_config['scs']
    kSSB = ssb_config["kSSB"]
    if not(scs == 30 and (kSSB % 2)):
        #matlab 5G toolbox ssb processing has one bug for 30khz scs and odd kSSB processing in hSSBurst.m
        #when calculate phase compensation, the carrier frequency should not add info.FrequencyOffsetSSB
        assert np.allclose(waveform_ref, td_waveform, atol=1e-5)


    