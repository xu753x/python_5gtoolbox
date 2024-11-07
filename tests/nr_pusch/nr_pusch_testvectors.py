# -*- coding:utf-8 -*-

import numpy as np
import json

def read_ulsch_testvec_matfile(matfile):
    """ read PUSCH test vector matfile
    trblk_out, RM_out, layermap_out, fd_slot_data, waveform, pusch_tvcfg =
        read_matfile(matfile)
    output:
        trblk_out: Trblk input bits
        RM_out: bit seq after CRC, LDPC, rate matching
        layermap_out: output after scrambling, modulation, layer mapping
        fd_slot_data: frequency domain IQ data on all slots
        waveform: timedomain IQ data on all slots
        pusch_tvcfg: PUSCH test vector parameters
    """
    pusch_tvcfg = {}
        
    pusch_tvcfg['rv_out'] = matfile["rv_out"][0]
    pusch_tvcfg['mcstableidx'] = matfile["mcstableidx"][0][0]
    pusch_tvcfg['imcs'] = matfile["imcs"][0][0]
    pusch_tvcfg['scs'] = matfile["scs"][0][0]
    pusch_tvcfg['BW'] = matfile["BW"][0][0]
    pusch_tvcfg['NumLayers'] = matfile["NumLayers"][0][0]
    pusch_tvcfg['SymbolAllocation'] = matfile["SymbolAllocation"][0]
    pusch_tvcfg['TransmissionScheme'] = matfile["TransmissionScheme"][0]
    pusch_tvcfg['NumAntennaPorts'] = matfile["NumAntennaPorts"][0][0]
    pusch_tvcfg['TPMI'] = matfile["TPMI"][0][0]

    pusch_tvcfg['EnableACK'] = matfile["EnableACK"][0][0]
    pusch_tvcfg['NumACKBits'] = matfile["NumACKBits"][0][0]
    pusch_tvcfg['BetaOffsetACK'] = matfile["BetaOffsetACK"][0][0]
    pusch_tvcfg['EnableCSI1'] = matfile["EnableCSI1"][0][0]
    pusch_tvcfg['NumCSI1Bits'] = matfile["NumCSI1Bits"][0][0]
    pusch_tvcfg['BetaOffsetCSI1'] = matfile["BetaOffsetCSI1"][0][0]
    pusch_tvcfg['EnableCSI2'] = matfile["EnableCSI2"][0][0]
    pusch_tvcfg['NumCSI2Bits'] = matfile["NumCSI2Bits"][0][0]
    pusch_tvcfg['BetaOffsetCSI2'] = matfile["BetaOffsetCSI2"][0][0]
    
    pusch_tvcfg['DMRSAdditionalPosition'] = matfile["DMRSAdditionalPosition"][0][0]
    pusch_tvcfg['NumCDMGroupsWithoutData'] = matfile["NumCDMGroupsWithoutData"][0][0]
    pusch_tvcfg['Qm'] = matfile["Qm"][0][0]
    pusch_tvcfg['TargetCodeRateby1024'] = matfile["TargetCodeRateby1024"][0][0]
    pusch_tvcfg['PRBSet'] = matfile["PRBSet"][0]
    pusch_tvcfg['TransformPrecoding'] = matfile["TransformPrecoding"][0][0]
    
    pusch_tvcfg['GroupHopping'] = matfile["GroupHopping"][0][0]  
    pusch_tvcfg['SequenceHopping'] = matfile["SequenceHopping"][0][0]  
    if 'SampleRate' in matfile:
        pusch_tvcfg['SampleRate'] = matfile["SampleRate"][0][0]  
    else:
        pusch_tvcfg['SampleRate'] = 0
    
    effACK_out = matfile["effACK_out"]
    csi1_out = matfile["csi1_out"]
    csi2_out = matfile["csi2_out"]
    trblk_out = matfile["trblk_out"][0]
    GACK_out = matfile["GACK_out"][0]
    GCSI1_out = matfile["GCSI1_out"][0]
    GCSI2_out = matfile["GCSI2_out"][0]
    GULSCH_out = matfile["GULSCH_out"][0]
    codedULSCH_out = matfile["codedULSCH_out"]
    codedACK_out = matfile["codedACK_out"]
    codedCSI1_out = matfile["codedCSI1_out"]
    codedCSI2_out = matfile["codedCSI2_out"]
    codeword_out = matfile["codeword_out"]
    
    if 'UCIScaling' in matfile:
        pusch_tvcfg['UCIScaling'] = matfile["UCIScaling"][0][0]
    else:
        pusch_tvcfg['UCIScaling'] = 1
    
    if 'EnableULSCH' in matfile:
        pusch_tvcfg['EnableULSCH'] = matfile["EnableULSCH"][0][0]
    else:
        pusch_tvcfg['EnableULSCH'] = 1

    if 'layermap_out' in matfile:
        layermap_out = matfile["layermap_out"]
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
        

    return effACK_out, csi1_out, csi2_out, trblk_out, \
          GACK_out, GCSI1_out, GCSI2_out, GULSCH_out, \
          codedULSCH_out, codedACK_out, codedCSI1_out, codedCSI2_out, codeword_out, \
              layermap_out, fd_slot_data, waveform, pusch_tvcfg

