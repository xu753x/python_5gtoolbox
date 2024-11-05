# -*- coding:utf-8 -*-

import numpy as np
import json

def read_nrPRACH_all_testvec_matfile(matfile):
    """read PRACH nrPRACH_all_testvec* test vectors
    """
    waveform = matfile['waveform'][0]
    prachSymbols_out = matfile['prachSymbols_out'][0]
    prachGrid_out = matfile['prachGrid_out']

    prachtv_cfg = {}
    prachtv_cfg['Nfft'] = matfile['Nfft'][0][0]
    prachtv_cfg['LRA'] = matfile['LRA'][0][0]

    prachtv_cfg['SampleRate'] = matfile['SampleRate'][0][0]
    prachtv_cfg['CyclicPrefixLengths'] = matfile['CyclicPrefixLengths'][0][0]
    prachtv_cfg['GuardLengths'] = matfile['GuardLengths'][0][0]
    prachtv_cfg['SymbolLengths'] = matfile['SymbolLengths'][0][0]
    prachtv_cfg['OffsetLength'] = matfile['OffsetLength'][0][0]
    prachtv_cfg['Windowing'] = matfile['Windowing'][0][0]
    
    prachtv_cfg['carrier_scs'] = matfile['carrier_scs'][0][0]
    prachtv_cfg['NSizeGrid'] = matfile['NSizeGrid'][0][0]
    prachtv_cfg['DuplexMode'] = matfile['DuplexMode'][0]
    prachtv_cfg['ConfigurationIndex'] = matfile['ConfigurationIndex'][0][0]
    prachtv_cfg['msg1_SubcarrierSpacing'] = matfile['msg1_SubcarrierSpacing'][0][0]
    prachtv_cfg['SequenceIndex'] = matfile['SequenceIndex'][0][0]
    prachtv_cfg['PreambleIndex'] = matfile['PreambleIndex'][0][0]
    prachtv_cfg['ZeroCorrelationZone'] = matfile['ZeroCorrelationZone'][0][0]
    prachtv_cfg['FrequencyStart'] = matfile['FrequencyStart'][0][0]
    prachtv_cfg['FrequencyIndex'] = matfile['FrequencyIndex'][0][0]
    prachtv_cfg['TimeIndex'] = matfile['TimeIndex'][0][0]
    prachtv_cfg['ActivePRACHSlot'] = matfile['ActivePRACHSlot'][0][0]
    prachtv_cfg['NPRACHSlot'] = matfile['NPRACHSlot'][0][0]
    prachtv_cfg['prach_subframes'] = matfile['prach_subframes'][0][0]

    return waveform, prachSymbols_out, prachGrid_out, prachtv_cfg

def gen_prach_alltestvec_config(prachtv_cfg):
    """ genrate UL carrier config and prach config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_prach_config.json", 'r') as f:
        prach_config_file = json.load(f)
    
    prach_config = prach_config_file['config']
    prach_parameters = prach_config_file['parameters']
    
    carrier_config['BW'] = 20 #used for all generated testvector 
    carrier_config['scs'] = prachtv_cfg['carrier_scs']
    carrier_config['duplex_type'] = prachtv_cfg['DuplexMode']

    prach_config['prach_ConfigurationIndex'] = prachtv_cfg['ConfigurationIndex']
    prach_config['msg1_FDM'] = 4 #used by all testvector
    prach_config['msg1_FrequencyStart'] = prachtv_cfg['FrequencyStart']
    prach_config['zeroCorrelationZoneConfig'] = prachtv_cfg['ZeroCorrelationZone']
    prach_config['msg1_SubcarrierSpacing'] = prachtv_cfg['msg1_SubcarrierSpacing']
    prach_config['prach_RootSequenceIndex'] = prachtv_cfg['SequenceIndex']

    prach_parameters['PreambleIndex'] = prachtv_cfg['PreambleIndex']
    prach_parameters['nRA'] = prachtv_cfg['FrequencyIndex']
    prach_parameters['ActivePRACHslotinSubframe'] = prachtv_cfg['ActivePRACHSlot']
    prach_parameters['nRA_t'] = prachtv_cfg['TimeIndex']
    prach_parameters['PRACH_subframe'] = prachtv_cfg['prach_subframes']
    
    return carrier_config, prach_config, prach_parameters

