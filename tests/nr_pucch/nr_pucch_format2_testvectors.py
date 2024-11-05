# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pucch_format2_testvec_matfile(matfile):
    pucchformat2_tvcfg = {}
    pucchformat2_tvcfg['scs'] = matfile["scs"][0][0]
    pucchformat2_tvcfg['BW'] = matfile["BW"][0][0]
    pucchformat2_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pucchformat2_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    pucchformat2_tvcfg['SecondHopStartPRB'] = matfile["SecondHopStartPRB"][0][0]
    pucchformat2_tvcfg['FrequencyHopping'] = matfile["FrequencyHopping"][0]
    pucchformat2_tvcfg['NID'] = matfile["NID"][0][0]
    pucchformat2_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    pucchformat2_tvcfg['NID0'] = matfile["NID0"][0][0]
    pucchformat2_tvcfg['NumUCIBits'] = matfile["NumUCIBits"][0][0]
    
    codeword_out = matfile["codeword_out"]
    symbols_out = matfile["symbols_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return codeword_out, symbols_out, fd_slot_data, pucchformat2_tvcfg

def gen_pucchformat2_testvec_config(pucchformat2_tvcfg):
    """ genrate UL carrier config and pucch format2 config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pucch_format2_config.json", 'r') as f:
        pucch_format2_config = json.load(f)
    
    carrier_config['BW'] = pucchformat2_tvcfg['BW']
    carrier_config['scs'] = pucchformat2_tvcfg['scs']
    carrier_config['num_of_ant'] = 1

    pucch_format2_config['startingPRB'] = pucchformat2_tvcfg['PRBSet'][0]
    pucch_format2_config['nrofPRBs'] = len(pucchformat2_tvcfg['PRBSet'])
    if pucchformat2_tvcfg['FrequencyHopping'] == 'intraSlot':
        pucch_format2_config['intraSlotFrequencyHopping'] = 'enabled'
    else:
        pucch_format2_config['intraSlotFrequencyHopping'] = 'disabled'
        
    pucch_format2_config['secondHopPRB'] = pucchformat2_tvcfg['SecondHopStartPRB']
    
    pucch_format2_config['nrofSymbols'] = pucchformat2_tvcfg['SymbolAllocation'][1]
    pucch_format2_config['startingSymbolIndex'] = pucchformat2_tvcfg['SymbolAllocation'][0]
    pucch_format2_config['NumUCIBits'] = pucchformat2_tvcfg['NumUCIBits']
    d1 = np.tile(np.array([1,0,1,0]), int((pucch_format2_config['NumUCIBits'] // 4)+4))
    pucch_format2_config['UCIbits'] = d1[0:pucch_format2_config['NumUCIBits']]

    pucch_format2_config['NID'] = pucchformat2_tvcfg['NID']
    pucch_format2_config['RNTI'] = pucchformat2_tvcfg['RNTI']
    pucch_format2_config['NID0'] = pucchformat2_tvcfg['NID0']

    pucch_format2_config['Periodicity_in_slot'] = 1
    pucch_format2_config['slotoffset'] = 0
    

    return carrier_config, pucch_format2_config