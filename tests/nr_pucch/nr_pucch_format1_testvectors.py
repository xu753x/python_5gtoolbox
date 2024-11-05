# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pucch_format1_testvec_matfile(matfile):
    pucchformat1_tvcfg = {}
    pucchformat1_tvcfg['scs'] = matfile["scs"][0][0]
    pucchformat1_tvcfg['BW'] = matfile["BW"][0][0]
    pucchformat1_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pucchformat1_tvcfg['PRBSet'] = matfile["PRBSet"][0][0]
    pucchformat1_tvcfg['SecondHopStartPRB'] = matfile["SecondHopStartPRB"][0][0]
    pucchformat1_tvcfg['FrequencyHopping'] = matfile["FrequencyHopping"][0]
    pucchformat1_tvcfg['GroupHopping'] = matfile["GroupHopping"][0]
    pucchformat1_tvcfg['HoppingID'] = matfile["HoppingID"][0][0]
    pucchformat1_tvcfg['InitialCyclicShift'] = matfile["InitialCyclicShift"][0][0]
    pucchformat1_tvcfg['NumUCIBits'] = matfile["NumUCIBits"][0][0]
    pucchformat1_tvcfg['DataSourceUCI'] = matfile["DataSourceUCI"][0]
    pucchformat1_tvcfg['OCCI'] = matfile["OCCI"][0][0]
    
    codeword_out = matfile["codeword_out"]
    symbols_out = matfile["symbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return codeword_out, symbols_out, fd_slot_data, pucchformat1_tvcfg

def gen_pucchformat1_testvec_config(pucchformat1_tvcfg):
    """ genrate UL carrier config and pucch format1 config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pucch_format1_config.json", 'r') as f:
        pucch_format1_config = json.load(f)
    
    carrier_config['BW'] = pucchformat1_tvcfg['BW']
    carrier_config['scs'] = pucchformat1_tvcfg['scs']
    carrier_config['num_of_ant'] = 1

    pucch_format1_config['startingPRB'] = pucchformat1_tvcfg['PRBSet']
    if pucchformat1_tvcfg['FrequencyHopping'] == 'intraSlot':
        pucch_format1_config['intraSlotFrequencyHopping'] = 'enabled'
    else:
        pucch_format1_config['intraSlotFrequencyHopping'] = 'disabled'
        
    pucch_format1_config['secondHopPRB'] = pucchformat1_tvcfg['SecondHopStartPRB']
    pucch_format1_config['initialCyclicShift'] = pucchformat1_tvcfg['InitialCyclicShift']
    pucch_format1_config['nrofSymbols'] = pucchformat1_tvcfg['SymbolAllocation'][1]
    pucch_format1_config['startingSymbolIndex'] = pucchformat1_tvcfg['SymbolAllocation'][0]
    pucch_format1_config['pucch_GroupHopping'] = pucchformat1_tvcfg['GroupHopping']
    pucch_format1_config['hoppingId'] = pucchformat1_tvcfg['HoppingID']
    pucch_format1_config['numHARQbits'] = pucchformat1_tvcfg['NumUCIBits']
    pucch_format1_config['HARQbits'] = pucchformat1_tvcfg['DataSourceUCI']
    pucch_format1_config['timeDomainOCC'] = pucchformat1_tvcfg['OCCI']

    pucch_format1_config['Periodicity_in_slot'] = 1
    pucch_format1_config['slotoffset'] = 0
    

    return carrier_config, pucch_format1_config