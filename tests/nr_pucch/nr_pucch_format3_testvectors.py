# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pucch_format3_testvec_matfile(matfile):
    pucchformat3_tvcfg = {}
    pucchformat3_tvcfg['scs'] = matfile["scs"][0][0]
    pucchformat3_tvcfg['BW'] = matfile["BW"][0][0]
    pucchformat3_tvcfg['Modulation'] = matfile["Modulation"][0]
    pucchformat3_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pucchformat3_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    pucchformat3_tvcfg['SecondHopStartPRB'] = matfile["SecondHopStartPRB"][0][0]
    pucchformat3_tvcfg['FrequencyHopping'] = matfile["FrequencyHopping"][0]
    pucchformat3_tvcfg['GroupHopping'] = matfile["GroupHopping"][0]
    pucchformat3_tvcfg['HoppingID'] = matfile["HoppingID"][0][0]
    pucchformat3_tvcfg['NID'] = matfile["NID"][0][0]
    pucchformat3_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    pucchformat3_tvcfg['NumUCIBits'] = matfile["NumUCIBits"][0][0]
    pucchformat3_tvcfg['AdditionalDMRS'] = matfile["AdditionalDMRS"][0][0]
    
    codeword_out = matfile["codeword_out"]
    symbols_out = matfile["symbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return codeword_out, symbols_out, fd_slot_data, pucchformat3_tvcfg

def gen_pucchformat3_testvec_config(pucchformat3_tvcfg):
    """ genrate UL carrier config and pucch format3 config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pucch_format3_config.json", 'r') as f:
        pucch_format3_config = json.load(f)
    
    carrier_config['BW'] = pucchformat3_tvcfg['BW']
    carrier_config['scs'] = pucchformat3_tvcfg['scs']
    carrier_config['num_of_ant'] = 1

    pucch_format3_config['startingPRB'] = pucchformat3_tvcfg['PRBSet'][0]
    pucch_format3_config['nrofPRBs'] = len(pucchformat3_tvcfg['PRBSet'])
    if pucchformat3_tvcfg['FrequencyHopping'] == 'intraSlot':
        pucch_format3_config['intraSlotFrequencyHopping'] = 'enabled'
    else:
        pucch_format3_config['intraSlotFrequencyHopping'] = 'disabled'
        
    pucch_format3_config['secondHopPRB'] = pucchformat3_tvcfg['SecondHopStartPRB']
    
    pucch_format3_config['nrofSymbols'] = pucchformat3_tvcfg['SymbolAllocation'][1]
    pucch_format3_config['startingSymbolIndex'] = pucchformat3_tvcfg['SymbolAllocation'][0]

    if pucchformat3_tvcfg['AdditionalDMRS']:
        pucch_format3_config['additionalDMRS'] = 'true'
    else:
        pucch_format3_config['additionalDMRS'] = 'false'

    if pucchformat3_tvcfg['Modulation'] == 'QPSK':
        pucch_format3_config['pi2BPSK'] = 'disabled'
    else:
        pucch_format3_config['pi2BPSK'] = 'enabled'

    pucch_format3_config['pucch_GroupHopping'] = pucchformat3_tvcfg['GroupHopping']
    pucch_format3_config['hoppingId'] = pucchformat3_tvcfg['HoppingID']

    pucch_format3_config['NumUCIBits'] = pucchformat3_tvcfg['NumUCIBits']
    d1 = np.tile(np.array([1,0,1,0]), int((pucch_format3_config['NumUCIBits'] // 4)+4))
    pucch_format3_config['UCIbits'] = d1[0:pucch_format3_config['NumUCIBits']]

    pucch_format3_config['NID'] = pucchformat3_tvcfg['NID']
    pucch_format3_config['RNTI'] = pucchformat3_tvcfg['RNTI']
    
    pucch_format3_config['Periodicity_in_slot'] = 1
    pucch_format3_config['slotoffset'] = 0
    

    return carrier_config, pucch_format3_config