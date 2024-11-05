# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nr_slot
from py5gphy.common import nrModulation
from py5gphy.common import nrPRBS
from py5gphy.nr_pucch import nr_pucch_uci

class NrPUCCHFormat2():
    """ PUCCH format 2, 38.211 6.3.2.5 PUCCH format 2"""
    def __init__(self, carrier_config, pucch_format2_config):
        self.carrier_config = carrier_config
        self.pucch_format2_config = pucch_format2_config
        
        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs,BW)

        #validate parameters
        #read info
        startingPRB = self.pucch_format2_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format2_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format2_config['secondHopPRB']
        nrofPRBs = self.pucch_format2_config['nrofPRBs']
        nrofSymbols = self.pucch_format2_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format2_config['startingSymbolIndex']
        NID = self.pucch_format2_config['NID']
        RNTI = self.pucch_format2_config['RNTI']
        NumUCIBits = self.pucch_format2_config['NumUCIBits']
        UCIbits = self.pucch_format2_config['UCIbits']
        NID0 = self.pucch_format2_config['NID0']

        assert startingPRB in range(self.carrier_prb_size - nrofPRBs)
        assert secondHopPRB in range(self.carrier_prb_size - nrofPRBs)
        assert intraSlotFrequencyHopping in ['enabled', 'disabled']
        assert nrofPRBs in range(1,17)
        assert nrofSymbols in range(1,3)
        assert startingSymbolIndex in range(14-nrofSymbols+1)
        assert (NumUCIBits > 2) and (NumUCIBits % 2 == 0)
        assert len(UCIbits) == NumUCIBits
        assert NID in range(1024)
        assert RNTI in range(65536)
        assert NID0 in range(65536)

        

    def process(self,fd_slot_data, RE_usage_inslot, sfn,slot):
        """ PUCCH format 2 processing
        """
        carrier_scs = self.carrier_config['scs']
        Nslot_in_frame = 10*int(carrier_scs/15)
        Periodicity_in_slot = self.pucch_format2_config['Periodicity_in_slot']
        slotoffset = self.pucch_format2_config['slotoffset']

        if (Nslot_in_frame*sfn + slot - slotoffset) % Periodicity_in_slot:
            #not PUCCH slot
            return fd_slot_data, RE_usage_inslot

        #read info
        startingPRB = self.pucch_format2_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format2_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format2_config['secondHopPRB']
        nrofPRBs = self.pucch_format2_config['nrofPRBs']
        nrofSymbols = self.pucch_format2_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format2_config['startingSymbolIndex']
        NID = self.pucch_format2_config['NID']
        RNTI = self.pucch_format2_config['RNTI']
        NumUCIBits = self.pucch_format2_config['NumUCIBits']
        UCIbits = self.pucch_format2_config['UCIbits']
        NID0 = self.pucch_format2_config['NID0']

        # UCI encoding, by 38.212 6.3.1
        # num of PRB * 8non-DMRS RE per PRB * 2(QPSK) * sym bum
        Etot = nrofPRBs*8*2*nrofSymbols
        g_seq = nr_pucch_uci.encode_uci(UCIbits, NumUCIBits, Etot)
        
        # 38.211 6.3.2.5 PUCCH format 2
        #6.3.2.5.1 Scrambling
        cinit = RNTI*(2**15) + NID
        c_seq = nrPRBS.gen_nrPRBS(cinit, len(g_seq))
        b_scramb = (g_seq + c_seq) % 2
        
        #6.3.2.5.2 Modulation
        d_seq = nrModulation.nrModulate(b_scramb, 'QPSK')

        samples_per_symbol = self.carrier_prb_size*12
        for m in range(nrofSymbols):
            sym = m + startingSymbolIndex
            PRB_loc = startingPRB
            if (m == 1) and (intraSlotFrequencyHopping == 'enabled'):
                PRB_loc = secondHopPRB

            #PUCCH format 2 DMRS 38.211 6.4.1.3.2 Demodulation reference signal for PUCCH format 2
            cinit = ((2**17)*(14*slot + sym + 1)*(2*NID0 + 1) + 2*NID0) % (2**31)
            DMRS_len = nrofPRBs*4
            c_seq = nrPRBS.gen_nrPRBS(cinit, (PRB_loc*4 + DMRS_len)*2)
            rm = nrModulation.nrModulate(c_seq[PRB_loc*4*2:], 'QPSK')
                        
            sample_offset = samples_per_symbol*sym + PRB_loc*12
            
            #DMRS 6.4.1.3.2.2 Mapping to physical resources
            fd_slot_data[0, sample_offset + 1 : sample_offset + nrofPRBs*12 : 3] = rm
            RE_usage_inslot[0,sample_offset + 1 : sample_offset + nrofPRBs*12 : 3] = nr_slot.get_REusage_value('PUCCH-DMRS')
            
            #data 6.3.2.5.3 Mapping to physical resources
            offset = m*nrofPRBs*8 #8 RE in one PRB
            fd_slot_data[0, sample_offset : sample_offset + nrofPRBs*12 : 3] = d_seq[offset : offset+nrofPRBs*8 : 2]
            fd_slot_data[0, sample_offset + 2 : sample_offset + nrofPRBs*12 : 3] = d_seq[offset+1 : offset+nrofPRBs*8 : 2]
            RE_usage_inslot[0,sample_offset + 0 : sample_offset + nrofPRBs*12 : 3] = nr_slot.get_REusage_value('PUCCH-DATA')
            RE_usage_inslot[0,sample_offset + 2 : sample_offset + nrofPRBs*12 : 3] = nr_slot.get_REusage_value('PUCCH-DATA')


        return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    print("test nr PUCCH format 2 class and waveform generation")
    from tests.nr_pucch import test_nr_pucchformat2
    file_lists = test_nr_pucchformat2.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat2.test_nr_pucchformat2(filename)

    aaaa=1