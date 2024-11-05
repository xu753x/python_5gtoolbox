# -*- coding:utf-8 -*-

import numpy as np
import json

def read_nrPDSCH_mixed_testvec_matfile(matfile):
    """read nrPDSCH_mixed_testvec_** testvectors
    """
    DL_tvcfg = {}
    DL_tvcfg['SampleRate'] = matfile["SampleRate"][0][0]
    DL_tvcfg['Modulation'] = matfile["Modulation"][0]
    DL_tvcfg['NumLayers'] = matfile["NumLayers"][0][0]
    DL_tvcfg['MappingType'] = matfile["MappingType"][0]
    DL_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    DL_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    DL_tvcfg['NID'] = matfile["NID"][0][0]
    DL_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    DL_tvcfg['TargetCodeRate'] = matfile["TargetCodeRate"][0][0]
    DL_tvcfg['RVSequence'] = matfile["RVSequence"][0]
    DL_tvcfg['DataSource'] = matfile["DataSource"][0]
    DL_tvcfg['DMRSConfigurationType'] = matfile["DMRSConfigurationType"][0][0]
    DL_tvcfg['DMRSTypeAPosition'] = matfile["DMRSTypeAPosition"][0][0]
    DL_tvcfg['DMRSAdditionalPosition'] = matfile["DMRSAdditionalPosition"][0][0]
    DL_tvcfg['DMRSLength'] = matfile["DMRSLength"][0][0]
    DL_tvcfg['NSCID'] = matfile["NSCID"][0][0]
    DL_tvcfg['NumCDMGroupsWithoutData'] = matfile["NumCDMGroupsWithoutData"][0][0]
    DL_tvcfg['G_out'] = matfile["G_out"][0]
    DL_tvcfg['rv_out'] = matfile["rv_out"][0]
    DL_tvcfg['Qm'] = matfile["Qm"][0][0]
    DL_tvcfg['TargetCodeRateby1024'] = matfile["TargetCodeRateby1024"][0][0]
    DL_tvcfg['mcstableidx'] = matfile["mcstableidx"][0][0]
    DL_tvcfg['imcs'] = matfile["imcs"][0][0]
    DL_tvcfg['scs'] = matfile["scs"][0][0]
    DL_tvcfg['BW'] = matfile["BW"][0][0]
    DL_tvcfg['csirs_NumRB'] = matfile["csirs_NumRB"][0][0]
    DL_tvcfg['coreset_FrequencyResources'] = matfile["coreset_FrequencyResources"][0]
    
    trblk_out = matfile["trblk_out"][0]
    RM_out = matfile["RM_out"]
    layermap_out = matfile['layermap_out']
    fd_slot_data = matfile['fd_slot_data']
    waveform = matfile['waveform']
       
    return trblk_out,RM_out,layermap_out, fd_slot_data, waveform, DL_tvcfg

