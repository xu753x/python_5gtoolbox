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
from py5gphy.nr_pusch import nr_pusch_uci
from py5gphy.nr_pusch import nr_pusch_process
from py5gphy.nr_pusch import nr_pusch_precoding

def get_testvectors():
    path = "tests/nr_pusch/testvectors_ulsch_with_uci"
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
        #if f.endswith(".mat") and f.startswith("nrULSCH_withUCIbits_testvec_2019_mcstable_2_iMCS_11_DMRSAdditionalPosition_3_EnableULSCH_0_EnableACK_1_EnableCSI1_0_EnableCSI2_0"):
        if f.endswith(".mat") and f.startswith("nrULSCH_withUCIbits_testvec_"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_pusch_process(filename):
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

    num_of_layers = pusch_config['num_of_layers']
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    nPMI = pusch_config['nPMI']
    rnti = pusch_config['rnti']
    nNid = pusch_config['nNid']
    nTransPrecode = pusch_config['nTransPrecode']
    nPMI = pusch_config['nPMI']
    RBSize = pusch_config['ResAlloType1']['RBSize']
        
    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)
    slot_num = codeword_out_ref.shape[0]
    for slot in range(slot_num):
                
        g_seq = codeword_out_ref[slot,:]
        precoding_matrix = nr_pusch_precoding.get_precoding_matrix(num_of_layers, nNrOfAntennaPorts, nPMI)
        ##scrambling, modulation, layer mapping, precoding
        precoded = nr_pusch_process.nr_pusch_process( \
            g_seq, rnti, nNid, Qm, num_of_layers,nTransPrecode, \
            RBSize, nNrOfAntennaPorts, precoding_matrix)
        outsym_ref = layermap_out[slot*nNrOfAntennaPorts:(slot+1)*nNrOfAntennaPorts,:]
        assert np.allclose(precoded, outsym_ref, atol=1e-5)

