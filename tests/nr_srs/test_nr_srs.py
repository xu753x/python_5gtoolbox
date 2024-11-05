# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile

from tests.nr_srs import nr_srs_testvector
from py5gphy.nr_srs import nr_srs
from py5gphy.common import nr_slot

def get_testvectors():
    path = "tests/nr_srs/testvectors"
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
        if f.endswith(".mat") and f.startswith("nrSRS_testvec"):
        #if f.endswith(".mat") and f.startswith("nrSRS_testvec_1_scs_15khz_BW_20_NumSRSPorts_1_CSRS_0_BSRS_0"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_srs(filename):
    #read data
    matfile = io.loadmat(filename)
    srsInd_out, srsSymbols_out, fd_slot_data_ref ,srstv_cfg = \
        nr_srs_testvector.read_nrSRS_testvec_matfile(matfile)
    carrier_config, srs_config = \
        nr_srs_testvector.gen_srs_testvec_config(srstv_cfg)
    
    nrSRS = nr_srs.NrSRS(carrier_config, srs_config)

    #init slot data
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    
    fd_slot_data, RE_usage_inslot = \
        nr_slot.init_fd_slot(carrier_config['num_of_ant'], nrSRS.carrier_prb_size)
    
    sfn = 1 #SRS period is 10 slots, so any value is OK
    
    fd_slot_data, RE_usage_inslot = \
        nrSRS.process(fd_slot_data, RE_usage_inslot,sfn,srs_config['SRSOffset'])
    
    #verify
    samples_per_sym = int(fd_slot_data.shape[1]/14)
    NSRS_ap = srs_config["nrofSRSPorts"]
    #sel slot 1 data from fd_slot_data_ref, matlab 5g toolbox didn't divide sqrt(num_of_ports), add here
    sel_fd_slot_data_ref = fd_slot_data_ref[:,samples_per_sym*14:samples_per_sym*14*2]/math.sqrt(NSRS_ap)

    assert np.allclose(fd_slot_data, sel_fd_slot_data_ref,atol=1e-5)

    