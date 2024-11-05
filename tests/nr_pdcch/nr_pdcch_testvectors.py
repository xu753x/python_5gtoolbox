# -*- coding:utf-8 -*-

import numpy as np
import json

def read_pdcch_testvec_matfile(matfile):
    pdcch_tvcfg = {}
    pdcch_tvcfg['scs'] = matfile["scs"][0][0]
    pdcch_tvcfg['BW'] = matfile["BW"][0][0]
    pdcch_tvcfg['FrequencyResources'] = matfile["FrequencyResources"][0]
    pdcch_tvcfg['coresetDuration'] = matfile["coresetDuration"][0][0]
    pdcch_tvcfg['CCEREGMapping'] = matfile["CCEREGMapping"][0]
    pdcch_tvcfg['REGBundleSize'] = matfile["REGBundleSize"][0][0]
    pdcch_tvcfg['InterleaverSize'] = matfile["InterleaverSize"][0][0]
    pdcch_tvcfg['ShiftIndex'] = matfile["ShiftIndex"][0][0]
    pdcch_tvcfg['PrecoderGranularity'] = matfile["PrecoderGranularity"][0]
    pdcch_tvcfg['StartSymbolWithinSlot'] = matfile["StartSymbolWithinSlot"][0][0]
    pdcch_tvcfg['SlotPeriodAndOffset'] = matfile["SlotPeriodAndOffset"][0]
    pdcch_tvcfg['spDuration'] = matfile["spDuration"][0][0]
    pdcch_tvcfg['NumCandidates'] = matfile["NumCandidates"][0]
    pdcch_tvcfg['AggregationLevel'] = matfile["AggregationLevel"][0][0]
    pdcch_tvcfg['AllocatedCandidate'] = matfile["AllocatedCandidate"][0][0]
    pdcch_tvcfg['DataBlockSize'] = matfile["DataBlockSize"][0][0]
    pdcch_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    pdcch_tvcfg['DMRSScramblingID'] = matfile["DMRSScramblingID"][0][0]
    
    dcibits_out = matfile["dcibits_out"]
    RM_out = matfile["RM_out"]
    mod_out = matfile["mod_out"]
    dmrssym_out = matfile["dmrssym_out"]
    fd_slot_data = matfile["fd_slot_data"]
    return dcibits_out,RM_out, mod_out, dmrssym_out, fd_slot_data, pdcch_tvcfg

def gen_pdcch_testvec_config(pdcch_tvcfg):
    """ genrate UL carrier config, coreset, search_space and pdcch config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pdcch_config.json", 'r') as f:
        pdcch_config = json.load(f)
    with open(path + "default_search_space.json", 'r') as f:
        search_space_config = json.load(f)
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)
    
    carrier_config['BW'] = pdcch_tvcfg['BW']
    carrier_config['scs'] = pdcch_tvcfg['scs']
    carrier_config['num_of_ant'] = 1   
    carrier_config['PCI'] = 1 #fixed value

    coreset_config['coreset_id'] = 1
    coreset_config['frequencyDomainResources'] = pdcch_tvcfg['FrequencyResources']
    coreset_config['symduration'] = pdcch_tvcfg['coresetDuration']
    coreset_config['CCE_REG_mapping_type'] = pdcch_tvcfg['CCEREGMapping']
    coreset_config['REG_bundle_size'] = pdcch_tvcfg['REGBundleSize']
    coreset_config['interleaver_size'] = pdcch_tvcfg['InterleaverSize']
    coreset_config['shift_index'] = pdcch_tvcfg['ShiftIndex']
    coreset_config['precoder_granularity'] = pdcch_tvcfg['PrecoderGranularity']
    coreset_config['PDCCH_DMRS_Scrambling_ID'] = pdcch_tvcfg['DMRSScramblingID']
    coreset_config['CORESET_startingPRB'] = 0

    search_space_config['searchSpaceId'] = 1
    search_space_config['controlResourceSetId'] = 1
    search_space_config['monitoringSlotPeriodicityAndOffset'] = pdcch_tvcfg['SlotPeriodAndOffset']
    search_space_config['slotduration'] = pdcch_tvcfg['spDuration']
    search_space_config['FirstSymbolWithinSlot'] = pdcch_tvcfg['StartSymbolWithinSlot']
    search_space_config['NrofCandidatesPerAggregationLevel'] = pdcch_tvcfg['NumCandidates']
    search_space_config['searchSpaceType'] = 'ue'

    pdcch_config['rnti'] = pdcch_tvcfg['RNTI']
    pdcch_config['searchSpaceId'] = 1
    pdcch_config['AggregationLevel'] = pdcch_tvcfg['AggregationLevel']
    #matlab generated AllocatedCandidate start from 1
    pdcch_config['AllocatedCandidate'] = pdcch_tvcfg['AllocatedCandidate'] - 1
    pdcch_config['NumDCIBits'] = pdcch_tvcfg['DataBlockSize']
    
    return carrier_config, coreset_config, search_space_config, pdcch_config