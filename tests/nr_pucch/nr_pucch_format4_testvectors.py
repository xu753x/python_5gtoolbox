# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pucch_format4_testvec_matfile(matfile):
    pucchformat4_tvcfg = {}
    pucchformat4_tvcfg['scs'] = matfile["scs"][0][0]
    pucchformat4_tvcfg['BW'] = matfile["BW"][0][0]
    pucchformat4_tvcfg['Modulation'] = matfile["Modulation"][0]
    pucchformat4_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pucchformat4_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    pucchformat4_tvcfg['SecondHopStartPRB'] = matfile["SecondHopStartPRB"][0][0]
    pucchformat4_tvcfg['FrequencyHopping'] = matfile["FrequencyHopping"][0]
    pucchformat4_tvcfg['GroupHopping'] = matfile["GroupHopping"][0]
    pucchformat4_tvcfg['HoppingID'] = matfile["HoppingID"][0][0]
    pucchformat4_tvcfg['NID'] = matfile["NID"][0][0]
    pucchformat4_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    pucchformat4_tvcfg['SpreadingFactor'] = matfile["SpreadingFactor"][0][0]
    pucchformat4_tvcfg['OCCI'] = matfile["OCCI"][0][0]
    pucchformat4_tvcfg['NumUCIBits'] = matfile["NumUCIBits"][0][0]
    pucchformat4_tvcfg['AdditionalDMRS'] = matfile["AdditionalDMRS"][0][0]
    
    codeword_out = matfile["codeword_out"]
    symbols_out = matfile["symbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return codeword_out, symbols_out, fd_slot_data, pucchformat4_tvcfg

def gen_pucchformat4_testvec_config(pucchformat4_tvcfg):
    """ genrate UL carrier config and pucch format4 config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pucch_format4_config.json", 'r') as f:
        pucch_format4_config = json.load(f)
    
    carrier_config['BW'] = pucchformat4_tvcfg['BW']
    carrier_config['scs'] = pucchformat4_tvcfg['scs']
    carrier_config['num_of_ant'] = 1

    pucch_format4_config['startingPRB'] = pucchformat4_tvcfg['PRBSet'][0]
    
    if pucchformat4_tvcfg['FrequencyHopping'] == 'intraSlot':
        pucch_format4_config['intraSlotFrequencyHopping'] = 'enabled'
    else:
        pucch_format4_config['intraSlotFrequencyHopping'] = 'disabled'
        
    pucch_format4_config['secondHopPRB'] = pucchformat4_tvcfg['SecondHopStartPRB']
    
    pucch_format4_config['nrofSymbols'] = pucchformat4_tvcfg['SymbolAllocation'][1]
    pucch_format4_config['startingSymbolIndex'] = pucchformat4_tvcfg['SymbolAllocation'][0]
    pucch_format4_config['occ_Length'] = pucchformat4_tvcfg['SpreadingFactor']
    pucch_format4_config['occ_index'] = pucchformat4_tvcfg['OCCI']

    if pucchformat4_tvcfg['AdditionalDMRS']:
        pucch_format4_config['additionalDMRS'] = 'true'
    else:
        pucch_format4_config['additionalDMRS'] = 'false'

    if pucchformat4_tvcfg['Modulation'] == 'QPSK':
        pucch_format4_config['pi2BPSK'] = 'disabled'
    else:
        pucch_format4_config['pi2BPSK'] = 'enabled'

    pucch_format4_config['pucch_GroupHopping'] = pucchformat4_tvcfg['GroupHopping']
    pucch_format4_config['hoppingId'] = pucchformat4_tvcfg['HoppingID']

    pucch_format4_config['NumUCIBits'] = pucchformat4_tvcfg['NumUCIBits']
    d1 = np.tile(np.array([0,0,1,1]), int((pucch_format4_config['NumUCIBits'] // 4)+4))
    pucch_format4_config['UCIbits'] = d1[0:pucch_format4_config['NumUCIBits']]

    pucch_format4_config['NID'] = pucchformat4_tvcfg['NID']
    pucch_format4_config['RNTI'] = pucchformat4_tvcfg['RNTI']
    
    pucch_format4_config['Periodicity_in_slot'] = 1
    pucch_format4_config['slotoffset'] = 0
    

    return carrier_config, pucch_format4_config