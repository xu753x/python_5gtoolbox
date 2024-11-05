# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import math

from tests.nr_pdsch import nr_pdsch_testvectors
from py5gphy.nr_pdsch import nr_dlsch
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.crc import crc
from py5gphy.ldpc import nr_ldpc_encode
from py5gphy.ldpc import nr_ldpc_cbsegment

def get_testvectors():
    path = "tests/nr_pdsch/testvectors_dlsch"
    if len(os.listdir(path)) < 10: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    f = open("tests/nr_pdsch/not_match_testvectors.txt","w")
    f.write("matlab 5g toolbox set Nref to fixed value 25344 which is not exact match to 3GPP spec \n")
    f.write("here list testvectors that can not match with matlab \n")
    f.write("------------------\n\n")
    f.close()
    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrDSCH_RM_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_dlsch_with_matlab_Nref(filename):
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

    blk_num = RM_out.shape[0]                
    for m in range(blk_num):
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

        
        g_seq = nr_dlsch.DLSCHEncode(trblk_out, len(trblk_out), Qmtable[Modulation], coderateby1024, 
                            NumLayers, rv_out[m], TBS_LBRM, G_out[m])
        assert np.array_equal(g_seq, RM_out[m,:])
        print("pass DLSCHEncode comparison on blk num = {}".format(m))   

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_dlsch_without_matlab_Nref_value(filename):
    """ matlab 5g toolbox set Nref to fixed value 25344 which is not exact match to 3GPP spec.
    this test list all the files that doesn't match 3GPP spec
    """
    
    #read data
    matfile = io.loadmat(filename)
    trblk_out,RM_out, layermap_out, fd_slot_data, waveform, pdsch_tvcfg = \
        nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
    carrier_config, pdsch_config = nr_pdsch_testvectors.gen_pdsch_testvec_config(pdsch_tvcfg)

    rv_out = pdsch_tvcfg['rv_out']
    G_out = pdsch_tvcfg['G_out']

    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    TBS_LBRM = nrpdsch.info['TBS_LBRM']
    Qm = nrpdsch.info['Qm']
    coderateby1024 = nrpdsch.info['coderateby1024']
    num_of_layers = nrpdsch.pdsch_config['num_of_layers']

    numofslot = RM_out.shape[0]
    for m in range(numofslot):
        g_seq = nr_dlsch.DLSCHEncode(trblk_out, len(trblk_out), Qm, coderateby1024, 
                            num_of_layers, rv_out[m], TBS_LBRM, G_out[m])
        if np.array_equal(g_seq, RM_out[m,:]) == False:
            print("failed DLSCHEncode comparison on blk num = {}".format(m))    
            with open("tests/nr_pdsch/not_match_testvectors.txt","a") as f:
                f.write(filename+"blk num = {}".format(m) + "\n")

@pytest.mark.parametrize('filename', get_testvectors())
def test_nr_dlsch_parameter(filename):
    """ LDPC encoder takes too ong time.
    this test is to verify DLSCH parameters are correct and bypass CEC/LDPC encoder and rate matching
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

    nrpdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
    TBS_LBRM = nrpdsch.info['TBS_LBRM']

    Nref_mat=25344
    Qmtable = {'QPSK':2, '16QAM':4, '64QAM':6, '256QAM':8}


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

    ck = cbs[0,:]
    K = ck.size
    if bgn == 1:
        Zc = K // 22
        N = 66 * Zc
    else:
        Zc = K // 10
        N = 50 * Zc

    #cal using matlab para
    Ncb_mat = min(N, Nref_mat)

    #cal floolowing to 3gpp
    Nref = math.floor(TBS_LBRM / (C * 2/3))
    Ncb_3gpp = min(N, Nref)
    
    if( Ncb_3gpp != Ncb_mat):
        print("Nref={}, Ncb_3gpp = {}, Ncb_mat= {}".format(Nref,Ncb_3gpp,Ncb_mat))  
        
        