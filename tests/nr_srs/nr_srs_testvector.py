# -*- coding:utf-8 -*-

import numpy as np
import json

def read_nrSRS_testvec_matfile(matfile):
    srstv_cfg = {}
    srstv_cfg['scs'] = matfile["scs"][0][0]
    srstv_cfg['BW'] = matfile["BW"][0][0]
    srstv_cfg['NumSRSPorts'] = matfile["NumSRSPorts"][0][0]
    srstv_cfg['SymbolStart'] = matfile["SymbolStart"][0][0]
    srstv_cfg['NumSRSSymbols'] = matfile["NumSRSSymbols"][0][0]
    srstv_cfg['FrequencyStart'] = matfile["FrequencyStart"][0][0]
    srstv_cfg['NRRC'] = matfile["NRRC"][0][0]
    srstv_cfg['CSRS'] = matfile["CSRS"][0][0]
    srstv_cfg['BSRS'] = matfile["BSRS"][0][0]
    srstv_cfg['KTC'] = matfile["KTC"][0][0]
    srstv_cfg['KBarTC'] = matfile["KBarTC"][0][0]
    srstv_cfg['CyclicShift'] = matfile["CyclicShift"][0][0]
    srstv_cfg['GroupSeqHopping'] = matfile["GroupSeqHopping"][0]
    srstv_cfg['NSRSID'] = matfile["NSRSID"][0][0]

    srsInd_out = matfile["srsInd_out"]
    srsSymbols_out = matfile["srsSymbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return srsInd_out, srsSymbols_out, fd_slot_data, srstv_cfg

def gen_srs_testvec_config(srstv_cfg):
    """ genrate UL carrier config and srs config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_srs_config.json", 'r') as f:
        srs_config = json.load(f)
    
    carrier_config['BW'] = srstv_cfg['BW']
    carrier_config['scs'] = srstv_cfg['scs']
    carrier_config['num_of_ant'] = srstv_cfg['NumSRSPorts']

    srs_config['nrofSRSPorts'] = srstv_cfg['NumSRSPorts']
    srs_config['KTC'] = srstv_cfg['KTC']
    srs_config['combOffset'] = srstv_cfg['KBarTC']
    srs_config['cyclicShift'] = srstv_cfg['CyclicShift']
    srs_config['startPosition'] = 14 - 1 - srstv_cfg['SymbolStart']
    srs_config['nrofSymbols'] = srstv_cfg['NumSRSSymbols']
    srs_config['freqDomainPosition'] = srstv_cfg['NRRC']
    srs_config['freqDomainShift'] = srstv_cfg['FrequencyStart']
    srs_config['cSRS'] = srstv_cfg['CSRS']
    srs_config['bSRS'] = srstv_cfg['BSRS']
    srs_config['groupOrSequenceHopping'] = srstv_cfg['GroupSeqHopping']
    srs_config['sequenceId'] = srstv_cfg['NSRSID']
    srs_config['SRSPeriodicity'] = 10
    srs_config['SRSOffset'] = 1

    return carrier_config, srs_config