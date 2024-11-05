# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_pdsch import dl_tbsize
from py5gphy.nr_pdsch import nr_dlsch
from py5gphy.nr_pdsch import nr_pdsch_dmrs
from py5gphy.nr_pdsch import nr_pdsch_process
from py5gphy.nr_pdsch import nrpdsch_resource_mapping
from py5gphy.common import nr_slot

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

def codebook_gen_pm(codebook):
    """ generate precoding matrix from codebook"""
    #todo next
    precoding_matrix = []
    return precoding_matrix


if __name__ == "__main__":
    print("test nr short symbol DLSCH")
    from tests.nr_pdsch import test_nr_pdsch
    file_lists = test_nr_pdsch.get_short_pdsch_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pdsch.test_nr_short_pdsch(filename)

    print("test nr DLSCH")
    from tests.nr_pdsch import test_nr_pdsch
    file_lists = test_nr_pdsch.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pdsch.test_nr_pdsch(filename)