# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_pdcch import nr_dci_encoder
from py5gphy.common import nr_slot
from py5gphy.common import nrModulation
from py5gphy.common import nrPRBS

class Pdcch():
    def __init__(self, pdcch_config, nrSearchSpace):
        self.pdcch_config = pdcch_config
        self.nrSearchSpace = nrSearchSpace

        #get info
        rnti = self.pdcch_config['rnti']
        searchSpaceId = self.pdcch_config['searchSpaceId']
        AggregationLevel = self.pdcch_config['AggregationLevel']
        AllocatedCandidate = self.pdcch_config['AllocatedCandidate']
        
        #validate
        assert rnti in range(65536)
        assert searchSpaceId == nrSearchSpace.search_space_config['controlResourceSetId']
        assert AggregationLevel in [1,2,4,8,16]
        assert AllocatedCandidate < 8
        
    def get_DCIbits(self,NumDCIBits):
        data_source = list(self.pdcch_config['data_source'])
        if not data_source:
            #generate random bit sequence
            DCIbits = np.random.randint(2, size=NumDCIBits,dtype='i1')
        else:
            data_source = list(data_source)
            data = data_source*(int(NumDCIBits/len(data_source))+1) #extend to be larger than TBSize
            DCIbits = np.array(data[0:NumDCIBits], 'i1')
            
        return DCIbits
    
    def process(self,fd_slot_data, RE_usage_inslot, sfn,slot):
        """ PDCCH processing
            PDCCH occupy first antenna only
        """
        
        #first check if this is PDSCH slot
        period_in_slot = self.pdcch_config['period_in_slot']
        allocated_slots = self.pdcch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return fd_slot_data, RE_usage_inslot
        
        #searchspace should also be active
        assert self.nrSearchSpace.is_active_slot(sfn, slot) == True          
        
        #get info
        rnti = self.pdcch_config['rnti']
        AggregationLevel = self.pdcch_config['AggregationLevel']
        AllocatedCandidate = self.pdcch_config['AllocatedCandidate']
        NumDCIBits = self.pdcch_config['NumDCIBits']
        DCIbits = self.get_DCIbits(NumDCIBits)
        precoding_matrix = self.pdcch_config['precoding_matrix']
        carrier_prb_size = self.nrSearchSpace.carrier_prb_size
        samples_per_symbol = carrier_prb_size*12

        #calculate rate matching total output length E
        #6:1CCE=6REG=6PRB, 9: non-DMRS REs in one PRB, 2: QPSK
        E = AggregationLevel*6*9*2
        fe = nr_dci_encoder.nrDCIEncode(DCIbits, rnti, E)

        #38.211 7.3.2.3 Scrambling
        cinit = self.nrSearchSpace.gen_cinit(rnti)
        c_seq = nrPRBS.gen_nrPRBS(cinit, len(fe))
        b_scramb = (fe + c_seq) % 2

        #7.3.2.4 PDCCH modulation
        d_seq = nrModulation.nrModulate(b_scramb, 'QPSK')

        #get PDCCH [sym, prb] resources based on AggregationLevel and AllocatedCandidate
        # refer to 38.213 10.1 
        #? does PDCCh occupy the same PRBs for all symbols? 
        # let's design it assume PRB could be different for different symbol
        PDCCH_DATA_RE_indices, PDCCH_PRB_resources = self.nrSearchSpace.gen_pdcch_resources(AggregationLevel, AllocatedCandidate,rnti,slot)

        #38.211 7.3.2.5 Mapping to physical resources
        symduration = self.nrSearchSpace.coreset_config['symduration']
        assert len(d_seq) == len(PDCCH_DATA_RE_indices)
        fd_slot_data[0, PDCCH_DATA_RE_indices] = d_seq
        RE_usage_inslot[0, PDCCH_DATA_RE_indices] = nr_slot.get_REusage_value('PDCCH-DATA')      

        # 38.211 7.4.1.3 Demodulation reference signals for PDCCH
        #first generate sequence for all CORESET symbols
        FirstSymbolWithinSlot = self.nrSearchSpace.search_space_config['FirstSymbolWithinSlot']
        DMRS_len = carrier_prb_size * 3 #one PRB contain 3 DMRS RE
        NID = self.nrSearchSpace.coreset_config['PDCCH_DMRS_Scrambling_ID']
        
        dmrs_seqs = np.zeros((symduration, DMRS_len), 'c8')
        for m in range(symduration):
            sym = FirstSymbolWithinSlot + m
            cinit = ((2**17)*(14*slot + sym + 1)*(2*NID + 1) + 2*NID) % (2**31)
            c_seq = nrPRBS.gen_nrPRBS(cinit, DMRS_len*2)
            rm = nrModulation.nrModulate(c_seq, 'QPSK')
            dmrs_seqs[m,:] = rm
        
        #7.4.1.3.2 Mapping to physical resources
        #TODO: need additional code to support CORESET0 
        #for CORESET0, DMRS sequence start from first_SSB PRB, not PRB 0
        precoder_granularity = self.nrSearchSpace.coreset_config["precoder_granularity"]
        if precoder_granularity == 'allContiguousRBs':
            #DMRS maps to all PRBs of CORESET, 
            # to make it simple, the system only support all PRB in CORESET are contiguous
            coreset_prb_list = self.nrSearchSpace.coreset.coreset_prb_list
            for sym_idx in range(symduration):
                sym = FirstSymbolWithinSlot + sym_idx
                for prb in coreset_prb_list:
                    sel_dmrs_seq = dmrs_seqs[sym_idx, prb*3:(prb+1)*3]
                    sample_offset = samples_per_symbol*sym + prb*12

                    #RE 1,5,9 for DMRS
                    fd_slot_data[0, sample_offset+1 : sample_offset + 12 : 4 ] = sel_dmrs_seq
                    RE_usage_inslot[0, sample_offset+1 : sample_offset + 12 : 4] = nr_slot.get_REusage_value('PDCCH-DMRS')                                               
        else:
            #sameAsREG-bundle, DMRS map to PDCCH data PRB only
            for prb_offset in PDCCH_PRB_resources:
                #CORESET REG are numbered in a time-first manner, 
                # for example if CORESET occupy 2 symbol and PRB 0-9, REG0 map to sym0-prb0, REG1 map to sym1-prb0
                #prb_offset = sym*carrier_prb_size + PRB_in_sym
                sym = int(prb_offset // carrier_prb_size)
                prb = prb_offset - sym*carrier_prb_size
                sym_idx = sym - FirstSymbolWithinSlot
                sel_dmrs_seq = dmrs_seqs[sym_idx, prb*3:(prb+1)*3]
                sample_offset = samples_per_symbol*sym + prb*12
                #DMRS occupy RE 1,5,9, 
                fd_slot_data[0, sample_offset+1 : sample_offset + 12 : 4 ] = sel_dmrs_seq
                RE_usage_inslot[0, sample_offset+1 : sample_offset + 12 : 4] = nr_slot.get_REusage_value('PDCCH-DMRS')                                          
        
        return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    print("test nr PDCCH class and waveform generation")
    from tests.nr_pdcch import test_nr_pdcch
    file_lists = test_nr_pdcch.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pdcch.test_nr_pdcch(filename)