def gen_pusch_testvec_config(pusch_tvcfg):
    """ genrate UL carrier config, coreset, search_space and pusch config"""
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pusch_config.json", 'r') as f:
        pusch_config = json.load(f)
    
    carrier_config['BW'] = pusch_tvcfg['BW']
    carrier_config['scs'] = pusch_tvcfg['scs']
    carrier_config['num_of_ant'] = pusch_tvcfg['NumAntennaPorts']
    carrier_config['maxMIMO_layers'] = pusch_tvcfg['NumLayers']   
    carrier_config['PCI'] = 1 #fixed value

    pusch_config['rnti'] = 1
    if pusch_tvcfg['mcstableidx'] == 2:
        pusch_config['mcs_table'] = '256QAM'
        pusch_config['mcs_index'] = pusch_tvcfg['imcs'] 
        pusch_config['nTpPi2BPSK'] = 0
    elif pusch_tvcfg['mcstableidx'] == 3:
        pusch_config['mcs_table'] = '64QAMLowSE'
        pusch_config['mcs_index'] = pusch_tvcfg['imcs'] 
        pusch_config['nTpPi2BPSK'] = 0
    elif pusch_tvcfg['mcstableidx'] == 4:
        pusch_config['mcs_table'] = 'MCStable61411'
        if pusch_tvcfg['imcs'] > 27:
            pusch_config['mcs_index'] = pusch_tvcfg['imcs'] - 28
            pusch_config['nTpPi2BPSK'] = 0
        else:
            pusch_config['mcs_index'] = pusch_tvcfg['imcs'] 
            pusch_config['nTpPi2BPSK'] = 1
    elif pusch_tvcfg['mcstableidx'] == 5:
        pusch_config['mcs_table'] = 'MCStable61412'
        if pusch_tvcfg['imcs'] > 27:
            pusch_config['mcs_index'] = pusch_tvcfg['imcs'] - 28
            pusch_config['nTpPi2BPSK'] = 0
        else:
            pusch_config['mcs_index'] = pusch_tvcfg['imcs'] 
            pusch_config['nTpPi2BPSK'] = 1
    else:
        assert 0
    
    pusch_config['nTransPrecode'] = pusch_tvcfg['TransformPrecoding']
    if pusch_tvcfg['TransmissionScheme'] == 'nonCodebook':
        pusch_config['nTransmissionScheme'] = 0
    else:
        pusch_config['nTransmissionScheme'] = 1
    pusch_config['num_of_layers'] = pusch_tvcfg['NumLayers']
    pusch_config['nNrOfAntennaPorts'] = pusch_tvcfg['NumAntennaPorts']
    
    pusch_config['DMRS']['dmrs_TypeA_Position'] = "pos2"
    pusch_config['DMRS']['nSCID'] = 0
    pusch_config['DMRS']['DMRSConfigType'] = 1
    pusch_config['DMRS']['NrOfDMRSSymbols'] = 1
    pusch_config['DMRS']['NumCDMGroupsWithoutData'] = pusch_tvcfg['NumCDMGroupsWithoutData']
    pusch_config['DMRS']['DMRSAddPos'] = pusch_tvcfg['DMRSAdditionalPosition']
    pusch_config['DMRS']['PUSCHMappintType'] = 'A'
    pusch_config['DMRS']['transformPrecodingDisabled']['NID0'] = 10
    pusch_config['DMRS']['transformPrecodingDisabled']['NID1'] = 20
    pusch_config['DMRS']['transformPrecodingEnabled']["nPuschID"] = 30
    if pusch_tvcfg['GroupHopping'] == 1:
        pusch_config['DMRS']['transformPrecodingEnabled']["groupOrSequenceHopping"] = "groupHopping"
    elif pusch_tvcfg['SequenceHopping'] == 1:
        pusch_config['DMRS']['transformPrecodingEnabled']["groupOrSequenceHopping"] = "sequenceHopping"
    else:
        pusch_config['DMRS']['transformPrecodingEnabled']["groupOrSequenceHopping"] = "neither"

    pusch_config['VRBtoPRBMapping'] = "non-interleaved"

    pusch_config['nPMI'] = pusch_tvcfg['TPMI']
    pusch_config['StartSymbolIndex'] = pusch_tvcfg['SymbolAllocation'][0]
    pusch_config['NrOfSymbols'] = pusch_tvcfg['SymbolAllocation'][1]

    pusch_config['ResAlloType1']['RBStart'] = pusch_tvcfg['PRBSet'][0]
    pusch_config['ResAlloType1']['RBSize'] = len(pusch_tvcfg['PRBSet'])

    pusch_config['rv'] = pusch_tvcfg['rv_out']
    pusch_config['nNid'] = 1
    pusch_config['UCIScaling'] = pusch_tvcfg['UCIScaling']
    pusch_config['EnableULSCH'] = pusch_tvcfg['EnableULSCH']
    
    pusch_config['EnableACK'] = pusch_tvcfg['EnableACK']
    if pusch_config['EnableACK'] == 1:
        pusch_config['NumACKBits'] = pusch_tvcfg['NumACKBits']
    else:
        pusch_config['NumACKBits'] = 0
    #find ACK index
    """ 38.213 Table 9.3-1: Mapping of beta_offset values for HARQ-ACK information and the index signalled by
        higher layers
    """
    acktable = [1.000,2.000,2.500,3.125,4.000,5.000,6.250,8.000,10.000,12.625, 15.875, 20.000, 31.000, 50.000, 80.000, 126.000]
    assert pusch_tvcfg['BetaOffsetACK'] in acktable
    pusch_config['I_HARQ_ACK_offset'] = acktable.index(pusch_tvcfg['BetaOffsetACK'])

    """ 38.213 Table 9.3-1: Mapping of beta_offset values for HARQ-ACK information and the index signalled by
        higher layers
    """
    csitable = [1.125,1.250,1.375,1.625,1.750,2.000,2.250,2.500,2.875,3.125,
            3.500, 4.000, 5.000, 6.250, 8.000, 10.000, 12.625, 15.875, 20.000]
    pusch_config['EnableCSI1'] = pusch_tvcfg['EnableCSI1']
    if pusch_config['EnableCSI1']:
        pusch_config['NumCSI1Bits'] = pusch_tvcfg['NumCSI1Bits']
    else:
        pusch_config['NumCSI1Bits'] = 0

    pusch_config['I_CSI1offset'] = csitable.index(pusch_tvcfg['BetaOffsetCSI1'])

    pusch_config['EnableCSI2'] = pusch_tvcfg['EnableCSI2']
    if pusch_config['EnableCSI2']:
        pusch_config['NumCSI2Bits'] = pusch_tvcfg['NumCSI2Bits']
    else:
        pusch_config['NumCSI2Bits'] = 0
        
    pusch_config['I_CSI2offset'] = csitable.index(pusch_tvcfg['BetaOffsetCSI2'])

    return carrier_config, pusch_config