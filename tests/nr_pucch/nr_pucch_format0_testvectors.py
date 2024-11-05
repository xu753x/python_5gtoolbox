# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pucch_format0_testvec_matfile(matfile):
    pucchformat0_tvcfg = {}
    pucchformat0_tvcfg['scs'] = matfile["scs"][0][0]
    pucchformat0_tvcfg['BW'] = matfile["BW"][0][0]
    pucchformat0_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pucchformat0_tvcfg['PRBSet'] = matfile["PRBSet"][0][0]
    pucchformat0_tvcfg['SecondHopStartPRB'] = matfile["SecondHopStartPRB"][0][0]
    pucchformat0_tvcfg['FrequencyHopping'] = matfile["FrequencyHopping"][0]
    pucchformat0_tvcfg['GroupHopping'] = matfile["GroupHopping"][0]
    pucchformat0_tvcfg['HoppingID'] = matfile["HoppingID"][0][0]
    pucchformat0_tvcfg['InitialCyclicShift'] = matfile["InitialCyclicShift"][0][0]
    pucchformat0_tvcfg['NumUCIBits'] = matfile["NumUCIBits"][0][0]
    pucchformat0_tvcfg['DataSourceUCI'] = matfile["DataSourceUCI"][0]
    pucchformat0_tvcfg['DataSourceSR'] = matfile["DataSourceSR"][0][0]
    
    codeword_out = matfile["codeword_out"]
    symbols_out = matfile["symbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return codeword_out, symbols_out, fd_slot_data, pucchformat0_tvcfg

def gen_pucchformat0_testvec_config(pucchformat0_tvcfg):
    """ genrate UL carrier config and pucch format0 config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pucch_format0_config.json", 'r') as f:
        pucch_format0_config = json.load(f)
    
    carrier_config['BW'] = pucchformat0_tvcfg['BW']
    carrier_config['scs'] = pucchformat0_tvcfg['scs']
    carrier_config['num_of_ant'] = 1

    pucch_format0_config['startingPRB'] = pucchformat0_tvcfg['PRBSet']
    if pucchformat0_tvcfg['FrequencyHopping'] == 'intraSlot':
        pucch_format0_config['intraSlotFrequencyHopping'] = 'enabled'
    else:
        pucch_format0_config['intraSlotFrequencyHopping'] = 'disabled'
        
    pucch_format0_config['secondHopPRB'] = pucchformat0_tvcfg['SecondHopStartPRB']
    pucch_format0_config['initialCyclicShift'] = pucchformat0_tvcfg['InitialCyclicShift']
    pucch_format0_config['nrofSymbols'] = pucchformat0_tvcfg['SymbolAllocation'][1]
    pucch_format0_config['startingSymbolIndex'] = pucchformat0_tvcfg['SymbolAllocation'][0]
    pucch_format0_config['pucch_GroupHopping'] = pucchformat0_tvcfg['GroupHopping']
    pucch_format0_config['hoppingId'] = pucchformat0_tvcfg['HoppingID']
    pucch_format0_config['numHARQbits'] = pucchformat0_tvcfg['NumUCIBits']
    pucch_format0_config['HARQbits'] = pucchformat0_tvcfg['DataSourceUCI']
    if pucchformat0_tvcfg['DataSourceSR'] == 0:
        pucch_format0_config['SR'] = 'negative'
    else:
        pucch_format0_config['SR'] = 'positive'
    
    pucch_format0_config['Periodicity_in_slot'] = 1
    pucch_format0_config['slotoffset'] = 0
    

    return carrier_config, pucch_format0_config