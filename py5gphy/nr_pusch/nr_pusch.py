# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch_validation
from py5gphy.nr_pusch import ul_tbsize
from py5gphy.nr_pusch import nr_pusch_dmrs
from py5gphy.nr_pusch import nrpusch_resource_mapping
from py5gphy.nr_pusch import nr_pusch_uci
from py5gphy.nr_pusch import nr_pusch_process
from py5gphy.nr_pusch import nr_pusch_precoding

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
    
    def rx_process(self,fd_slot_data, slot):
        """ PUDSCH receiving process
        """
        #pdsch timing ofsfet estimation
        
        #timing offset compensation

        #pdsch channel estimation

        #PDSCh channel equalization

        #DSCH receiving processing
               
        TBSize = self.info["TBSize"]
        Qm = self.info["Qm"]
        num_of_layers = self.pusch_config['num_of_layers']
        rv = self.getnextrv()
        RBSize = self.pusch_config['ResAlloType1']['RBSize']

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
        
if __name__ == "__main__":
    print("test nr PUSCH")
    from tests.nr_pusch import test_nr_pusch
    file_lists = test_nr_pusch.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pusch.test_nr_pusch(filename)