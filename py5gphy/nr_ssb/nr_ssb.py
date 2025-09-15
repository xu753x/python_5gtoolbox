# -*- coding:utf-8 -*-

import numpy as np
from scipy import fft

from py5gphy.nr_ssb import ssb_generate
from py5gphy.nr_ssb import nrBCH
from py5gphy.common import nr_slot
from py5gphy.nr_ssb import nr_ssb_validate
from py5gphy.nr_ssb import nr_ssb_resource_mapping

class NrSSB(object):
    """ nr SSB class
        support SSB PBCH, PSS,SSS generation and resource mapping
        
    """
    def __init__(self, carrier_config, ssb_config):
        self.ssb_config = ssb_config
        self.carrier_config = carrier_config
        nr_ssb_validate.nrssb_config_validate(carrier_config, ssb_config)
        
        self.get_info(carrier_config["carrier_frequency_in_mhz"],carrier_config["duplex_type"])
        scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
                
    from py5gphy.nr_ssb._getinfo import get_info   
    from py5gphy.nr_ssb._getinfo import get_ssbidx_list_in_slot
            
    def process(self,fd_slot_data, RE_usage_inslot,sfn,slot):
        """map ssb block to frequency domain slot
        SSB SCS and PDCCH/PDSCH SCS could be the same or different,
        here only support that SSB SCS is the same with PDCCH/PDSCH SCS, 
        for 30KHz SCS, by spec SSB RE could be totally overlap with DL RE, or could be 15kHz shift from DL RE.
        here only support SSB RE fully overlap with DL RE case
        
        fd_slot_data, RE_usage_inslot = nrSSBProcess(self,fd_slot_data, slot_used_prb,sfn,slot):
        input:
            fd_slot_data: frequency domain slot data, numofant X (14symbol*scs_per_symbol) array
            RE_usage_inslot: 14symbol X (12*prbsize), each value map to RE occupation type
        output:
            fd_slot_data: frequency domain slot data after SSB resource mapping
            RE_usage_inslot: RE occupation type for the slot after adding SSB type
        """
        #gen info
        ssbscs = self.info["ssbscs"]
        slotsize_in_sfn = 10*ssbscs // 15  #number of slot in one SFN
        HRF = slot // (slotsize_in_sfn // 2)  #half frame idx
        
        bchmib = nrBCH.genBCHMIB(self.ssb_config, sfn)

        #check if ssb schedule in the slot
        ssbfirstsym_list,iSSB_list = self.get_ssbidx_list_in_slot(sfn, slot)
        #empty ssbfirstsym_list means no SSB block in the slot
        for idx in range(ssbfirstsym_list.size):
            iSSB = iSSB_list[idx]  
            ssb_block = ssb_generate.gen_ssblock(bchmib, self.ssb_config, self.info["LMax"],self.carrier_config["PCI"], sfn, HRF, iSSB)
            
            #select precoding matrix
            PMI = np.array(self.ssb_config["PMI"])
            sel_pmi = PMI[0:self.carrier_config["num_of_ant"],0]
            
            # precoding and resource mapping 
            for sym in range(4):
                ssb_sym = sym + ssbfirstsym_list[idx]

                precoded = sel_pmi.reshape((sel_pmi.shape[0],1)) @ ssb_block[sym,:].reshape((1,240))
                
                # Matlab 5G toolbox SSB resource mapping function is 
                #implemented in a very complicated method
                fd_slot_data, RE_usage_inslot = nr_ssb_resource_mapping.nrssb_one_symbol_re_mapping( \
                    precoded, fd_slot_data, RE_usage_inslot,ssb_sym,self.ssb_config["NSSB_CRB"],\
                    self.ssb_config["kSSB"], ssbscs)

        return fd_slot_data, RE_usage_inslot       
    
    def waveform_gen(self,waveform_config):
        """the function is to generate SSB time domain waveform
        SSB time domain data generation implementation in Matlab 5G tolbox is very complicated.
        The implementation should be simple and clear
        1. generate SSB burst
        2. calculate frequency offset between SSB lowest subcarrier frequency to central frequency of the carrier
        3. put SSB burst into frequency REs with loweset subcarrier on the carrier central frequency
        4. IFFT/add CP/phase compensation  to get timedomain data
        5. frequency shift timedomain data 
        
        to make it simple, assume all slots are DL slot, 
        (1)to avoid judge special slot, 
        (2)avoid carrier slot vs ssb slot mismatch(carrier scs is different with ssb scs), it would be too complicated
        """
        #get info from waveform config
        samplerate_in_mhz = waveform_config["samplerate_in_mhz"]
        numofslots = waveform_config["numofslots"]
        startSFN = waveform_config["startSFN"]
        startslot = waveform_config["startslot"]
        assert samplerate_in_mhz in [7.68, 15.36, 30.72, 61.44, 122.88, 245.76]
        sample_rate_in_hz = int(samplerate_in_mhz*(10**6))

        #get info from carrier config
        num_of_ant = self.carrier_config["num_of_ant"]
        central_freq_in_hz = int(self.carrier_config["carrier_frequency_in_mhz"] * (10**6))
        
        #calculate frequency offset between SSB lowest subcarrier frequency to central frequency of the carrier
        #first get carrier pointA frequency
        carrier_scs = self.carrier_config['scs']
        carrier_prb_size = self.carrier_prb_size
        #assume  central frequency is zero, get point A frequency in 15Khz step
        PointA_in15khz = int(0 - carrier_prb_size*carrier_scs/15*12/2)

        NSSB_CRB = self.ssb_config["NSSB_CRB"] #offsetto pointA, RB offset to pointA in 15khz SCS
        kSSB = self.ssb_config["kSSB"] #subcarrier offset from SSB subcarrier 0 to SSB_CRB
        #subcarrier 0 of the SS/PBCH block offset to point A in 15khz, by 38.211 7.4.3.1
        #ssb_sc0_in15khz is the frequency offset between SSB lowest subcarrier frequency to central frequency of the carrier
        ssb_sc0_in15khz = PointA_in15khz + NSSB_CRB * 12 + kSSB

        #init IFFT size
        ssbscs = self.info["ssbscs"]
        ifftsize = int(sample_rate_in_hz/(ssbscs*1000))
        assert ifftsize in [128,256,512,1024,2048,4096,8192,16384]

        #get cp table
        #CP size
        ifft4096_scs30_cp_list = np.array([352] + [288]*13)
        ifft4096_scs15_cp_list = np.array([320] + [288]*6 + [320] + [288]*6 )

        if ssbscs == 15:
            cptable = ifft4096_scs15_cp_list / (4096 / ifftsize)
        else:
            cptable = ifft4096_scs30_cp_list / (4096 / ifftsize)
        cptable = cptable.astype(int)
        
        #init output time domain waveform
        td_waveform = np.zeros((num_of_ant, int(sample_rate_in_hz*numofslots*15/ssbscs/1000)), 'c8')

        num_ssb_slot = numofslots 
        for m in range(num_ssb_slot):
            #get sfn and slot
            sfn = startSFN + int((startslot+m)//(ssbscs/15*10))
            slot = (startslot+m) % int(ssbscs/15*10)
            HRF = int(slot // (ssbscs/30*10))  #half frame idx
            
            #check if ssb schedule in the slot
            #ssbfirstsym_list is empty is no SSB block in the slot
            ssbfirstsym_list,iSSB_list = self.get_ssbidx_list_in_slot(sfn, slot)
            if ssbfirstsym_list.size == 0:
                continue

            #time domain one slot size = ifftsize*14 + total cp size(one ifftsize)
            td_slot_data = np.zeros((num_of_ant, ifftsize*15), 'c8')

            bchmib = nrBCH.genBCHMIB(self.ssb_config, sfn)     
            
            for idx in range(ssbfirstsym_list.size):
                iSSB = iSSB_list[idx]  
                ssb_block = ssb_generate.gen_ssblock(bchmib, self.ssb_config, self.info["LMax"],self.carrier_config["PCI"], sfn, HRF, iSSB)
            
                #select precoding matrix
                PMI = np.array(self.ssb_config["PMI"])
                sel_pmi = PMI[0:self.carrier_config["num_of_ant"],0]
            
                # precoding and resource mapping 
                for sym in range(4):
                    ssb_sym = sym + ssbfirstsym_list[idx]

                    precoded = sel_pmi.reshape((sel_pmi.shape[0],1)) @ ssb_block[sym,:].reshape((1,240))
                    
                    ifftin = np.zeros((num_of_ant,ifftsize),'c8')
                    ifftin[:,ifftsize // 2: ifftsize // 2 + 240] = precoded
                    ifftout = fft.ifft(fft.ifftshift(ifftin))
                    #freuency shify by ssb_sc0_in15khz 
                    shift_v = np.exp(1j * 2 * np.pi * ssb_sc0_in15khz*15000/sample_rate_in_hz * np.arange(ifftsize))
                    ifftout = ifftout * shift_v

                    #add cp
                    td_sym = np.zeros((num_of_ant,cptable[ssb_sym] + ifftsize),'c8')
                    td_sym[:, 0:cptable[ssb_sym]] = ifftout[:, -cptable[ssb_sym]:]
                    td_sym[:, cptable[ssb_sym]:] = ifftout

                    #phase compensation for each symbol in one slot assuming tu_start start from 0
                    #phase compemsation for each slot shall be done in other place
                    td_offset = np.sum(cptable[0:ssb_sym]) + ifftsize*ssb_sym
                    if central_freq_in_hz:
                        #phase compensation only when central_freq_in_hz nonzero
                        delta = central_freq_in_hz / sample_rate_in_hz
                        td_sym = td_sym * np.exp(-1j * 2 * np.pi * delta * (td_offset + cptable[ssb_sym]))

                    td_slot_data[:,td_offset : td_offset+cptable[ssb_sym] + ifftsize] = td_sym
            
            #write to td_waveform
            td_waveform[:,m*ifftsize*15 : (m+1)*ifftsize*15]   = td_slot_data

        return  td_waveform       
        
            
if __name__ == "__main__":
    print("test nr ssb waveform generation")
    from tests.nr_ssb import test_nr_ssb_waveform
    file_lists = test_nr_ssb_waveform.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_ssb_waveform.test_ssb_waveform(filename)

    print("test nr SSB")
    from tests.nr_ssb import test_nr_ssb
    file_lists = test_nr_ssb.get_highphy_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_ssb.test_ssb_highphy(filename)