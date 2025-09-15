# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_pdsch import dl_tbsize
from py5gphy.nr_pdsch import nr_dlsch
from py5gphy.nr_pdsch import nr_dlsch_rx
from py5gphy.nr_pdsch import nr_pdsch_dmrs
from py5gphy.nr_pdsch import nr_pdsch_process
from py5gphy.nr_pdsch import nrpdsch_resource_mapping
from py5gphy.common import nr_slot
from py5gphy.channel_estimate import nr_channel_estimation
from py5gphy.channel_equalization import nr_channel_eq
from py5gphy.demodulation import nr_Demodulation
from py5gphy.common import nrPRBS

class Pdsch():
    """ define PDSCH class"""

    def __init__(self, pdsch_config, carrier_config):
        """ refer 38.311 ControlResourceSet """
        self.pdsch_config = pdsch_config
        self.carrier_config = carrier_config
        
        scs = carrier_config['scs']
        BW = carrier_config['BW']
        self.carrier_prb_size = nr_slot.get_carrier_prb_size(scs, BW)
        
        self.get_info()
        self.rvidx = -1

        #if pdsch_config["precoding_matrix"] = [], set it to identity matrix
        if self.pdsch_config["precoding_matrix"].size == 0:
            tmp = np.zeros((self.carrier_config["num_of_ant"],self.pdsch_config["num_of_layers"]),'c8')
            for n in range(self.pdsch_config["num_of_layers"]):
                tmp[n,n] = 1
            self.pdsch_config["precoding_matrix"] = tmp
        else:
            self.pdsch_config["precoding_matrix"] =np.array(self.pdsch_config["precoding_matrix"],'c8')

    def get_info(self):
        """ generate parameters PDSCH used """
        info = {}
        TBSize, Qm, coderateby1024 = dl_tbsize.gen_tbsize(self.pdsch_config)
        info["TBSize"] = TBSize
        info["Qm"] = Qm
        info["coderateby1024"] = coderateby1024
        
        TBS_LBRM = dl_tbsize.gen_TBS_LBRM(self.pdsch_config,self.carrier_prb_size,self.carrier_config['maxMIMO_layers'])
        info["TBS_LBRM"] = TBS_LBRM

        self.info = info
    
    def getnextrv(self):
        rvlist = self.pdsch_config['rv']
        self.rvidx = (self.rvidx + 1) % len(rvlist)

        return rvlist[self.rvidx]

    def get_trblk(self,TBSize):
        data_source = list(self.pdsch_config["data_source"])
        if not data_source:
            #generate random bit sequence
            trblk = np.random.randint(2, size=TBSize,dtype='i1')
        else:
            data_source = list(data_source)
            data = data_source*(int(TBSize/len(data_source))+1) #extend to be larger than TBSize
            trblk = data[0:TBSize]
            trblk = np.array(trblk, 'i1')
        return trblk

    def process(self,fd_slot_data, RE_usage_inslot, slot):
        """does (1) PDSCH bit processing(CRC, LDPC, rate matching) 
            (2) PDSCH symbil level procesisng(scrambling, modulation, layer mapping, precoding)
            (3) PDSCH DMRS processing
            (4) PDSCH and PDSCH-DMRS resource mapping to fd_slot_data, and update RE_usage_inslot
            fd_slot_data, RE_usage_inslot = process(self,fd_slot_data, RE_usage_inslot,sfn,slot)
        """
        #first check if this is PDSCH slot
        period_in_slot = self.pdsch_config['period_in_slot']
        allocated_slots = self.pdsch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return fd_slot_data, RE_usage_inslot

        #get input
        TBSize = self.info["TBSize"]
        Qm = self.info["Qm"]
        coderateby1024 = self.info["coderateby1024"]
        TBS_LBRM = self.info["TBS_LBRM"]
        num_of_layers = self.pdsch_config['num_of_layers']
        rv = self.getnextrv()
        rnti = self.pdsch_config['rnti']
        nID = self.pdsch_config['nID']
        num_of_ant = self.carrier_config["num_of_ant"]

        if self.pdsch_config['codebook']['enable'] == "False":
            precoding_matrix = self.pdsch_config['precoding_matrix']
        else:
            precoding_matrix = codebook_gen_pm(self.pdsch_config['codebook'])

        #get trblk
        if self.rvidx == 0: #first time sending out trblk
            trblk = self.get_trblk(TBSize)
            self.trblk = trblk
        else: 
            #retransmission
            trblk = self.trblk
        ### PDSCH DMRS preocessing
        fd_slot_data,RE_usage_inslot= nr_pdsch_dmrs.pdsch_dmrs_process(fd_slot_data,RE_usage_inslot, 
            self.pdsch_config, precoding_matrix, num_of_ant, slot)
        
        #calculate rate mating output total bit len G
        RE_usage_inslot, pdsch_data_RE_num = \
            nrpdsch_resource_mapping.pdsch_data_re_mapping_prepare(RE_usage_inslot, self.pdsch_config)
        G = Qm * num_of_layers * pdsch_data_RE_num

        #CRC, LDPC, rate matching
        g_seq = nr_dlsch.DLSCHEncode(trblk, TBSize, Qm, coderateby1024, num_of_layers, rv, TBS_LBRM, G)

        #scrambling, modulation, layer mapping, precoding
        pdsch_precoded = nr_pdsch_process.nr_pdsch_encode(
            g_seq, rnti, nID, Qm, num_of_layers, precoding_matrix, num_of_ant) 

        #PDSCh resouce mapping to Slot RE
        fd_slot_data =nrpdsch_resource_mapping.pdsch_data_re_mapping(
            pdsch_precoded, fd_slot_data, RE_usage_inslot, self.pdsch_config)

        return fd_slot_data, RE_usage_inslot
    
    def bak_RX_process(self,rx_fd_slot_data, slot,CE_config,CEQ_config,freq_offset=None):
        """ PDSCH receiving process
        CE_config: channel estimation config
        CEQ_config: channel equalization
        """
        #first check if this is PDSCH slot
        period_in_slot = self.pdsch_config['period_in_slot']
        allocated_slots = self.pdsch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return False
        
        StartSymbolIndex = self.pdsch_config['StartSymbolIndex']

        # H-LS est
        H_LS, DMRS_info = self.H_LS_est(rx_fd_slot_data, slot)

        #pdsch channel estimation
        nrChannelEstimation = \
            nr_channel_estimation.NrChannelEstimation(H_LS,DMRS_info, CE_config)

        H_result, cov_m = nrChannelEstimation.channel_est(freq_offset)

        #read PDSCH Rx resource
        pdsch_resource,pdsch_RE_usage = nrpdsch_resource_mapping.copy_Rx_pdsch_resource(rx_fd_slot_data, self.pdsch_config,DMRS_info)

        #PDSCH data timing compensation,to make it simple, timing compensate both PDSCH data and DMRS,
        #also conpemsate overlapped channels such as CSI-RS, SSB,...
        pdsch_resource = nrChannelEstimation.process_pdsch_data(pdsch_resource,StartSymbolIndex)

        #PDSCh channel equalization
        NrOfSymbols,RE_num,Nr = pdsch_resource.shape
        NL = self.pdsch_config["num_of_layers"]
        ceq_o = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        noise_vars = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        for m in range(NrOfSymbols):
            sel_H = H_result[m+StartSymbolIndex,:,:,:]
            sel_cov_m = cov_m[m+StartSymbolIndex,:,:,:]
            for re in range(RE_num):
                Y = pdsch_resource[m,re,:]
                prb = re // 12
                H = sel_H[re,:,:]
                cov = sel_cov_m[prb,:,:]
                if CEQ_config["algo"] == "ZF":
                    s_est, noise_var = ZF.ZF(Y, H, cov)
                elif CEQ_config["algo"] == "ZF-IRC":
                    s_est, noise_var = ZF.ZF_IRC(Y, H, cov)
                elif CEQ_config["algo"] == "MMSE":
                    s_est, noise_var = MMSE.MMSE(Y, H, cov)
                elif CEQ_config["algo"] == "MMSE-IRC":
                    s_est, noise_var = MMSE.MMSE_IRC(Y, H, cov)
                ceq_o[m,re,:] = s_est
                noise_vars[m,re,:] = noise_var

        # PDSCH de-resource mapping to get all REs that is assigned to PDSCH data
        pdsch_data_only = np.zeros((NrOfSymbols* RE_num, NL),'c8')
        pdsch_data_noise_var = np.zeros((NrOfSymbols* RE_num, NL),'c8')
        offset = 0
        for m in range(NrOfSymbols):
            re_size = np.count_nonzero(pdsch_RE_usage[m,:]==0)
            pdsch_data_only[offset:offset+re_size,:] = ceq_o[m,pdsch_RE_usage[m,:]==0,:]
            pdsch_data_noise_var[offset:offset+re_size,:] = noise_vars[m,pdsch_RE_usage[m,:]==0,:]
            offset += re_size
        pdsch_data_only = pdsch_data_only[0:offset,:]
        pdsch_data_noise_var = pdsch_data_noise_var[0:offset,:]

        #de-layer mapping
        de_data = pdsch_data_only.reshape(pdsch_data_only.size,order='F')
        de_noise_var = pdsch_data_noise_var.reshape(pdsch_data_only.size,order='F')

        #LLR soft demodulation
        Qm = self.info["Qm"] #Qm in [2,4,6,8]
        mod_table = {2:'QPSK', 4:'16QAM', 6:'64QAM', 8:'256QAM'}
        hardbits,LLR = nr_Demodulation.nrDemodulate(de_data,mod_table[Qm],de_noise_var)

        #de scrambling
        rnti = self.pdsch_config['rnti']
        nID = self.pdsch_config['nID']
        G=LLR.size
        cinit = rnti *(2**15) + nID
        prbs_seq = nrPRBS.gen_nrPRBS(cinit, G)
        de_scramb = LLR * (1-2*prbs_seq)

    def RX_process(self,rx_fd_slot_data, slot,CEQ_config,H_result, cov_m,LDPC_decoder_config,nrChannelEstimation=[]):
        """ PDSCH receiving process
        CE_config: channel estimation config
        CEQ_config: channel equalization
        """
        #first check if this is PDSCH slot
        period_in_slot = self.pdsch_config['period_in_slot']
        allocated_slots = self.pdsch_config['allocated_slots']
        if (slot % period_in_slot) not in allocated_slots:
            return False
        
        StartSymbolIndex = self.pdsch_config['StartSymbolIndex']
        Qm = self.info["Qm"] #Qm in [2,4,6,8]
        modtype_list = {2:"qpsk", 4:"16qam", 6:"64qam", 8:"256qam", 10:"1024qam"}
        modtype = modtype_list[Qm]
        
        #read PDSCH Rx resource
        pdsch_resource,pdsch_RE_usage = \
            nrpdsch_resource_mapping.copy_Rx_pdsch_resource(rx_fd_slot_data, self.pdsch_config)
        
        #PDSCH Rx resource may need timing offset compensation and freq offset compensation
        if nrChannelEstimation:
            pdsch_resource = nrChannelEstimation.process_pdsch_data(pdsch_resource,StartSymbolIndex)

        #PDSCh channel equalization
        NrOfSymbols,RE_num,Nr = pdsch_resource.shape
        NL = self.pdsch_config["num_of_layers"]
        ceq_o = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        noise_vars = np.zeros((NrOfSymbols, RE_num, NL),'c8')
        #init demodulation LLR array with maximim possible size
        demod_LLRs = np.zeros(NrOfSymbols*RE_num*NL*Qm)
        demod_LLR_offset = 0

        for m in range(NrOfSymbols):
            sel_H = H_result[m+StartSymbolIndex,:,:,:]
            sel_cov_m = cov_m[m+StartSymbolIndex,:,:,:]
            for re in range(RE_num):
                if pdsch_RE_usage[m,re] != 0: #not PDSCh data RE
                    continue

                Y = pdsch_resource[m,re,:]
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

        #de scrambling
        rnti = self.pdsch_config['rnti']
        nID = self.pdsch_config['nID']
        G=demod_LLRs.size
        cinit = rnti *(2**15) + nID
        prbs_seq = nrPRBS.gen_nrPRBS(cinit, G)
        de_scramb_LLR = demod_LLRs * (1-2*prbs_seq)       

        TBSize = self.info["TBSize"]
        coderateby1024 = self.info["coderateby1024"]
        TBS_LBRM = self.info["TBS_LBRM"]
        rv = self.getnextrv()

        status,tbblk, new_LLr_dns = \
            nr_dlsch_rx.DLSCHDecode(de_scramb_LLR,TBSize, Qm, coderateby1024, NL, rv, TBS_LBRM, LDPC_decoder_config,HARQ_on=False)
        
        return status,tbblk, new_LLr_dns

    def H_LS_est(self,fd_slot_data, slot):
        """ estimate H_LS"""
        H_LS, DMRS_info = nr_pdsch_dmrs.pdsch_dmrs_LS_est(fd_slot_data,self.pdsch_config,slot)
        DMRS_info["scs"] = self.carrier_config['scs']
        
        self.H_LS = H_LS
        self.DMRS_info = DMRS_info
        return H_LS, DMRS_info

