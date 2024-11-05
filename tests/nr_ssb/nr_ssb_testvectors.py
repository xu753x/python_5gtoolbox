# -*- coding:utf-8 -*-

import numpy as np
import json

def read_ssb_testvec_matfile(matfile):
    """ read SSB testvectors
    """
    ssb_tvcfg = {}

    ssb_tvcfg['scs'] = matfile["scs"][0][0]
    ssb_tvcfg['BW'] = matfile["BW"][0][0]
    ssb_tvcfg['NCellID'] = matfile["NCellID"][0][0]
    ssb_tvcfg['BlockPattern_idx'] = matfile["BlockPattern_idx"][0][0]
    ssb_tvcfg['carrier_freq_in_mhz'] = matfile["carrier_freq_in_mhz"][0][0]
    ssb_tvcfg['TransmittedBlocks'] = matfile["TransmittedBlocks"][0]
    ssb_tvcfg['Period'] = matfile["Period"][0][0]
    ssb_tvcfg['NCRBSSB'] = matfile["NCRBSSB"][0][0]
    ssb_tvcfg['KSSB'] = matfile["KSSB"][0][0]
    ssb_tvcfg['DMRSTypeAPosition'] = matfile["DMRSTypeAPosition"][0][0]
    ssb_tvcfg['CellBarred_idx'] = matfile["CellBarred_idx"][0][0]
    ssb_tvcfg['IntraFreqReselection_idx'] = matfile["IntraFreqReselection_idx"][0][0]
    ssb_tvcfg['PDCCHConfigSIB1'] = matfile["PDCCHConfigSIB1"][0][0]

    if 'highphyData' in matfile:
        highphyData = matfile["highphyData"]
    else:
        highphyData = 0
    
    if 'waveform' in matfile:
        waveform = matfile["waveform"]
    else:
        waveform = 0
    
    return waveform, highphyData, ssb_tvcfg

def gen_ssb_testvec_config(ssb_tvcfg):
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    
    carrier_config['BW'] = ssb_tvcfg['BW']
    carrier_config['scs'] = ssb_tvcfg['scs']
    carrier_config['num_of_ant'] = 1
    carrier_config['maxMIMO_layers'] = 1
    carrier_config['PCI'] = ssb_tvcfg['NCellID']
    carrier_config['carrier_frequency_in_mhz'] = ssb_tvcfg['carrier_freq_in_mhz']

    if ssb_tvcfg['BlockPattern_idx'] == 0:
        ssb_config["SSBPattern"] = "Case A"
    elif ssb_tvcfg['BlockPattern_idx'] == 1:
        ssb_config["SSBPattern"] = "Case B"
    elif ssb_tvcfg['BlockPattern_idx'] == 2:
        ssb_config["SSBPattern"] = "Case C"
    
    ssb_config["ssb_PositionsInBurst"] = ssb_tvcfg["TransmittedBlocks"]
    ssb_config["SSBperiod"] = ssb_tvcfg["Period"]
    ssb_config["kSSB"] = ssb_tvcfg["KSSB"]
    ssb_config["NSSB_CRB"] = ssb_tvcfg["NCRBSSB"]

    if ssb_tvcfg['scs'] == 15:
        ssb_config["MIB"]["subCarrierSpacingCommon"] = 0
    else:
        ssb_config["MIB"]["subCarrierSpacingCommon"] = 1
    
    ssb_config["MIB"]["dmrs_TypeA_Position"] = ssb_tvcfg["DMRSTypeAPosition"] - 2
    ssb_config["MIB"]["pdcch_ConfigSIB1"] = ssb_tvcfg["PDCCHConfigSIB1"] 
    ssb_config["MIB"]["cellBarred"] = ssb_tvcfg["CellBarred_idx"] 
    ssb_config["MIB"]["intraFreqReselection"] = ssb_tvcfg["IntraFreqReselection_idx"] 

    return carrier_config,ssb_config




