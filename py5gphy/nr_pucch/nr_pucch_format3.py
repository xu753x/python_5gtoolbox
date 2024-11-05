# -*- coding:utf-8 -*-

import numpy as np
import math
from py5gphy.common import nr_slot
from py5gphy.common import nrModulation
from py5gphy.common import nrPRBS
from py5gphy.common import lowPAPR_seq
from py5gphy.nr_pucch import nr_pucch_common
from py5gphy.nr_pucch import nr_pucch_uci

class NrPUCCHFormat3():
    """ PUCCH format 3, 38.211 6.3.2.6 PUCCH formats 3 and 4"""
    def __init__(self, carrier_config, pucch_format3_config):
        self.carrier_config = carrier_config
        self.pucch_format3_config = pucch_format3_config
        
        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs,BW)

        #validate parameters
        #read info
        startingPRB = self.pucch_format3_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format3_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format3_config['secondHopPRB']
        nrofPRBs = self.pucch_format3_config['nrofPRBs']
        nrofSymbols = self.pucch_format3_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format3_config['startingSymbolIndex']
        additionalDMRS = self.pucch_format3_config['additionalDMRS']
        pi2BPSK = self.pucch_format3_config['pi2BPSK']
        pucch_GroupHopping = self.pucch_format3_config['pucch_GroupHopping']
        hoppingId = self.pucch_format3_config['hoppingId']
        NumUCIBits = self.pucch_format3_config['NumUCIBits']
        UCIbits = self.pucch_format3_config['UCIbits']
        NID = self.pucch_format3_config['NID']
        RNTI = self.pucch_format3_config['RNTI']
         
        assert startingPRB in range(self.carrier_prb_size - nrofPRBs)
        assert secondHopPRB in range(self.carrier_prb_size - nrofPRBs)
        assert intraSlotFrequencyHopping in ['enabled', 'disabled']
        assert nrofPRBs in [1,2,3,4,5,6,8,9,10,12,15,16]
        assert nrofSymbols in range(4,15)
        assert startingSymbolIndex in range(14-nrofSymbols+1)
        assert (NumUCIBits > 2) 
        assert len(UCIbits) == NumUCIBits
        assert NID in range(1024)
        assert RNTI in range(65536)
        assert additionalDMRS in ["true", "false"]
        assert pi2BPSK in ["enabled", "disabled"]
        assert pucch_GroupHopping in ["neither", "enable", "disable"]
        assert hoppingId in range(1024)       

    def process(self,fd_slot_data, RE_usage_inslot, sfn,slot):
        """ PUCCH format 3 processing
        """
        carrier_scs = self.carrier_config['scs']
        Nslot_in_frame = 10*int(carrier_scs/15)
        Periodicity_in_slot = self.pucch_format3_config['Periodicity_in_slot']
        slotoffset = self.pucch_format3_config['slotoffset']

        if (Nslot_in_frame*sfn + slot - slotoffset) % Periodicity_in_slot:
            #not PUCCH slot
            return fd_slot_data, RE_usage_inslot

        #read info
        startingPRB = self.pucch_format3_config['startingPRB']
        intraSlotFrequencyHopping = self.pucch_format3_config['intraSlotFrequencyHopping']
        secondHopPRB = self.pucch_format3_config['secondHopPRB']
        nrofPRBs = self.pucch_format3_config['nrofPRBs']
        nrofSymbols = self.pucch_format3_config['nrofSymbols']
        startingSymbolIndex = self.pucch_format3_config['startingSymbolIndex']
        additionalDMRS = self.pucch_format3_config['additionalDMRS']
        pi2BPSK = self.pucch_format3_config['pi2BPSK']
        pucch_GroupHopping = self.pucch_format3_config['pucch_GroupHopping']
        hoppingId = self.pucch_format3_config['hoppingId']
        NumUCIBits = self.pucch_format3_config['NumUCIBits']
        UCIbits = self.pucch_format3_config['UCIbits']
        NID = self.pucch_format3_config['NID']
        RNTI = self.pucch_format3_config['RNTI']

        DMRSsyms, nonDMRSsyms = nr_pucch_common.format34_sym_info(nrofSymbols, startingSymbolIndex, additionalDMRS, intraSlotFrequencyHopping)
        DMRSsym_size = len(DMRSsyms)
            
        #calculate Etot by 38.212 Table 6.3.1.4-1: Total rate matching output sequence length
        if pi2BPSK == 'disabled': 
            #QPSK
            Etot = 24*(nrofSymbols - DMRSsym_size) * nrofPRBs
        else:
            Etot = 12*(nrofSymbols - DMRSsym_size) * nrofPRBs

        # UCI encoding, by 38.212 6.3.1
        g_seq = nr_pucch_uci.encode_uci(UCIbits, NumUCIBits, Etot)

        # 38.211 6.3.2.6 PUCCH format 3
        #6.3.2.5.1 Scrambling
        cinit = RNTI*(2**15) + NID
        c_seq = nrPRBS.gen_nrPRBS(cinit, len(g_seq))
        b_scramb = (g_seq + c_seq) % 2
        
        #6.3.2.5.2 Modulation
        if pi2BPSK == 'disabled': 
            d_seq = nrModulation.nrModulate(b_scramb, 'QPSK')
        else:
            d_seq = nrModulation.nrModulate(b_scramb, 'pi/2-bpsk')
            
        samples_per_symbol = self.carrier_prb_size*12
        # data processing by 38.211 6.3.2.6 PUCCH formats 3 and 4
        d_offset = 0
        MPUCCH3sc = nrofPRBs * 12
        for sym in nonDMRSsyms: #nonDMRSsyms is non-DMRS PUCCH symbol
            PRB_loc = startingPRB
            if (intraSlotFrequencyHopping == 'enabled') and (sym - startingSymbolIndex >= int(nrofSymbols // 2)):
                PRB_loc = secondHopPRB

            #6.3.2.6.4 Transform precoding
            ym = d_seq[d_offset : d_offset + MPUCCH3sc]
            d_offset += MPUCCH3sc
            zk = np.fft.fft(ym) / math.sqrt(MPUCCH3sc)

            #6.3.2.6.5 Mapping to physical resources
            sample_offset = samples_per_symbol*sym + PRB_loc*12
            fd_slot_data[0, sample_offset : sample_offset + nrofPRBs*12 ] = zk
            RE_usage_inslot[0,sample_offset : sample_offset + nrofPRBs*12 ] = nr_slot.get_REusage_value('PUCCH-DATA')
        
        #6.4.1.3.3 Demodulation reference signal for PUCCH formats 3 and 4
        for sym in DMRSsyms:
            #If frequency hopping is enabled, nhop=1 for second hop
            nhop = 0
            PRB_loc = startingPRB
            if (intraSlotFrequencyHopping == 'enabled') and (sym - startingSymbolIndex >= int(nrofSymbols // 2)):
                PRB_loc = secondHopPRB
                nhop = 1

            #PUCCH format 3 DMRS 38.211 6.4.1.3.3.1 Sequence generation
            u, v = nr_pucch_common.Group_and_sequence_hopping(pucch_GroupHopping, hoppingId, slot, nhop)
            m0 = 0
            mcs = 0
            alpha = nr_pucch_common.cyclic_shift_hopping(m0, mcs, slot, sym, hoppingId)
            ruv = lowPAPR_seq.gen_lowPAPR_seq(u, v, alpha, MPUCCH3sc)

            #6.3.2.6.5 Mapping to physical resources
            sample_offset = samples_per_symbol*sym + PRB_loc*12
            fd_slot_data[0, sample_offset : sample_offset + nrofPRBs*12 ] = ruv
            RE_usage_inslot[0,sample_offset : sample_offset + nrofPRBs*12  ] = nr_slot.get_REusage_value('PUCCH-DMRS')

        return fd_slot_data, RE_usage_inslot

if __name__ == "__main__":
    print("test nr PUCCH format 3 class and waveform generation")
    from tests.nr_pucch import test_nr_pucchformat3
    file_lists = test_nr_pucchformat3.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat3.test_nr_pucchformat3(filename)

    aaaa=1