def gen_DL_waveform_testvec_config(DL_tvcfg):
    """ genrate UL carrier config, coreset, search_space and pdcch config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    with open(path + "default_csirs_config.json", 'r') as f:
        csirs_config = json.load(f)
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)
    with open(path + "default_pdcch_config.json", 'r') as f:
        pdcch_config = json.load(f)
    with open(path + "default_search_space.json", 'r') as f:
        search_space_config = json.load(f)
    
    waveform_config['numofsubframes'] = 20
    waveform_config['samplerate_in_mhz'] = DL_tvcfg['SampleRate']/(1e6)
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    carrier_config['BW'] = DL_tvcfg['BW']
    carrier_config['scs'] = DL_tvcfg['scs']
    carrier_config['num_of_ant'] = DL_tvcfg['NumLayers']
    carrier_config['maxMIMO_layers'] = DL_tvcfg['NumLayers']   
    carrier_config['PCI'] = 1 #fixed value
    carrier_config['carrier_frequency_in_mhz'] = 0 #fixed value

    pdsch_config['rnti'] = DL_tvcfg['RNTI']
    if DL_tvcfg['mcstableidx'] == 1:
        pdsch_config['mcs_table'] = '64QAM'
    else:
        pdsch_config['mcs_table'] = '256QAM'
    pdsch_config['mcs_index'] = DL_tvcfg['imcs']
    pdsch_config['rv'] = DL_tvcfg['rv_out']
    pdsch_config['data_source'] = [1,0,0,1]
    pdsch_config['NID'] = DL_tvcfg['NID']
    pdsch_config['num_of_layers'] = DL_tvcfg['NumLayers']
    pdsch_config['nID'] = DL_tvcfg['RNTI']
    pdsch_config['DMRS']['nSCID'] = DL_tvcfg['NSCID']
    pdsch_config['DMRS']['nNIDnSCID'] = 1
    pdsch_config['DMRS']['DMRSConfigType'] = DL_tvcfg['DMRSConfigurationType']
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = DL_tvcfg['NumCDMGroupsWithoutData']
    pdsch_config['DMRS']['DMRSAddPos'] = DL_tvcfg['DMRSAdditionalPosition']

    pdsch_config['StartSymbolIndex'] = DL_tvcfg['SymbolAllocation'][0]
    pdsch_config['NrOfSymbols'] = DL_tvcfg['SymbolAllocation'][1]
    pdsch_config['ResAlloType1']['RBStart'] = DL_tvcfg['PRBSet'][0]
    pdsch_config['ResAlloType1']['RBSize'] = len(DL_tvcfg['PRBSet'])

    scs = DL_tvcfg['scs']
    if scs == 15:
        ssb_config['SSBPattern'] = "Case A"
        ssb_config["MIB"]['subCarrierSpacingCommon'] = 0
    else:
        ssb_config['SSBPattern'] = "Case B"
        ssb_config["MIB"]['subCarrierSpacingCommon'] = 1
    ssb_config["MIB"]['dmrs_TypeA_Position'] = 0
    ssb_config['ssb_PositionsInBurst'] =  [1,1,0,0]
    ssb_config['SSBperiod']  = 20
    ssb_config['kSSB']  = 0
    ssb_config['NSSB_CRB']  = 0

    csirs_config['nrofPorts'] = 1 #rownumber = 2
    csirs_config['cdm_type'] = 'noCDM'
    csirs_config['frequencyDomainAllocation']['row'] = 2

    SubcarrierLocations = 0
    fi = SubcarrierLocations #for row = 2
    csirs_config['frequencyDomainAllocation']['bitstring'] = \
        '0'*(11 - fi) + '1' + '0'*fi
    csirs_config['density'] = 'one'
    csirs_config['firstOFDMSymbolInTimeDomain'] = 10
    csirs_config['nrofRBs'] = DL_tvcfg['csirs_NumRB'].astype('int32')
    csirs_config['startingRB'] = 0
    csirs_config['scramblingID'] = 0
    csirs_config['periodicity'] = 10
    csirs_config['slotoffset'] = 3

    coreset_config['coreset_id'] = 1
    coreset_config['frequencyDomainResources'] = DL_tvcfg['coreset_FrequencyResources']
    coreset_config['symduration'] = 2
    coreset_config['CCE_REG_mapping_type'] = 'noninterleaved'
    coreset_config['REG_bundle_size'] = 6
    coreset_config['shift_index'] = 0
    coreset_config['interleaver_size'] = 2
    coreset_config['precoder_granularity'] = 'sameAsREG-bundle'
    coreset_config['PDCCH_DMRS_Scrambling_ID'] = 2
    coreset_config['CORESET_startingPRB'] = 0

    search_space_config['searchSpaceId'] = 1
    search_space_config['controlResourceSetId'] = 1
    search_space_config['monitoringSlotPeriodicityAndOffset'] = [10,2]
    search_space_config['slotduration'] = 1
    search_space_config['FirstSymbolWithinSlot'] = 0
    search_space_config['NrofCandidatesPerAggregationLevel'] = [1,1,0,0,0]
    search_space_config['searchSpaceType'] = 'ue'

    pdcch_config['rnti'] = 1
    pdcch_config['searchSpaceId'] = 1
    pdcch_config['AggregationLevel'] = 1
    pdcch_config['AllocatedCandidate'] = 0
    pdcch_config['NumDCIBits'] = 20
    pdcch_config['data_source'] = [1,1,0,0]
    pdcch_config['period_in_slot'] = 10
    pdcch_config['allocated_slots'] = [2]
    
    return waveform_config, carrier_config, ssb_config, pdsch_config, csirs_config, coreset_config, search_space_config, pdcch_config