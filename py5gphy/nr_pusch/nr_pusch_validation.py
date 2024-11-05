# -*- coding:utf-8 -*-

from py5gphy.common import nr_slot

def pusch_config_validate(carrier_config, pusch_config):
    """ check if pusch configuration validate or not"""

    #read input
    BW = carrier_config['BW']
    scs = carrier_config['scs']
    num_of_ant = carrier_config['num_of_ant']

    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)

    rnti = pusch_config['rnti']
    assert rnti in range(1,65536)
    
    mcs_table = pusch_config['mcs_table']
    assert mcs_table in ['256QAM', '64QAMLowSE','MCStable61411', 'MCStable61412']

    mcs_index = pusch_config['mcs_index']
    assert mcs_index < 28
    
    nTransPrecode = pusch_config['nTransPrecode']
    assert nTransPrecode in [0,1]

    nTransmissionScheme = pusch_config['nTransmissionScheme']
    assert nTransmissionScheme == 1 #support codebook-based transmission only

    num_of_layers = pusch_config['num_of_layers']
    assert num_of_layers in [1,2] #most 5G gNB and cell phone aupport at most 2 layers 
    assert num_of_layers <= num_of_ant

    nNrOfAntennaPorts = pusch_config['nNrOfAntennaPorts']
    assert nNrOfAntennaPorts in [1,2] #most 5G gNB and cell phone aupport at most 2 layers 

    nSCID = pusch_config['DMRS']['nSCID']
    assert nSCID in [0,1]

    DMRSConfigType = pusch_config['DMRS']['DMRSConfigType']
    assert DMRSConfigType in [1, 2]

    NrOfDMRSSymbols = pusch_config['DMRS']['NrOfDMRSSymbols']
    assert NrOfDMRSSymbols in [1, 2]

    NumCDMGroupsWithoutData = pusch_config['DMRS']['NumCDMGroupsWithoutData']
    assert NumCDMGroupsWithoutData in [1, 2, 3]

    DMRSAddPos = pusch_config['DMRS']['DMRSAddPos']
    assert DMRSAddPos in [0, 1, 2, 3]

    PUSCHMappintType = pusch_config['DMRS']['PUSCHMappintType']
    assert PUSCHMappintType in ['A', 'B']

    VRBtoPRBMapping = pusch_config['VRBtoPRBMapping']
    assert VRBtoPRBMapping in ['non-interleaved', 'interleaved']

    RBBundleSize = pusch_config['RBBundleSize']

    nPMI = pusch_config['nPMI']
    assert nPMI in range(28)

    StartSymbolIndex = pusch_config['StartSymbolIndex']
    NrOfSymbols = pusch_config['NrOfSymbols']
    assert StartSymbolIndex + NrOfSymbols <=14

    ResourceAllocType = pusch_config['ResourceAllocType']
    assert ResourceAllocType == 1 #only support type 1

    RBStart = pusch_config['ResAlloType1']['RBStart']
    RBSize = pusch_config['ResAlloType1']['RBSize']
    assert RBStart + RBSize <= carrier_prbsize

    rv = pusch_config['rv']
    assert any(rv) < 4

    nHARQID = pusch_config['nHARQID']
    assert nHARQID in range(16)

    NDI = pusch_config['NDI']
    assert NDI in [0, 1]

    nNid = pusch_config['nNid']
    assert nNid in range(1024)

    UCIScaling = pusch_config['UCIScaling']
    assert UCIScaling in [0.5, 0.65, 0.8, 1] #38.331 pusch-config

    I_HARQ_ACK_offset = pusch_config['I_HARQ_ACK_offset']
    assert I_HARQ_ACK_offset in range(16)

    nTpPi2BPSK = pusch_config['nTpPi2BPSK']
    assert nTpPi2BPSK in [0, 1]
    
