# -*- coding:utf-8 -*-

import numpy as np
import json

from py5gphy.common import nr_slot
from py5gphy.nr_testmodel import TM1p1_cfg
from py5gphy.nr_testmodel import TM2_cfg
from py5gphy.nr_testmodel import TM2a_cfg
from py5gphy.nr_testmodel import TM3p1_cfg
from py5gphy.nr_testmodel import TM3p1a_cfg

def gen_nr_TM_cfg(scs, BW, Duplex_mode, test_model,cell_id, carrier_frequency_in_mhz):
    """ generate FR1 standard-compliant 5G NR test models (NR-TMs)
        The NR-TMs for FR1 are defined in TS 38.141-1 Section 4.9.2
        support only rel 15 test models
    """
    #validate the input
    assert scs in [15,30]
    if scs == 15:
        assert BW in [5,10,15,20,25,30,35,40,45,50]
    else:
        assert [5,10,15,20,25,30,35,40,45,50,60,70,80,90,100]
    
    assert Duplex_mode in ["TDD", "FDD"]
    #right now the library only support PDSCH resource allocation 1
    #38.141-1 4.9.2.3.2 define PDSCH resource allocation used by each TM
    assert test_model in ['NR-FR1-TM1.1','NR-FR1-TM2','NR-FR1-TM2a','NR-FR1-TM3.1','NR-FR1-TM3.1a' ]
    assert cell_id in range(1008)

    #first read default configurations
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        waveform_config = json.load(f)
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        carrier_config = json.load(f)
    with open(path + "default_pdsch_config.json", 'r') as f:
        ref_pdsch_config = json.load(f)
    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)
    with open(path + "default_pdcch_config.json", 'r') as f:
        pdcch_config = json.load(f)
    with open(path + "default_search_space.json", 'r') as f:
        search_space_config = json.load(f)
    
    carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)

    #update waveform config
    #Duration is 1 radio frame (10 ms) for FDD and 2 radio frames for TDD (20 ms)
    #from 38.141-1 4.9.2.2
    if Duplex_mode == 'TDD':
        waveform_config['numofslots'] = int(20*scs/15)
    else:
        waveform_config['numofslots'] = int(10*scs/15)
    samplerate_in_mhz = (scs * (2 ** np.ceil(np.log2(carrier_prb_size*12/0.85))) * 1000)/(10 ** 6)
    waveform_config['samplerate_in_mhz'] = samplerate_in_mhz
    waveform_config['startSFN'] = 0
    waveform_config['startslot'] = 0

    #update carrier config
    carrier_config['frequency_range'] = 'FR1'
    carrier_config['BW'] = BW
    carrier_config['scs'] = scs
    carrier_config['num_of_ant'] = 1
    carrier_config['maxMIMO_layers'] = 1
    carrier_config['PCI'] = cell_id
    carrier_config['duplex_type'] = Duplex_mode
    carrier_config['carrier_frequency_in_mhz'] = carrier_frequency_in_mhz

    ssb_config["enable"] = "False"
    csirs_config_list = [] #no CSI-RS 

    coreset_config['enable'] = 'True'
    coreset_config['coreset_id'] = 1
    coreset_config['frequencyDomainResources'] = [1]
    coreset_config['symduration'] = 2
    coreset_config['CCE_REG_mapping_type'] = 'noninterleaved'
    coreset_config['REG_bundle_size'] = 2
    coreset_config['interleaver_size'] = 2
    coreset_config['shift_index'] = 0
    coreset_config['precoder_granularity'] = 'sameAsREG-bundle'
    coreset_config['PDCCH_DMRS_Scrambling_ID'] = cell_id
    coreset_config['CORESET_startingPRB'] = 0
    coreset_config_list = []
    coreset_config_list.append(coreset_config)  

    search_space_config['enable'] = 'True'
    search_space_config['searchSpaceId'] = 1
    search_space_config['controlResourceSetId'] = 1
    search_space_config['monitoringSlotPeriodicityAndOffset'] = [1,0]
    search_space_config['slotduration'] = 1
    search_space_config['FirstSymbolWithinSlot'] = 0
    search_space_config['NrofCandidatesPerAggregationLevel'] = [2,1,0,0,0]
    search_space_config['searchSpaceType'] = 'ue'
    search_space_list = []
    search_space_list.append(search_space_config)

    pdcch_config['enable'] = 'True'
    pdcch_config['rnti'] = 0
    pdcch_config['searchSpaceId'] = 1
    pdcch_config['AggregationLevel'] = 1
    pdcch_config['AllocatedCandidate'] = 0
    pdcch_config['dci_format'] = '1_0'
    pdcch_config['NumDCIBits'] = 20
    
    #TDD pattern is defined in 38.141-1 Table 4.9.2.2-1 
    #for 15khz scs, TDD pattern is 5ms period, DDDSUU, S slot(D/E/U): 10:2:2
    #for 30khz scs, TDD pattern is 5ms period, DDDDDDDSUUUU, S slot(D/E/U): 6:4:4
    if Duplex_mode == 'FDD':
        pdcch_config['period_in_slot'] = 1
        pdcch_config['allocated_slots'] = [0]
    else:
        #TDD
        if scs == 15:
            pdcch_config['period_in_slot'] = 5
            pdcch_config['allocated_slots'] = [0,1,2,3]
        else:
            pdcch_config['period_in_slot'] = 10
            pdcch_config['allocated_slots'] = list(range(8))
    #38.141-1 4.9.2.3.1 define PN23 is used to generate PDCCh bits, 
    # here PN23 is not supproted and just random generate PDCCH bits
    pdcch_config['data_source'] = []
    pdcch_config_list = []
    pdcch_config_list.append(pdcch_config)

    #generate pdsch common config
    ref_pdsch_config["DMRS"]["PDSCHMappintType"] = 'A'
    ref_pdsch_config["DMRS"]["DMRSAddPos"] = 1
    ref_pdsch_config["DMRS"]["DMRSConfigType"] = 1
    ref_pdsch_config["DMRS"]["NrOfDMRSSymbols"] = 1
    ref_pdsch_config["DMRS"]["nSCID"] = 0
    ref_pdsch_config["DMRS"]["NumCDMGroupsWithoutData"] = 1
    ref_pdsch_config["DMRS"]["nNIDnSCID"] = cell_id
    ref_pdsch_config["nID"] = cell_id

    if test_model == 'NR-FR1-TM1.1':
        pdsch_config_list = TM1p1_cfg.gen_TM1p1_pdsch_cfg_list(carrier_prb_size, Duplex_mode, scs,ref_pdsch_config)
    elif test_model == 'NR-FR1-TM2':
        pdsch_config_list = TM2_cfg.gen_TM2_pdsch_cfg_list(carrier_prb_size, Duplex_mode, scs,ref_pdsch_config)
    elif test_model == 'NR-FR1-TM2a':
        pdsch_config_list = TM2a_cfg.gen_TM2a_pdsch_cfg_list(carrier_prb_size, Duplex_mode, scs,ref_pdsch_config)
    elif test_model == 'NR-FR1-TM3.1':
        pdsch_config_list = TM3p1_cfg.gen_TM3p1_pdsch_cfg_list(carrier_prb_size, Duplex_mode, scs,ref_pdsch_config)
    elif test_model == 'NR-FR1-TM3.1a':
        pdsch_config_list = TM3p1a_cfg.gen_TM3p1a_pdsch_cfg_list(carrier_prb_size, Duplex_mode, scs,ref_pdsch_config)
    else:
        assert 0
    
    return waveform_config, carrier_config, ssb_config, csirs_config_list, \
        coreset_config_list, search_space_list, pdcch_config_list, pdsch_config_list

if __name__ == "__main__":
    print("test Test models")
    from tests.nr_testmodel import test_nr_testmodel
    file_lists = test_nr_testmodel.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_testmodel.test_nr_testmodels(filename)
    


    

    
    
    