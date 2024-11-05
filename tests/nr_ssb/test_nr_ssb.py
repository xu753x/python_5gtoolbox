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

def get_highphy_testvectors():
    path = "tests/nr_ssb/testvectors_highphy"
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
        if f.endswith(".mat") and f.startswith("nrSSB_highphy_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_highphy_testvectors())
def test_ssb_highphy(filename):
    matfile = io.loadmat(filename)
    
    waveform, fd_slot_data_ref, ssb_tvcfg = nr_ssb_testvectors.read_ssb_testvec_matfile(matfile)

    carrier_config,ssb_config = nr_ssb_testvectors.gen_ssb_testvec_config(ssb_tvcfg)

    nrssb = nr_ssb.NrSSB(carrier_config, ssb_config)
    carrier_prb_size = nrssb.carrier_prb_size
    num_of_ant = carrier_config["num_of_ant"]
    numofslot = fd_slot_data_ref.shape[1] // (carrier_prb_size*12*14)
    
    for m in range(numofslot):
        slot = m
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)
        sfn = int(slot // (carrier_config["scs"]/15*10))
        fd_slot_data, RE_usage_inslot = nrssb.process(fd_slot_data, RE_usage_inslot, sfn, slot)

        sel_ref_fdslot_data = fd_slot_data_ref[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]
        assert np.allclose(fd_slot_data, sel_ref_fdslot_data, atol=1e-5)


    