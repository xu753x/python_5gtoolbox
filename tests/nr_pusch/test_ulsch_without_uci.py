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
def test_nr_ulsch_without_uci(filename):
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
    num_of_layers = pusch_config['num_of_layers']
    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    nPMI = pusch_config['nPMI']
    NumCDMGroupsWithoutData = pusch_config['DMRS']["NumCDMGroupsWithoutData"]
    rvlist = pusch_config['rv']
        
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)

    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)
    
    slot_num = codeword_out_ref.shape[0]
    for slot in range(slot_num):
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(nNrOfAntennaPorts, carrier_prbsize)

        fd_slot_data, RE_usage_inslot, DMRS_symlist = nr_pusch_dmrs.process(fd_slot_data,RE_usage_inslot, pusch_config, slot)

        #calculate Gtotal after 6.2.7 Data and control multiplexing
        RE_usage_inslot, pusch_data_RE_num = \
            nrpusch_resource_mapping.pusch_data_re_mapping_prepare(RE_usage_inslot, pusch_config)
        Gtotal = Qm * num_of_layers * pusch_data_RE_num

        #ULSCH CRC and codeblock segment, cbs(code blocks) is used to calculate UCI resources
        cbs, Zc, bgn = nr_ulsch.ULSCH_Crc_CodeBlockSegment(trblk_out, TBSize, coderateby1024)

        G_ULSCH = Gtotal 
        #ULSCH LDPC encode, rate matching and code block concatenation from 6.2.4 to 6.2.6
        g_ulsch = nr_ulsch.ULSCH_ldpc_ratematch(cbs, Zc, bgn, Qm, G_ULSCH, num_of_layers, rvlist[slot])

        assert np.array_equal(g_ulsch, codeword_out_ref[slot,:])
        #print("pass PUSCH DMRS processing")   

