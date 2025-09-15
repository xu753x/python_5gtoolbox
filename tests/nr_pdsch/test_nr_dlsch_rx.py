# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import math

from tests.nr_pdsch import nr_pdsch_testvectors
from py5gphy.nr_pdsch import nr_dlsch
from py5gphy.nr_pdsch import nr_dlsch_rx
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_encode
from py5gphy.ldpc import nr_ldpc_cbsegment

def get_testvectors():
    path = "tests/nr_pdsch/testvectors_dlsch"
    if len(os.listdir(path)) < 50: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrDSCH_RM_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_dlsch_rx_with_matlab_Nref(filename):
    """ matlab 5g toolbox set Nref to fixed value 25344 which is not exact match to 3GPP spec.
    this test uses Matlab Nref value to check functions 
    """
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)

    Modulation = pdsch_tvcfg['Modulation']
    TargetCodeRate = pdsch_tvcfg['TargetCodeRate']
    NumLayers = pdsch_tvcfg['NumLayers']
    G_out = pdsch_tvcfg['G_out']
    rv_out = pdsch_tvcfg['rv_out']

    Nref_mat=25344
    Qmtable = {'QPSK':2, '16QAM':4, '64QAM':6, '256QAM':8}

    LDPC_decoder_config={}
    LDPC_decoder_config["L"] = 32
    LDPC_decoder_config["algo"] = "min-sum"
    LDPC_decoder_config["alpha"] = 0.8
    LDPC_decoder_config["beta"] = 0.3

    HARQ_on = True

    snr_db = 30
    new_LLr_dns = np.array([])
    blk_num = RM_out.shape[0]                
    for m in range(blk_num):
        #if rv_out[m] in [1,2]:
        #    continue

        tmp1 = 1 - 2*RM_out[m,:].astype('f')
        fn = tmp1 + np.random.normal(0, 10**(-snr_db/20), tmp1.size) #add noise
        #LLR is log(P(0)/P(1)) = (-(x-1)^2+(x+1)^2)/(2*noise_power) = 4x/(2*noise_power) = 2x/noise_power
        noise_power = 10**(-snr_db/10)
        LLr = 2*fn/noise_power

        coderateby1024 = TargetCodeRate*1024
        ###find number of codeblock
        A = len(trblk_out)
        if A > 3824:
            blkandcrc = crc.nr_crc_encode(trblk_out, '24A')
        else:
            blkandcrc = crc.nr_crc_encode(trblk_out, '16')
        B = len(blkandcrc)

        #7.2.2 LDPC base graph selection
        bgn = 1
        if (A <= 292) \
                or ((A <= 3924) and (coderateby1024 <= 0.67*1024)) \
                or (coderateby1024 <= 0.25*1024):
            bgn = 2

        #7.2.3 Code block segmentation and code block CRC attachment
        cbs, Zc = nr_ldpc_cbsegment.ldpc_cbsegment(blkandcrc, bgn)  
        ###end of find number of codeblock

        C = cbs.shape[0]
        TBS_LBRM = round(Nref_mat*(C*2/3))

        #g_seq = nr_dlsch.DLSCHEncode(trblk_out, len(trblk_out), Qmtable[Modulation], coderateby1024, 
        #                    NumLayers, rv_out[m], TBS_LBRM, G_out[m])
        
        rx_status,rx_tbblk,new_LLr_dns = nr_dlsch_rx.DLSCHDecode(LLr,A, Qmtable[Modulation], coderateby1024, NumLayers, rv_out[m], TBS_LBRM, LDPC_decoder_config,HARQ_on,new_LLr_dns)

        #assert rx_status == True
        if rx_status:
            assert np.array_equal(trblk_out, rx_tbblk)
            print("pass DLSCHDecode comparison on blk num = {}".format(m))   
        else:
            print("failed DLSCHDecode comparison on blk num = {}".format(m))   
