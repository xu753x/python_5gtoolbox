# -*- coding:utf-8 -*-

import numpy as np
import math
from py5gphy.common import lowPAPR_seq
from py5gphy.common import nr_slot
from py5gphy.common import nrModulation
from py5gphy.nr_pucch import nr_pucch_common
from py5gphy.nr_pucch import nr_pucch_format1_info

class NrPUCCHFormat1():
    """ PUCCH format 1
        38.211 6.3.2.4 PUCCH format 1
    """
    def __init__(self, carrier_config, pucch_format1_config):
        self.carrier_config = carrier_config
        self.pucch_format1_config = pucch_format1_config
        
        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs,BW)

        #validate parameters
        #read info
        startingPRB = self.pucch_format1_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format1_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format1_config['secondHopPRB']
        initialCyclicShift = self.pucch_format1_config['initialCyclicShift']
        nrofSymbols = self.pucch_format1_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format1_config['startingSymbolIndex']
        pucch_GroupHopping = self.pucch_format1_config['pucch_GroupHopping']
        hoppingId = self.pucch_format1_config['hoppingId']
        numHARQbits = self.pucch_format1_config['numHARQbits']
        HARQbits = self.pucch_format1_config['HARQbits']
        timeDomainOCC = self.pucch_format1_config['timeDomainOCC']

        assert startingPRB in range(self.carrier_prb_size)
        assert secondHopPRB in range(self.carrier_prb_size)
        assert intraSlotFrequencyHopping in ['enabled', 'disabled']
        assert initialCyclicShift in range(12)
        assert nrofSymbols in range(4,15)
        assert startingSymbolIndex in range(14-nrofSymbols+1)
        
        #38.211 5.2.2, only one base sequence if ruv length < 72
        # format 0 ruv length = 12, so 'disable' is not supported
        assert pucch_GroupHopping in ['neither', 'enable']
        assert hoppingId in range(1024)
        assert numHARQbits in [1, 2]

        #38.211 Table 6.3.2.4.1-2: Orthogonal sequences
        if intraSlotFrequencyHopping == 'enabled':
            NPUCCH_1_SF_0 = math.floor(math.floor(nrofSymbols/2)/2)
        else:
            NPUCCH_1_SF_0 = math.floor(nrofSymbols/2)
        assert timeDomainOCC in range(NPUCCH_1_SF_0)
        
        #calculate mcs
        self.mcs = 0

        #m0, 38.213 the section above Table 9.2.3-3:
        self.m0 = initialCyclicShift

        #use BPSK in numHARQbits =1, else QPSK, by 38.211 6.3.2.4.1 Sequence modulation
        if numHARQbits == 1:
            d0 = nrModulation.nrModulate(HARQbits[0], 'BPSK')
        else:
            d0 = nrModulation.nrModulate(HARQbits[0:2], 'QPSK')
        
        #PUCCH format 1 DMRS and data processing are almost the same except d(0)=1 for DMRS
        d_list = np.zeros(nrofSymbols,'c8')
        d_list[0::2] = 1 #DMRS
        d_list[1::2] = d0
        self.d_list = d_list

        wm_list, NPUCCH_1_SF_0, NPUCCHDMRS_1_SF_0 = nr_pucch_format1_info.get_wm_list(intraSlotFrequencyHopping, nrofSymbols, timeDomainOCC)
        self.wm_list = wm_list
        self.NPUCCH_1_SF_0 = NPUCCH_1_SF_0
        self.NPUCCHDMRS_1_SF_0 = NPUCCHDMRS_1_SF_0

    def process(self,fd_slot_data, RE_usage_inslot, sfn,slot):
        """ PUCCH format 1 processing
        """
        carrier_scs = self.carrier_config['scs']
        Nslot_in_frame = 10*int(carrier_scs/15)
        Periodicity_in_slot = self.pucch_format1_config['Periodicity_in_slot']
        slotoffset = self.pucch_format1_config['slotoffset']

        if (Nslot_in_frame*sfn + slot - slotoffset) % Periodicity_in_slot:
            #not PUCCH slot
            return fd_slot_data, RE_usage_inslot
        
        #read info
        startingPRB = self.pucch_format1_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format1_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format1_config['secondHopPRB']
        nrofSymbols = self.pucch_format1_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format1_config['startingSymbolIndex']
        pucch_GroupHopping = self.pucch_format1_config['pucch_GroupHopping']
        hoppingId = self.pucch_format1_config['hoppingId']
        
        #this processing handle both data and DMRS
        for m in range(nrofSymbols):
            #If frequency hopping is enabled, nhop=1 for second hop
            nhop = 0
            if (m >= (self.NPUCCH_1_SF_0 + self.NPUCCHDMRS_1_SF_0)) and (intraSlotFrequencyHopping == 'enabled'):
                nhop = 1
            
            #gen ruv, 38.211 6.3.2.3.1 Sequence generation
            sym = m + startingSymbolIndex
            u, v = nr_pucch_common.Group_and_sequence_hopping(pucch_GroupHopping, hoppingId, slot, nhop)
            alpha = nr_pucch_common.cyclic_shift_hopping(self.m0, self.mcs, slot, sym, hoppingId)
            ruv = lowPAPR_seq.gen_lowPAPR_seq(u, v, alpha, 12)

            #d=1 for DMRS
            zn = self.wm_list[m] * self.d_list[m] * ruv
            
            #resource  mapping, 38.211 6.3.2.4.2 Mapping to physical resources
            #put data on all antenna, 
            #TODO: do we need add precoding?
            PRB_loc = startingPRB
            if (m >= (self.NPUCCH_1_SF_0 + self.NPUCCHDMRS_1_SF_0)) and (intraSlotFrequencyHopping == 'enabled'):
                PRB_loc = secondHopPRB
            
            samples_per_symbol = self.carrier_prb_size*12
            sample_offset = samples_per_symbol*sym + PRB_loc*12
            
            #onlys upport one antenna here
            fd_slot_data[0, sample_offset : sample_offset + 12] = zn
            RE_usage_inslot[0,sample_offset : sample_offset + 12] = nr_slot.get_REusage_value('PUCCH-DATA')
        
        return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    print("test nr PUCCH format 1 class and waveform generation")
    from tests.nr_pucch import test_nr_pucchformat1
    file_lists = test_nr_pucchformat1.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat1.test_nr_pucchformat1(filename)

    aaaa=1