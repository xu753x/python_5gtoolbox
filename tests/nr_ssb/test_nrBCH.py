# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np
import json

from py5gphy.nr_ssb import nrBCH

def get_mib_testvectors():
    path = "tests/nr_ssb/testvectors"
    if len(os.listdir(path)) < 20: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("mib_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_mib_testvectors())
def test_genBCHMIB(filename):
    matfile = io.loadmat(filename)
    #read mat file
    mib_ref = matfile["mib"][0]
    sfn = matfile['sfn'][0][0]
    ssb_config = {}
    ssb_config["kSSB"] = matfile['burst']['kSSB'][0][0][0][0]
    ssb_config["MIB"] = {}
    ssb_config["MIB"]["subCarrierSpacingCommon"] = matfile['burst']['SubcarrierSpacingCommon'][0][0][0][0]
    ssb_config["MIB"]["dmrs_TypeA_Position"] = matfile['burst']['DMRSTypeAPosition'][0][0][0][0]
    ssb_config["MIB"]["pdcch_ConfigSIB1"] = matfile['burst']['PDCCHConfigSIB1'][0][0][0][0]
    ssb_config["MIB"]["cellBarred"] = matfile['burst']['CellBarred'][0][0][0][0]
    ssb_config["MIB"]["intraFreqReselection"] = matfile['burst']['IntraFreqReselection'][0][0][0][0]
                
    mib = nrBCH.genBCHMIB(ssb_config, sfn)
    assert np.array_equal(mib, mib_ref)
                
def get_nrBCH_testvectors():
    path = "tests/nr_ssb/testvectors"
    if len(os.listdir(path)) < 20: #desn't unzip testvectors
        zipfile_lists = []
        for f in os.listdir(path):
            if f.endswith(".zip"):
                zipfile_lists.append(path + '/' + f)

        for zipfile in zipfile_lists:
            zObject = ZipFile(zipfile, 'r')
            zObject.extractall(path)

    file_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat") and f.startswith("nrBCH_testvec"):
            file_lists.append(path + '/' + f)
                        
    return file_lists

@pytest.mark.parametrize('filename', get_nrBCH_testvectors())
def test_nrBCHencode(filename):
    path = "py5gphy/nr_default_config/"
    afile = "default_ssb_config.json"
    with open(path + afile, 'r') as f:
        ssb_config = json.load(f)

    matfile = io.loadmat(filename)
    #read mat file
    trblk = matfile['trblk'][0]
    cdBlk = matfile['cdBlk'][0]
    sfn = matfile['sfn'][0][0]
    HRF = matfile['hrf'][0][0]
    idxOffset = matfile['idxOffset'][0][0]
    NcellID = matfile['NcellID'][0][0]
    ssb_config["kSSB"] = idxOffset  

    rm_bitseq = nrBCH.nrBCHencode(trblk, ssb_config, sfn,HRF,NcellID)
    assert np.array_equal(cdBlk, rm_bitseq)
                
    