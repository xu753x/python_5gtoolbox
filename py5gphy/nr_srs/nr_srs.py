# -*- coding:utf-8 -*-

import numpy as np
import math
from py5gphy.nr_srs import nr_srs_info
from py5gphy.common import lowPAPR_seq
from py5gphy.common import nr_slot

class NrSRS():
    """NR SRS class
    frequency hopping is not supported in this design
    """
    def __init__(self, carrier_config, srs_config):
        self.carrier_config = carrier_config
        self.srs_config = srs_config

        carrier_scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(carrier_scs,BW)
            
    def process(self, fd_slot_data, RE_usage_inslot, sfn,slot):
        """generate one slot frquency domain data that includes SRS data
        output:
            fd_slot_data : frequency slot data after adding SRS, 
            RE_usage_inslot: add SRS mapping 

        """
        samples_per_symbol = self.carrier_prb_size*12

        #get info
        carrier_scs = self.carrier_config['scs']
        nrofSRSPorts = self.srs_config['nrofSRSPorts']
        nrofSymbols = self.srs_config["nrofSymbols"]
        KTC = self.srs_config["KTC"]
        Nslot_in_frame = 10*carrier_scs/15        
        
        #check if this is SRS slot, by 38.211 6.4.1.4.4
        TSRS = self.srs_config["SRSPeriodicity"]
        Toffset = self.srs_config["SRSOffset"]
        if (Nslot_in_frame*sfn + slot - Toffset) % TSRS:
            #not SRS slot
            return fd_slot_data, RE_usage_inslot
        
        info = nr_srs_info.get_nrsrs_info(self.srs_config,slot)

        sym_RE_size = self.carrier_prb_size*12

        #below defined by by 38.214 6.2.1 on  how 5G handle the case when SRS and PUSCH/PUCCH send on the same slot
        #based idea is that SRS shall send after PUSCH symbols, and drop SRS if PUCCH and SRS happen on the same symbol
        #"When PUSCH and SRS are transmitted in the same slot, the UE may only be configured to transmit SRS after the
        #transmission of the PUSCH and the corresponding DM-RS."
        #"For PUCCH and SRS on the same carrier, a UE shall not transmit SRS when semi-persistent or periodic SRS is
        #configured in the same symbol(s) with PUCCH carrying only CSI report(s), or only L1-RSRP report(s). A UE shall not
        #transmit SRS when semi-persistent or periodic SRS is configured or aperiodic SRS is triggered to be transmitted in the
        #same symbol(s) with PUCCH carrying HARQ-ACK and/or SR. In the case that SRS is not transmitted due to overlap
        #with PUCCH, only the SRS symbol(s) that overlap with PUCCH symbol(s) are dropped."

        #check if PUSCH send on SRS symbol
        first_srs_sym = info['srs_symbols'][0]
        pdsch_data_value = nr_slot.get_REusage_value('PDSCH-DATA')
        pdsch_dmrs_value = nr_slot.get_REusage_value('PDSCH-DMRS')
        first_srs_sym_RE = RE_usage_inslot[0,first_srs_sym*sym_RE_size:(first_srs_sym+1)*sym_RE_size]
        if np.count_nonzero(first_srs_sym_RE == pdsch_data_value) or np.count_nonzero(first_srs_sym_RE == pdsch_dmrs_value):
            #assert if PUSCH exist in first SRS symbol
            assert 0

        # processing SRS
        for Lq in range(nrofSymbols):
            srs_sym = info['srs_symbols'][Lq]
            sym_RE = RE_usage_inslot[0,srs_sym*sym_RE_size:(srs_sym+1)*sym_RE_size]
            #drop SRS if PUCCH exist on the symbol
            if np.count_nonzero(sym_RE == nr_slot.get_REusage_value('PDCCH-DATA')) \
                    or np.count_nonzero(sym_RE == nr_slot.get_REusage_value('PDCCH-DMRS')):
                continue

            for port in range(nrofSRSPorts):
                #generate sequence by 38.211 6.4.1.4.2 Sequence generation
                u = info['u_list'][Lq]
                v = info['v_list'][Lq]
                alpha = info['alpha_list'][port]
                MSRS_sc_b = info['MSRS_sc_b']
                rseq = lowPAPR_seq.gen_lowPAPR_seq(u,v,alpha,MSRS_sc_b)

                #resource mapping by 38.211 6.4.1.4.3 Mapping to physical resources
                k0_pi = info['k0_pis'][port]
                rseq = rseq/math.sqrt(nrofSRSPorts)
                
                sym_offset = samples_per_symbol*srs_sym
                assert k0_pi + KTC*MSRS_sc_b <= samples_per_symbol

                fd_slot_data[port, int(sym_offset + k0_pi):int(sym_offset + k0_pi + KTC*MSRS_sc_b):KTC ] \
                    = rseq
                RE_usage_inslot[port,int(sym_offset + k0_pi):int(sym_offset + k0_pi + KTC*MSRS_sc_b):KTC] \
                 = nr_slot.get_REusage_value('SRS')
        
        return fd_slot_data, RE_usage_inslot


if __name__ == "__main__":
    print("test nr SRS class and waveform generation")
    from tests.nr_srs import test_nr_srs
    file_lists = test_nr_srs.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_srs.test_nr_srs(filename)

    aaaa=1