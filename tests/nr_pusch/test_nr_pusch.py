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
def test_nr_pusch(filename):
    """ the main pupose this this test is to test PUSCH scrambling, modulation and resurce mapping
     
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

    nrpusch = nr_pusch.NrPUSCH(carrier_config,pusch_config)
    
    for m in range(numofslot):
        slot = m
        
        num_of_ant = nrpusch.carrier_config["num_of_ant"]
        carrier_prb_size = nrpusch.carrier_prb_size
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prb_size)

        #pdsch processing
        fd_slot_data, RE_usage_inslot = nrpusch.process(fd_slot_data,RE_usage_inslot,slot)
                            
        sel_ref_fdslot_data = fd_slot_data_ref[:,m*carrier_prb_size*12*14:(m+1)*carrier_prb_size*12*14]
        for sym in range(14):
            sel_sym = sel_ref_fdslot_data[:,sym*carrier_prb_size*12:(sym+1)*carrier_prb_size*12]
            sel_sym[:,RE_usage_inslot[0,sym*carrier_prb_size*12:(sym+1)*carrier_prb_size*12]==nr_slot.get_REusage_value('PUSCH-DMRS')] *= DMRS_scaling
            
        assert np.allclose(fd_slot_data, sel_ref_fdslot_data, atol=1e-5)
        print("pass comparison for slot {}".format(m))