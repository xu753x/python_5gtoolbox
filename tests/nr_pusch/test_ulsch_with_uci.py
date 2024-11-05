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
def test_nr_ulsch_with_uci(filename):
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
    rnti = pusch_config['rnti']
    nNid = pusch_config['nNid']
    nTransPrecode = pusch_config['nTransPrecode']
    nPMI = pusch_config['nPMI']
    RBSize = pusch_config['ResAlloType1']['RBSize']
        
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)

    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)
    slot_num = codeword_out_ref.shape[0]
    for slot in range(slot_num):
        #
        pusch_config['ACKbits'] = effACK_out[slot]
        pusch_config['CSI1bits'] = csi1_out[slot]
        pusch_config['CSI2bits'] = csi2_out[slot]

        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(nNrOfAntennaPorts, carrier_prbsize)

        fd_slot_data, RE_usage_inslot, DMRSinfo = nr_pusch_dmrs.process(fd_slot_data,RE_usage_inslot, pusch_config, slot)
        DMRS_symlist = DMRSinfo['DMRS_symlist'] 

        #calculate Gtotal after 6.2.7 Data and control multiplexing
        RE_usage_inslot, pusch_data_RE_num = \
            nrpusch_resource_mapping.pusch_data_re_mapping_prepare(RE_usage_inslot, pusch_config)
        Gtotal = Qm * num_of_layers * pusch_data_RE_num

        g_seq = nr_pusch_uci.ULSCHandUCIProcess(pusch_config, trblk_out, Gtotal, rvlist[slot], DMRS_symlist)
        
        assert np.array_equal(g_seq, codeword_out_ref[slot,:])

                

