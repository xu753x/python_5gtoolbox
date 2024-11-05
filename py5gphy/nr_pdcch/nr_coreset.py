# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nr_slot

class Coreset():
    """ define PDCCH CORESET class"""

    def __init__(self, carrier_config, coreset_config):
        """ refer 38.311 ControlResourceSet """
        self.coreset_config = coreset_config
        self.carrier_config = carrier_config
        
        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs, BW)

        #read info
        coreset_id = coreset_config["coreset_id"]
        frequencyDomainResources = coreset_config["frequencyDomainResources"]
        symduration = coreset_config["symduration"]
        CCE_REG_mapping_type = coreset_config["CCE_REG_mapping_type"]
        REG_bundle_size = coreset_config["REG_bundle_size"]
        interleaver_size = coreset_config["interleaver_size"]
        shift_index = coreset_config["shift_index"]
        precoder_granularity = coreset_config["precoder_granularity"]
        PDCCH_DMRS_Scrambling_ID = coreset_config["PDCCH_DMRS_Scrambling_ID"]
        CORESET_startingPRB = coreset_config["CORESET_startingPRB"]

        #validate
        assert coreset_id in range(12) #maxNrofControlResourceSets = 12
        #find last 1 index, each bit in frequencyDomainResources map to 6 PRB
        lastone_idx = np.array(frequencyDomainResources).nonzero()[0][-1]
        assert CORESET_startingPRB+(lastone_idx+1)*6 <= self.carrier_prb_size
        
        assert symduration in [1, 2, 3]
        assert CCE_REG_mapping_type in ['noninterleaved', 'interleaved']
        if symduration < 3:
            assert REG_bundle_size in [2, 6]
        else:
            assert REG_bundle_size in [3, 6]
        assert interleaver_size in [2, 3, 6]
        assert shift_index in range(275)
        assert precoder_granularity in ["sameAsREG-bundle", "allContiguousRBs"]
        assert PDCCH_DMRS_Scrambling_ID in range(65536)

        CCE_to_REG_mapping, coreset_prb_list, NUM_CCE = self.CCE_mapping_info()
        self.CCE_to_REG_mapping = CCE_to_REG_mapping
        self.coreset_prb_list = coreset_prb_list
        self.NUM_CCE = NUM_CCE
        
    def CCE_mapping_info(self):
        """ the function is to return CCE to [symbol, PRB] mapping for each CCE       
        return:
            CCE_to_REG_mapping: CCE to [symbol, PRB] mapping
            coreset_prb_list: CORESET PRB list in sorted order
            NUM_CCE: number of CCE
        """
        #read info
        frequencyDomainResources = self.coreset_config["frequencyDomainResources"]
        symduration = self.coreset_config["symduration"]
        CCE_REG_mapping_type = self.coreset_config["CCE_REG_mapping_type"]
        REG_bundle_size = self.coreset_config["REG_bundle_size"]
        interleaver_size = self.coreset_config["interleaver_size"]
        shift_index = self.coreset_config["shift_index"]
        precoder_granularity = self.coreset_config["precoder_granularity"]
        PDCCH_DMRS_Scrambling_ID = self.coreset_config["PDCCH_DMRS_Scrambling_ID"]
        CORESET_startingPRB = self.coreset_config["CORESET_startingPRB"]
        carrier_prb_size = self.carrier_prb_size
              
        #first get CORESET PRB list
        coreset_prb_list = []
        for idx, x in enumerate(frequencyDomainResources):
            if x == 1:
                #idx*6 is PRB index
                coreset_prb_list += [idx*6,idx*6+1,idx*6+2,idx*6+3,idx*6+4,idx*6+5,]
        num_coreset_prb = len(coreset_prb_list)

        #get REG pRB mapping in the slot. REG PRB location = prb + sym*carrier_prb_size
        #generate REG to [sym,PRB0] mapping. one REG = one PRB during one symbol
        #REG is numbered in increasing order in a time-first manner, then PRB
        REG_PRB_mapping = np.zeros(num_coreset_prb*symduration, 'i4')
        offset = 0
        for prb in coreset_prb_list:
            for sym in range(symduration):
                REG_PRB_mapping[offset] = prb + sym*carrier_prb_size
                offset += 1
                
        NCORESET_REG = len(REG_PRB_mapping)
        NUM_CCE = int(NCORESET_REG // 6)

        #38.211 7.3.2.2 Control-resource set (CORESET)
        if CCE_REG_mapping_type == 'noninterleaved':
            CCE_to_REG_mapping = REG_PRB_mapping.reshape((NUM_CCE, 6))   
        else: #interleaved
            REGbundle = REG_PRB_mapping.reshape((NCORESET_REG // REG_bundle_size, REG_bundle_size))
            CCE_to_REG_mapping = np.zeros((NUM_CCE, 6), 'i4')
            for m in range(NUM_CCE):
                #m is CCE index
                C = int(NCORESET_REG/(REG_bundle_size * interleaver_size))
                assert NCORESET_REG % (REG_bundle_size * interleaver_size) == 0
                #num of bundles 6/L
                num_bundles = int(6 // REG_bundle_size)
                for n in range(num_bundles):
                    x = int(6*m/REG_bundle_size) + n #m is CCE index j, here get 6j/L value
                    c = int(x // interleaver_size)
                    r = x - c*interleaver_size
                    fx = (r*C + c + shift_index) % int(NCORESET_REG // REG_bundle_size)
                    CCE_to_REG_mapping[m,n*REG_bundle_size : (n+1)*REG_bundle_size] = REGbundle[fx,:]
                   
                                
        return CCE_to_REG_mapping, coreset_prb_list, NUM_CCE

if __name__ == "__main__":
    import json
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)

    coreset = Coreset(coreset_config)
    


