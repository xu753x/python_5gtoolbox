# -*- coding:utf-8 -*-

import numpy as np
import json

def read_dlsch_testvec_matfile(matfile):
    """ read PDSCH test vector matfile
    trblk_out, RM_out, layermap_out, fd_slot_data, waveform, pdsch_tvcfg =
        read_matfile(matfile)
    output:
        trblk_out: Trblk input bits
        RM_out: bit seq after CRC, LDPC, rate matching
        layermap_out: output after scrambling, modulation, layer mapping
        fd_slot_data: frequency domain IQ data on all slots
        waveform: timedomain IQ data on all slots
        pdsch_tvcfg: PDSCH test vector parameters
    """
    pdsch_tvcfg = {}
    pdsch_tvcfg['SampleRate'] = matfile["SampleRate"][0]
    pdsch_tvcfg['Modulation'] = matfile["Modulation"][0]
    pdsch_tvcfg['NumLayers'] = matfile["NumLayers"][0][0]
    pdsch_tvcfg['MappingType'] = matfile["MappingType"][0]
    pdsch_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pdsch_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    pdsch_tvcfg['NID'] = matfile["NID"][0][0]
    pdsch_tvcfg['RNTI'] = matfile["RNTI"][0][0]
    pdsch_tvcfg['TargetCodeRate'] = matfile["TargetCodeRate"][0][0]
    pdsch_tvcfg['RVSequence'] = matfile["RVSequence"][0][0]
    pdsch_tvcfg['DataSource'] = matfile["DataSource"][0]
    pdsch_tvcfg['DMRSConfigurationType'] = matfile["DMRSConfigurationType"][0][0]
    pdsch_tvcfg['DMRSTypeAPosition'] = matfile["DMRSTypeAPosition"][0][0]
    pdsch_tvcfg['DMRSAdditionalPosition'] = matfile["DMRSAdditionalPosition"][0][0]
    pdsch_tvcfg['DMRSLength'] = matfile["DMRSLength"][0][0]
    pdsch_tvcfg['NSCID'] = matfile["NSCID"][0][0]
    pdsch_tvcfg['NumCDMGroupsWithoutData'] = matfile["NumCDMGroupsWithoutData"][0][0]
    pdsch_tvcfg['G_out'] = matfile["G_out"][0]
    pdsch_tvcfg['rv_out'] = matfile["rv_out"][0]
    pdsch_tvcfg['Qm'] = matfile["Qm"][0][0]
    pdsch_tvcfg['TargetCodeRateby1024'] = matfile["TargetCodeRateby1024"][0][0]
    pdsch_tvcfg['mcstableidx'] = matfile["mcstableidx"][0][0]
    pdsch_tvcfg['imcs'] = matfile["imcs"][0][0]
    pdsch_tvcfg['scs'] = matfile["scs"][0][0]
    pdsch_tvcfg['BW'] = matfile["BW"][0][0]
    
    trblk_out = matfile["trblk_out"][0]
    RM_out = matfile["RM_out"]
    if 'layermap_out' in matfile:
        layermap_out = matfile['layermap_out']
    else:
        layermap_out = []
    
    if 'fd_slot_data' in matfile:
        fd_slot_data = matfile['fd_slot_data']
    else:
        fd_slot_data = []
    
    if 'waveform' in matfile:
        waveform = matfile['waveform']
    else:
        waveform = []
        
    if 'pdschsym_dur' in matfile:
        pdsch_tvcfg['pdschsym_dur'] = matfile['pdschsym_dur'][0][0]
    else:
        pdsch_tvcfg['pdschsym_dur'] = 12

    return trblk_out,RM_out,layermap_out, fd_slot_data, waveform, pdsch_tvcfg

def gen_pdsch_testvec_config(pdsch_tvcfg):
    """ genrate UL carrier config, coreset, search_space and pdcch config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    
    carrier_config['BW'] = pdsch_tvcfg['BW']
    carrier_config['scs'] = pdsch_tvcfg['scs']
    carrier_config['num_of_ant'] = pdsch_tvcfg['NumLayers']
    carrier_config['maxMIMO_layers'] = pdsch_tvcfg['NumLayers']   
    carrier_config['PCI'] = 1 #fixed value

    pdsch_config['rnti'] = pdsch_tvcfg['RNTI']
    if pdsch_tvcfg['mcstableidx'] == 1:
        pdsch_config['mcs_table'] = '64QAM'
    else:
        pdsch_config['mcs_table'] = '256QAM'
    pdsch_config['mcs_index'] = pdsch_tvcfg['imcs']
    pdsch_config['rv'] = pdsch_tvcfg['rv_out']
    pdsch_config['NID'] = pdsch_tvcfg['NID']
    pdsch_config['num_of_layers'] = pdsch_tvcfg['NumLayers']
    pdsch_config['nID'] = pdsch_tvcfg['RNTI']
    pdsch_config['DMRS']['nSCID'] = pdsch_tvcfg['NSCID']
    pdsch_config['DMRS']['nNIDnSCID'] = 1
    pdsch_config['DMRS']['DMRSConfigType'] = pdsch_tvcfg['DMRSConfigurationType']
    pdsch_config['DMRS']['NumCDMGroupsWithoutData'] = pdsch_tvcfg['NumCDMGroupsWithoutData']
    pdsch_config['DMRS']['DMRSAddPos'] = pdsch_tvcfg['DMRSAdditionalPosition']

    pdsch_config['StartSymbolIndex'] = pdsch_tvcfg['SymbolAllocation'][0]
    pdsch_config['NrOfSymbols'] = pdsch_tvcfg['SymbolAllocation'][1]
    pdsch_config['ResAlloType1']['RBStart'] = pdsch_tvcfg['PRBSet'][0]
    pdsch_config['ResAlloType1']['RBSize'] = len(pdsch_tvcfg['PRBSet'])

    return carrier_config, pdsch_config