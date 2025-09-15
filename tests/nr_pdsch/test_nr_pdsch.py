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
def test_nr_pdsch(filename):
    """ the main pupose this this test is to test PDSCH scrambling, modulation and resurce mapping
     defined in 38.211 7.3.1
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
    for m in range(numofslot):
        slot = m
        
        num_of_ant = nrpdsch.carrier_config["num_of_ant"]
        carrier_prb_size = nrpdsch.carrier_prb_size
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)

        #pdsch processing
        fd_slot_data, RE_usage_inslot = nrpdsch.process(fd_slot_data,RE_usage_inslot, slot)
                            
        sel_ref_fdslot_data = ref_fd_slot_data[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]
        assert np.allclose(fd_slot_data, sel_ref_fdslot_data, atol=1e-5)
        print("pass comparison for slot {}".format(m))

def get_short_pdsch_testvectors():
    path = "tests/nr_pdsch/testvectors_short_pdsch"
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
        if f.endswith(".mat") and f.startswith("nrPDSCH_short_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_short_pdsch_testvectors())
def test_nr_short_pdsch(filename):
    """ the main pupose this this test is to test PDSCH scrambling, modulation and resurce mapping
    test pdsch with shorter number of symbol
     defined in 38.211 7.3.1
     the teste vectors contain only PDSCH channel, no SSB/PDCCH/CSI-RS channel which may have PRB resource conflict with PDSCH
     """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, ref_fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)
    pdsch_config["data_source"] = [1,0,0,1]
    pdsch_config["precoding_matrix"] = np.array([])
    pdsch_config["NrOfSymbols"] = pdsch_tvcfg['pdschsym_dur']

    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    numofslot = RM_out.shape[0]
    for m in range(numofslot):
        slot = m
        
        num_of_ant = nrpdsch.carrier_config["num_of_ant"]
        carrier_prb_size = nrpdsch.carrier_prb_size
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)

        #pdsch processing
        fd_slot_data, RE_usage_inslot = nrpdsch.process(fd_slot_data,RE_usage_inslot, slot)
                            
        sel_ref_fdslot_data = ref_fd_slot_data[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]
        assert np.allclose(fd_slot_data, sel_ref_fdslot_data, atol=1e-5)
        print("pass comparison for slot {}".format(m))

