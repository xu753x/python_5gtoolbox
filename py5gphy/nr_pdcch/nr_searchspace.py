# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_pdcch import nr_coreset
from py5gphy.common import nr_slot

class NrSearchSpace():
    """ define PDCCH search space class"""

    def __init__(self, carrier_config, search_space_config, coreset_config):
        """ refer 38.311 ControlResourceSet """
        self.coreset_config = coreset_config
        self.carrier_config = carrier_config
        self.search_space_config = search_space_config

        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs, BW)

        #read info
        coreset_id = coreset_config["coreset_id"]
        controlResourceSetId = search_space_config["controlResourceSetId"]
        monitoringSlotPeriodicityAndOffset = search_space_config["monitoringSlotPeriodicityAndOffset"]
        slotduration = search_space_config["slotduration"]
        FirstSymbolWithinSlot = search_space_config["FirstSymbolWithinSlot"]
        NrofCandidatesPerAggregationLevel = search_space_config["NrofCandidatesPerAggregationLevel"]
        searchSpaceType = search_space_config["searchSpaceType"]

        assert controlResourceSetId == coreset_id
        self.coreset = nr_coreset.Coreset(carrier_config, coreset_config)


        #validate
        assert FirstSymbolWithinSlot + coreset_config["symduration"] < 14
        assert searchSpaceType in ['common', 'ue']
        for (v, L) in zip(NrofCandidatesPerAggregationLevel, [1,2,4,8,16]):
            #ENUMERATED {n0, n1, n2, n3, n4, n5, n6, n8},
            assert v in [0,1,2,3,4,5,6,8]
            assert v*L <= self.coreset.NUM_CCE
        
    def is_active_slot(self, sfn, slot):
        """ check if this slot is search space active slot
        
        """
        scs = self.carrier_config['scs']
        monitoringSlotPeriodicityAndOffset = self.search_space_config["monitoringSlotPeriodicityAndOffset"]
        ks = monitoringSlotPeriodicityAndOffset[0] #PDCCH monitoring periodicity
        Os = monitoringSlotPeriodicityAndOffset[1] #PDCCH monitoring offset
        slotduration = self.search_space_config["slotduration"]

        assert scs in [15, 30]
        if scs == 15:
            Nframe_slot = 10
        else:
            Nframe_slot = 20
        
        for m in range(slotduration):
            if (sfn*Nframe_slot + slot - Os - m) % ks == 0:
                return True
        return False
    
    def gen_cinit(self, rnti):
        """refer to 38.211 7.3.2.3 Scrambling,
         generate cinit """
        PCI = self.carrier_config['PCI']
        searchSpaceType = self.search_space_config['searchSpaceType']
        PDCCH_DMRS_Scrambling_ID = self.coreset_config['PDCCH_DMRS_Scrambling_ID']
        if searchSpaceType == 'ue':
            nID = PDCCH_DMRS_Scrambling_ID
            nRNTI = rnti
        else:
            #common search space
            nID = PCI
            nRNTI = 0
        
        cinit = (nRNTI*(2**16) + nID) % (2**31)
        return cinit
    
    def gen_pdcch_resources(self,AggregationLevel, AllocatedCandidate,rnti,slot):
        """refer to 38.213 10.1 to generate PDCCH PRB resources(sym and RE) that PDCCH data and DMRS map to
        """
        #get info
        FirstSymbolWithinSlot = self.search_space_config["FirstSymbolWithinSlot"]
        NrofCandidatesPerAggregationLevel = self.search_space_config["NrofCandidatesPerAggregationLevel"]
        searchSpaceType = self.search_space_config["searchSpaceType"]
        p = self.coreset_config['coreset_id']

        index = int(np.log2(AggregationLevel))
        ms_nCI = AllocatedCandidate
        Ms_nCI = NrofCandidatesPerAggregationLevel[index] #number of PDCCH candidates
        assert ms_nCI < Ms_nCI

        NCCE = self.coreset.NUM_CCE
        L = AggregationLevel
        nCI = 0 #no CrossCarrierSchedulingConfig

        if searchSpaceType == 'common':
            Yp_nsf = 0
        else:
            Ap = p % 3
            if p % 3 == 0:
                Ap = 39827
            elif p % 3 == 1:
                Ap = 39829
            else:
                Ap = 39839
            D = 65537
            Yp = rnti # init value Yp(-1)
            for m in range(slot+1):
                Yp = (Ap * Yp) % D
        
        first_CCE_index = int(L * ((Yp + (ms_nCI*NCCE // (L*Ms_nCI)) + nCI) % int((NCCE//L))))
        
        #first get PDCCH PRB resources
        PDCCH_PRB_resources = [] #np.zeros(L*6,'i4')
        CCE_to_REG_mapping = self.coreset.CCE_to_REG_mapping
        for m in range(L):
            CCE_idx = first_CCE_index + m
            CCE_resource = list(CCE_to_REG_mapping[CCE_idx]) #get 6 REG PRB location
            PDCCH_PRB_resources += CCE_resource
        
        #PDCCH data resource mapping in increasing order of first k , then l, 
        #so it need sort to get frequency first, then sym order
        PDCCH_PRB_resources.sort()
        #offset by FirstSymbolWithinSlot
        PDCCH_PRB_resources = np.array(PDCCH_PRB_resources,'i4') + FirstSymbolWithinSlot*self.carrier_prb_size

        #second to get PDCCH data RE sources and DMRS RE sources
        #PDCCH DMRS occupy RE 1,5,9, data occupy RE 0,2,3,4,6,7,8,10,11
        PDCCH_DATA_RE_indices = np.zeros(len(PDCCH_PRB_resources)*9,'i4')
        for idx in range(len(PDCCH_PRB_resources)):
            prb_offset = PDCCH_PRB_resources[idx]
            PDCCH_DATA_RE_indices[idx*9 : (idx+1)*9] = np.array([0,2,3,4,6,7,8,10,11],'i4') + prb_offset*12
        
        return PDCCH_DATA_RE_indices, PDCCH_PRB_resources

    def process(self,RE_usage_inslot,sfn, slot):
        """ 38.214 5.1.4.1 PDSCH resource mapping with RB symbol level granularity describe PRBs that are not available for PDSCH
        if 5G has configured RateMatchPattern with CORESET-ID and the slot is active for the search space,
        frequency domain resource of this CORESET is not available for PDSCH(38.214 5.1.4.1)
        if this is search space active slot, the function will map all CORESET PRB resources as used
        """
        if self.is_active_slot(sfn, slot) == False:
            return RE_usage_inslot
        carrier_prb_size = self.carrier_prb_size

        FirstSymbolWithinSlot = self.search_space_config["FirstSymbolWithinSlot"]
        coreset_prb_list = self.coreset.coreset_prb_list
        symduration = self.coreset_config["symduration"]
        for prb in coreset_prb_list:
            for sym in range(symduration):
                slotsym = sym + FirstSymbolWithinSlot
                start_pos = carrier_prb_size*12*slotsym + prb*12
                RE_usage_inslot[0, start_pos: start_pos+12] = nr_slot.get_REusage_value('CORESET')
        return RE_usage_inslot

if __name__ == "__main__":
    import json
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)

    
    


