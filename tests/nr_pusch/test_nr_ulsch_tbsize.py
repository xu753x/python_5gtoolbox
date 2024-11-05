# -*- coding: utf-8 -*-
import pytest
from scipy import io
import os
import numpy as np
import math
from zipfile import ZipFile 

from tests.nr_pusch import nr_pusch_testvectors
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch

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
        #if f.endswith(".mat") and f.startswith("nrULSCH_only_noCSIbits_testvec"):
        if f.endswith(".mat") and f.startswith("nrULSCH_without_uci_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_ulsch_tbsize(filename):
    """ 
    """
    #read data
    matfile = io.loadmat(filename)
    effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out, \
              layermap_out, fd_slot_data, waveform, pusch_tvcfg = \
        nr_pusch_testvectors.read_ulsch_testvec_matfile(matfile)
    
    carrier_config, pusch_config = nr_pusch_testvectors.gen_pusch_testvec_config(pusch_tvcfg)

    Qm_ref = pusch_tvcfg['Qm']
    TargetCodeRateby1024_ref = pusch_tvcfg['TargetCodeRateby1024']
    TBsize_ref = len(trblk_out)

    #nrpusch = nr_pusch.NrPUSCH(carrier_config, pusch_config)
    TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(pusch_config)

    assert Qm_ref == Qm
    assert TargetCodeRateby1024_ref == coderateby1024
    assert TBsize_ref == TBSize
    print("pass ULSCH TBSize comparison, TBSize={}".format(TBSize))   

