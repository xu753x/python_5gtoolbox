# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch_validation
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch_dmrs
from py5gphy.nr_pusch import nrpusch_resource_mapping
from py5gphy.nr_pusch import nr_pusch_uci
from py5gphy.nr_pusch import nr_pusch_uci_decode
from py5gphy.nr_pusch import nr_pusch_process
from py5gphy.nr_pusch import nr_pusch_precoding
from py5gphy.channel_equalization import nr_channel_eq
from py5gphy.common import nrPRBS
from py5gphy.demodulation import nr_Demodulation

class NrPUSCH():
    """ PUSCH class
    support: I_LBRM=0, gNB need not limitedbuffer for rate matching
    
    """
    def __init__(self, carrier_config, pusch_config):
        self.carrier_config = carrier_config
        self.pusch_config = pusch_config
        nr_pusch_validation.pusch_config_validate(carrier_config, pusch_config)

        scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
        self.get_info()
        self.rvidx = -1

    def get_info(self):
        """ generate parameters PDSCH used """
        info = {}
        TBSize, Qm, coderateby1024 = ul_tbsize.gen_tbsize(self.pusch_config)
        info["TBSize"] = TBSize
        info["Qm"] = Qm
        info["coderateby1024"] = coderateby1024
                
        self.info = info

    def getnextrv(self):
        rvlist = self.pusch_config['rv']
        self.rvidx = (self.rvidx + 1) % len(rvlist)

        return rvlist[self.rvidx]    
    
    def get_trblk(self,TBSize):
        data_source = list(self.pusch_config["data_source"])
        if not data_source:
            #generate random bit sequence
            trblk = np.random.randint(2, size=TBSize,dtype='i1')
        else:
            data_source = list(data_source)
            data = data_source*(int(TBSize/len(data_source))+1) #extend to be larger than TBSize
            trblk = data[0:TBSize]
            trblk = np.array(trblk, 'i1')
        return trblk
    
    def process(self,fd_slot_data, RE_usage_inslot,slot):
        """
        """
        #first check if this is PUSCH slot
        period_in_slot = self.pusch_config['period_in_slot']
        allocated_slots = self.pusch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return fd_slot_data, RE_usage_inslot
        
        TBSize = self.info["TBSize"]
        Qm = self.info["Qm"]
        num_of_layers = self.pusch_config['num_of_layers']
        rv = self.getnextrv()
        RBSize = self.pusch_config['ResAlloType1']['RBSize']

        #get trblk
        if self.rvidx == 0: #first time sending out trblk
            trblk = self.get_trblk(TBSize)
            self.trblk = trblk
        else: 
            #retransmission
            trblk = self.trblk

        #PUSCH DMRS processing
        fd_slot_data, RE_usage_inslot, DMRSinfo = nr_pusch_dmrs.process(fd_slot_data,RE_usage_inslot,
                self.pusch_config, slot)
        DMRS_symlist = DMRSinfo['DMRS_symlist'] 

        #calculate Gtotal based on 6.2.7 Data and control multiplexing
        RE_usage_inslot, pusch_data_RE_num = \
            nrpusch_resource_mapping.pusch_data_re_mapping_prepare(RE_usage_inslot, self.pusch_config)
        Gtotal = Qm * num_of_layers * pusch_data_RE_num

        g_seq = nr_pusch_uci.ULSCHandUCIProcess(self.pusch_config, trblk, Gtotal, rv, DMRS_symlist)

        rnti = self.pusch_config['rnti']
        nNid = self.pusch_config['nNid']
        nTransPrecode = self.pusch_config['nTransPrecode']
        nNrOfAntennaPorts = self.pusch_config['nNrOfAntennaPorts']
        nPMI = self.pusch_config['nPMI']

        precoding_matrix = nr_pusch_precoding.get_precoding_matrix(num_of_layers, nNrOfAntennaPorts, nPMI)
        ##scrambling, modulation, layer mapping, precoding
        precoded = nr_pusch_process.nr_pusch_process( \
            g_seq, rnti, nNid, Qm, num_of_layers,nTransPrecode, \
            RBSize, nNrOfAntennaPorts, precoding_matrix)

        #PDSCh resouce mapping to Slot RE
        fd_slot_data =nrpusch_resource_mapping.pusch_data_re_mapping(
            precoded, fd_slot_data, RE_usage_inslot, self.pusch_config)

        return fd_slot_data, RE_usage_inslot
    
    def RX_process(self,rx_fd_slot_data, slot,CEQ_config,H_result, cov_m,LDPC_decoder_config,nrChannelEstimation=[],HARQ_on=False,current_LLr_dns=np.array([])):
        """ PUDSCH receiving process
        """
        #first check if this is PUSCH slot
        period_in_slot = self.pusch_config['period_in_slot']
        allocated_slots = self.pusch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return False, np.array([]), np.array([])
        
        StartSymbolIndex = self.pusch_config['StartSymbolIndex']
        Qm = self.info["Qm"] #Qm in [2,4,6,8]
        modtype_list = {1: 'pi/2-bpsk', 2:'qpsk', 4:'16qam', 6:'64qam', 8:'256qam', 10:"1024qam"}
        modtype = modtype_list[Qm]

        #read PUSCH Rx resource
        pusch_resource,pusch_RE_usage = \
            nrpusch_resource_mapping.copy_Rx_pusch_resource(rx_fd_slot_data, self.pusch_config)
        
        #PUSCH Rx resource may need timing offset compensation and freq offset compensation
        if nrChannelEstimation:
            pusch_resource = nrChannelEstimation.process_pdsch_data(pusch_resource,StartSymbolIndex)

        #PUSCh channel equalization
        NrOfSymbols,RE_num,Nr = pusch_resource.shape
        NL = self.pusch_config["num_of_layers"]
        ceq_o = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        noise_vars = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        #init demodulation LLR array with maximim possible size
        demod_LLRs = np.zeros(NrOfSymbols*RE_num*NL*Qm)
        demod_LLR_offset = 0

        for m in range(NrOfSymbols):
            sel_H = H_result[m+StartSymbolIndex,:,:,:]
            sel_cov_m = cov_m[m+StartSymbolIndex,:,:,:]
            for re in range(RE_num):
                if pusch_RE_usage[m,re] != 0: #not PuSCh data RE
                    continue

                Y = pusch_resource[m,re,:]
                prb = re // 12
                H = sel_H[re,:,:]
                cov = sel_cov_m[prb,:,:]
                
                s_est, noise_var, hardbits,LLR = nr_channel_eq.channel_equ_and_demod(Y, H, cov, modtype, CEQ_config)

                demod_LLRs[demod_LLR_offset:demod_LLR_offset+LLR.size] = LLR
                demod_LLR_offset += LLR.size
                
                ceq_o[m,re,:] = s_est 
                noise_vars[m,re,:] = noise_var
        
        #puncture demod_LLRs to correct size
        demod_LLRs = demod_LLRs[0:demod_LLR_offset]

        #6.3.1.4 Transform precoding
        nTransPrecode = self.pusch_config['nTransPrecode']
        RBSize = self.pusch_config['ResAlloType1']['RBSize']
        if nTransPrecode == 1: 
            #transform precoding is enabled and no PTRS
            #PDSCH data will not map to DMRS symbol
            assert NL == 1
            MPUSCHSC = RBSize * 12
            #here demod_LLRs is not real LLr value, LLR value need calculate after de-transform precoding
            assert demod_LLRs.size % MPUSCHSC == 0

            yi = np.zeros(demod_LLRs.size//Qm,'c8')
            no_dmrs_noise_vars = np.zeros(demod_LLRs.size//Qm,'c8')
            offset = 0
            for sym in range(ceq_o.shape[0]):
                ifftin = ceq_o[sym,:,0]
                if np.all(ifftin == 0):
                    continue
                ifftout = np.fft.ifft(ifftin) * math.sqrt(MPUSCHSC)
                yi[offset : offset + MPUSCHSC] = ifftout
                no_dmrs_noise_vars[offset : offset + MPUSCHSC] = noise_vars[sym,:,0]
                offset += MPUSCHSC
            
            #LLR estimate
            de_hardbits,demod_LLRs = nr_Demodulation.nrDemodulate(yi,modtype,no_dmrs_noise_vars)

        #de scrambling
        rnti = self.pusch_config['rnti']
        nNid = self.pusch_config['nNid']
        G=demod_LLRs.size
        cinit = rnti *(2**15) + nNid
        prbs_seq = nrPRBS.gen_nrPRBS(cinit, G)
        #the code didn;t check x/y UCI placeholder bits and it may cause some issue
        #but adding such check seems not easy
        de_scramb_LLR = demod_LLRs * (1-2*prbs_seq)       

        rv = self.getnextrv()

        ulsch_status,tbblk, ulsch_new_LLr_dns = \
            nr_pusch_uci_decode.ULSCHandUCIDecodeProcess(de_scramb_LLR,self.pusch_config, rv, LDPC_decoder_config,HARQ_on,current_LLr_dns)
        
        return ulsch_status,tbblk, ulsch_new_LLr_dns
    def H_LS_est(self,fd_slot_data, slot):
        """ estimate H_LS"""
        H_LS, DMRS_info = nr_pusch_dmrs.pusch_dmrs_LS_est(fd_slot_data,self.pusch_config,slot)
        DMRS_info["scs"] = self.carrier_config['scs']
        
        self.H_LS = H_LS
        self.DMRS_info = DMRS_info
        return H_LS, DMRS_info
    
if __name__ == "__main__":
    if 0:
        print("test nr PUSCH")
        from tests.nr_pusch import test_nr_pusch
        file_lists = test_nr_pusch.get_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_nr_pusch.test_nr_pusch(filename)
    
    if 0:
        print("test nr PUSCH rx, no channel est")
        from tests.nr_pusch import test_nr_pusch_rx_basic
        file_lists = test_nr_pusch_rx_basic.get_testvectors()
        count = 1
        for filename in file_lists:
            #print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_nr_pusch_rx_basic.test_nr_pusch_rx_no_channel_est(filename)
    
    if 1:
        print("test nr PUSCH rx, one tap")
        from tests.nr_pusch import test_nr_pusch_rx_one_tap_channel
        pusch_carrier_testvectors_list = test_nr_pusch_rx_one_tap_channel.get_pusch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pusch_rx_one_tap_channel.get_channel_parameter_list()
        CEQ_algo_list = test_nr_pusch_rx_one_tap_channel.get_channel_equ_config_list()
        CE_config_list = test_nr_pusch_rx_one_tap_channel.get_CE_config_list()
        count = 1
        for pusch_carrier_testvectors in pusch_carrier_testvectors_list:
            for CE_config in CE_config_list:
                for channel_parameter in channel_parameter_list:
                    for CEQ_algo in CEQ_algo_list:        
                        #print(f"count= {count}, {CEQ_algo}")
                        count += 1
                        test_nr_pusch_rx_one_tap_channel.test_nr_pusch_rx_one_tap_basic(pusch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo)