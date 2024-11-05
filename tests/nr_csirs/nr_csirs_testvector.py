# -*- coding:utf-8 -*-

import numpy as np
import json

def read_nrCSIRS_testvec_matfile(matfile):
    csirstv_cfg = {}
    csirstv_cfg['scs'] = matfile["scs"][0][0]
    csirstv_cfg['BW'] = matfile["BW"][0][0]
    csirstv_cfg['RowNumber'] = matfile["RowNumber"][0][0]
    csirstv_cfg['Density'] = matfile["Density"][0]
    csirstv_cfg['SymbolLocations'] = matfile["SymbolLocations"][0][0]
    csirstv_cfg['SubcarrierLocations'] = matfile["SubcarrierLocations"][0][0]
    csirstv_cfg['NumRB'] = matfile["NumRB"][0][0]
    csirstv_cfg['RBOffset'] = matfile["RBOffset"][0][0]
    csirstv_cfg['NID'] = matfile["NID"][0][0]
    
    csirsSym_out = matfile["csirsSym_out"]
    csirsLinInd_out = matfile["csirsLinInd_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return csirsSym_out, csirsLinInd_out, fd_slot_data, csirstv_cfg

def gen_nrCSIRS_testvec_config(csirstv_cfg):
    """ genrate UL carrier config and srs config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_csirs_config.json", 'r') as f:
        csirs_config = json.load(f)
    
    carrier_config['BW'] = csirstv_cfg['BW'].astype('int32')
    carrier_config['scs'] = csirstv_cfg['scs'].astype('int32')

    row = csirstv_cfg['RowNumber']
    if row in [1,2]:
        carrier_config['num_of_ant'] = 1
        csirs_config['nrofPorts'] = 1
        csirs_config['cdm_type'] = 'noCDM'
    elif row == 3:
        carrier_config['num_of_ant'] = 2
        csirs_config['nrofPorts'] = 2
        csirs_config['cdm_type'] = 'fd-CDM2'
    else:
        carrier_config['num_of_ant'] = 4
        csirs_config['nrofPorts'] = 4
        csirs_config['cdm_type'] = 'fd-CDM2'

    csirs_config['frequencyDomainAllocation']['row'] = csirstv_cfg['RowNumber']
    
    SubcarrierLocations = csirstv_cfg['SubcarrierLocations']
    if row in [1,2]:
        fi = SubcarrierLocations
    elif row == 4:
        fi = int(SubcarrierLocations / 4)
    else:
        fi = int(SubcarrierLocations / 2)

    csirs_config['frequencyDomainAllocation']['bitstring'] = \
        '0'*(11 - fi) + '1' + '0'*fi
    
    if csirstv_cfg['Density'] == 'dot5even':
        csirs_config['density'] = 'dot5evenPRBs'
    elif csirstv_cfg['Density'] == 'dot5odd':
        csirs_config['density'] = 'dot5oddPRBs'
    else:
        csirs_config['density'] = csirstv_cfg['Density']
        
    csirs_config['firstOFDMSymbolInTimeDomain'] = csirstv_cfg['SymbolLocations'].astype('int32')

    
    csirs_config['nrofRBs'] = csirstv_cfg['NumRB'].astype('int32')
    csirs_config['startingRB'] = csirstv_cfg['RBOffset'].astype('int32')
    csirs_config['scramblingID'] = csirstv_cfg['NID']
    csirs_config['periodicity'] = 10
    csirs_config['slotoffset'] = 0
    

    return carrier_config, csirs_config