def codebook_gen_pm(codebook):
    """ generate precoding matrix from codebook"""
    #todo next
    precoding_matrix = []
    return precoding_matrix


if __name__ == "__main__":
    if 0:
        print("test nr short symbol DLSCH")
        from tests.nr_pdsch import test_nr_pdsch
        file_lists = test_nr_pdsch.get_short_pdsch_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_nr_pdsch.test_nr_short_pdsch(filename)

    if 0:
        print("test nr DLSCH")
        from tests.nr_pdsch import test_nr_pdsch
        file_lists = test_nr_pdsch.get_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_nr_pdsch.test_nr_pdsch(filename)
    
    if 0:
        print("test nr PDSCH Rx")
        from tests.nr_pdsch import test_nr_pdsch_rx_basic
        file_lists = test_nr_pdsch_rx_basic.get_testvectors()
        count = 1
        for filename in file_lists:
            print("count= {}, filename= {}".format(count, filename))
            count += 1
            test_nr_pdsch_rx_basic.test_nr_pdsch_rx_no_channel_est(filename)
    
    if 0:
        print("test nr PDSCH Rx AWGN basic")
        from tests.nr_pdsch import test_nr_pdsch_rx_AWGN
        pdsch_carrier_testvectors_list = test_nr_pdsch_rx_AWGN.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_rx_AWGN.get_channel_parameter_list()
        CEQ_algo_list = test_nr_pdsch_rx_AWGN.get_channel_equ_config_list()
        CE_config_list = test_nr_pdsch_rx_AWGN.get_CE_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for CE_config in CE_config_list:
                for channel_parameter in channel_parameter_list:
                    for CEQ_algo in CEQ_algo_list:        
                        #print(f"count= {count}, {CEQ_algo}")
                        count += 1
                        test_nr_pdsch_rx_AWGN.test_nr_pdsch_rx_AWGN_basic(pdsch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo)
                            
    if 0:
        print("test nr PDSCH Rx one tap")
        from tests.nr_pdsch import test_nr_pdsch_rx_one_tap_channel
        pdsch_carrier_testvectors_list = test_nr_pdsch_rx_one_tap_channel.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_rx_one_tap_channel.get_channel_parameter_list()
        CEQ_algo_list = test_nr_pdsch_rx_one_tap_channel.get_channel_equ_config_list()
        CE_config_list = test_nr_pdsch_rx_one_tap_channel.get_CE_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for CE_config in CE_config_list:
                for channel_parameter in channel_parameter_list:
                    for CEQ_algo in CEQ_algo_list:        
                        #print(f"count= {count}, {CEQ_algo}")
                        count += 1
                        test_nr_pdsch_rx_one_tap_channel.test_nr_pdsch_rx_one_tap_basic(pdsch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo)
                        
    
    if 1:
        print("test nr PDSCH Rx TDL basic")
        from tests.nr_pdsch import test_nr_pdsch_rx_TDL
        pdsch_carrier_testvectors_list = test_nr_pdsch_rx_TDL.get_pdsch_carrier_testvectors_list()
        channel_parameter_list = test_nr_pdsch_rx_TDL.get_channel_parameter_list()
        CEQ_algo_list = test_nr_pdsch_rx_TDL.get_channel_equ_config_list()
        CE_config_list = test_nr_pdsch_rx_TDL.get_CE_config_list()
        count = 1
        for pdsch_carrier_testvectors in pdsch_carrier_testvectors_list:
            for CE_config in CE_config_list:
                for channel_parameter in channel_parameter_list:
                    for CEQ_algo in CEQ_algo_list:        
                        #print(f"count= {count}, {CEQ_algo}")
                        count += 1
                        test_nr_pdsch_rx_TDL.test_nr_pdsch_rx_TDL_basic(pdsch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo)
                        test_nr_pdsch_rx_TDL.test_nr_pdsch_rx_TDL_correlated_MIMO(pdsch_carrier_testvectors, CE_config,channel_parameter,CEQ_algo)