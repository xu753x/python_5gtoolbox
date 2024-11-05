# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math

from tests.nr_pusch import nr_pusch_testvectors
from py5gphy.nr_pusch import nr_pusch_dmrs
from py5gphy.nr_pusch import nr_pusch
from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch_precoding

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
def test_nr_ulsch_dmrs(filename):
    """ 
    """
    #read data
    matfile = io.loadmat(filename)
    effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out, \
              layermap_out, fd_slot_data_ref, waveform, pusch_tvcfg = \
        nr_pusch_testvectors.read_ulsch_testvec_matfile(matfile)
    
    carrier_config, pusch_config = nr_pusch_testvectors.gen_pusch_testvec_config(pusch_tvcfg)

    scs = carrier_config['scs']
    BW = carrier_config['BW']
    num_of_layers = pusch_config['num_of_layers']
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    nPMI = pusch_config['nPMI']
    NumCDMGroupsWithoutData = pusch_config['DMRS']["NumCDMGroupsWithoutData"]
    #following to 38.214 Table 6.2.2-1: The ratio of PUSCH EPRE to DM-RS EPRE, get PUSCH DMRS scaling factor
    #matlab toolbox didn;t select DMRS_scaling, need compensation 
    if NumCDMGroupsWithoutData == 1:
        DMRS_scaling = 1 #0db EPRE ratio
    else:
        DMRS_scaling = 10 ** (-3/20) #-3db EPRE ratio
    
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    
    slot_num = fd_slot_data_ref.shape[0]
    for slot in range(slot_num):
        sel_ref_fdslot_data = fd_slot_data_ref[:,slot*carrier_prbsize*12*14:(slot+1)*carrier_prbsize*12*14]
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(nNrOfAntennaPorts, carrier_prbsize)

        fd_slot_data, RE_usage_inslot, DMRSinfo = nr_pusch_dmrs.process(fd_slot_data,RE_usage_inslot, pusch_config, slot)

        for ant in range(nNrOfAntennaPorts):
            dmrs_indice = fd_slot_data[ant].nonzero()
            dmrsdata = fd_slot_data[ant,dmrs_indice]
            
            dmrsdata_ref = sel_ref_fdslot_data[ant,dmrs_indice]
            assert np.allclose(dmrsdata, dmrsdata_ref*DMRS_scaling, atol=1e-5)

        #print("pass PUSCH DMRS processing")   

