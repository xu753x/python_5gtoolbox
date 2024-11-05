# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.common import lowPAPR_seq
from py5gphy.common import nr_slot
from py5gphy.nr_pucch import nr_pucch_common

class NrPUCCHFormat0():
    """ PUCCH format 0
        38.211 6.3.2.3 PUCCH format 0
    """
    def __init__(self, carrier_config, pucch_format0_config):
        self.carrier_config = carrier_config
        self.pucch_format0_config = pucch_format0_config
        
        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs,BW)

        #validate parameters
        #read info
        startingPRB = self.pucch_format0_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format0_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format0_config['secondHopPRB']
        initialCyclicShift = self.pucch_format0_config['initialCyclicShift']
        nrofSymbols = self.pucch_format0_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format0_config['startingSymbolIndex']
        pucch_GroupHopping = self.pucch_format0_config['pucch_GroupHopping']
        hoppingId = self.pucch_format0_config['hoppingId']
        numHARQbits = self.pucch_format0_config['numHARQbits']
        HARQbits = self.pucch_format0_config['HARQbits']
        SR = self.pucch_format0_config['SR']

        assert startingPRB in range(self.carrier_prb_size)
        assert secondHopPRB in range(self.carrier_prb_size)
        assert intraSlotFrequencyHopping in ['enabled', 'disabled']
        assert initialCyclicShift in range(12)
        assert nrofSymbols in [1,2]
        if nrofSymbols == 1:
            assert startingSymbolIndex in range(14)
        else:
            assert startingSymbolIndex in range(13)
        
        #38.211 5.2.2, only one base sequence if ruv length < 72
        # format 0 ruv length = 12, so 'disable' is not supported
        assert pucch_GroupHopping in ['neither', 'enable']
        assert hoppingId in range(1024)
        assert numHARQbits in [0, 1, 2]
        assert SR in ['positive', 'negative']

        #calculate mcs
        numHARQbits = self.pucch_format0_config['numHARQbits']
        HARQbits = self.pucch_format0_config['HARQbits']
        SR = self.pucch_format0_config['SR']
        if SR == 'negative':
            if numHARQbits == 0:
                #38.213 9.2.4 UE procedure for reporting SR:
                mcs =  0
            elif numHARQbits == 1:
                #38.213 Table 9.2.3-3:
                mcs =  HARQbits[0] * 6
            else:
                #38.213 Table 9.2.3-4:
                table9234 = [0,3,9,6]
                mcs = table9234[HARQbits[0]*2 + HARQbits[1]]
        else:
            if numHARQbits == 0:
                #38.213 9.2.4 UE procedure for reporting SR:
                mcs =  0
            elif numHARQbits == 1:
                #38.213 Table 9.2.5-1:
                mcs =  3 + HARQbits[0] * 6
            else:
                #38.213 Table 9.2.5-2:
                table9252 = [1, 4, 10, 7]
                mcs = table9252[HARQbits[0]*2 + HARQbits[1]]
        self.mcs = mcs

        #m0, 38.213 the section above Table 9.2.3-3:
        self.m0 = initialCyclicShift

    def process(self,fd_slot_data, RE_usage_inslot, sfn,slot):
        """ PUCCH format 0 processing
        """
        carrier_scs = self.carrier_config['scs']
        Nslot_in_frame = 10*int(carrier_scs/15)
        Periodicity_in_slot = self.pucch_format0_config['Periodicity_in_slot']
        slotoffset = self.pucch_format0_config['slotoffset']

        if (Nslot_in_frame*sfn + slot - slotoffset) % Periodicity_in_slot:
            #not PUCCH slot
            return fd_slot_data, RE_usage_inslot

        numHARQbits = self.pucch_format0_config['numHARQbits']
        SR = self.pucch_format0_config['SR']
        if (numHARQbits == 0) and (SR == 'negative'):
            #no PUCCH if no ACKinformation and SR is negative
            return fd_slot_data, RE_usage_inslot

        #read info
        startingPRB = self.pucch_format0_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format0_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format0_config['secondHopPRB']
        nrofSymbols = self.pucch_format0_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format0_config['startingSymbolIndex']
        pucch_GroupHopping = self.pucch_format0_config['pucch_GroupHopping']
        hoppingId = self.pucch_format0_config['hoppingId']
        
        #
        for m in range(nrofSymbols):
            #If frequency hopping is enabled, nhop=1 for second hop
            nhop = 0
            if (m == 1) and (intraSlotFrequencyHopping == 'enabled'):
                nhop = 1
            
            #gen ruv, 38.211 6.3.2.3.1 Sequence generation
            sym = m + startingSymbolIndex
            u, v = nr_pucch_common.Group_and_sequence_hopping(pucch_GroupHopping, hoppingId, slot, nhop)
            alpha = nr_pucch_common.cyclic_shift_hopping(self.m0, self.mcs, slot, sym, hoppingId)
            ruv = lowPAPR_seq.gen_lowPAPR_seq(u, v, alpha, 12)

            #resource  mapping, 38.211 6.3.2.3.2 Mapping to physical resources
            #put data on all antenna, 
            #TODO: do we need add precoding?
            PRB_loc = startingPRB
            if (m == 1) and (intraSlotFrequencyHopping == 'enabled'):
                PRB_loc = secondHopPRB
            
            samples_per_symbol = self.carrier_prb_size*12
            sample_offset = samples_per_symbol*sym + PRB_loc*12
            fd_slot_data[0, sample_offset : sample_offset + 12] = ruv
            RE_usage_inslot[0,sample_offset : sample_offset + 12] = nr_slot.get_REusage_value('PUCCH-DATA')
        
        return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    print("test nr PUCCH format 0 class and waveform generation")
    from tests.nr_pucch import test_nr_pucchformat0
    file_lists = test_nr_pucchformat0.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat0.test_nr_pucchformat0(filename)

    aaaa=1