# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.nr_csirs import nr_csirs_info
from py5gphy.nr_csirs import nr_csirs_row1_process
from py5gphy.nr_csirs import nr_csirs_row2_process
from py5gphy.nr_csirs import nr_csirs_row3_process
from py5gphy.nr_csirs import nr_csirs_row4_process
from py5gphy.nr_csirs import nr_csirs_row5_process
from py5gphy.common import nr_slot

class NrCSIRS():
    """ NR CSI RS, support 1/2/4 num of ant ports
        support 38.211 7.4.1.5 Table 7.4.1.5.3-1: CSI-RS locations within a slot. row from 1 to 5
    """
    def __init__(self, carrier_config, csirs_config):
        self.carrier_config = carrier_config
        self.csirs_config = csirs_config

        scs = carrier_config['scs']
        BW = carrier_config['BW']
        carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
        self.carrier_prb_size = carrier_prbsize

        nr_csirs_info.validate_config(csirs_config, carrier_prbsize)

    def is_valid_slot(self,sfn,slot):
        carrier_scs = self.carrier_config['scs']
        #read input
        periodicity = self.csirs_config["periodicity"]
        slotoffset = self.csirs_config["slotoffset"]

        #check if this is CSIRS slot by 38.211 7.4.1.5.3 Mapping to physical resources
        Nslot_in_frame = 10*carrier_scs/15        
        if (Nslot_in_frame*sfn + slot - slotoffset) % periodicity:
            #not CSIRS slot
            return True
        return False
        
    def process(self, fd_slot_data, RE_usage_inslot, sfn,slot):
        """generate one slot frquency domain data that includes CSI-RS data
        output:
            fd_slot_data : frequency slot data after adding CSI-RS, 
            RE_usage_inslot: add CSI-RS mapping 
        """
        
        #get info
        carrier_scs = self.carrier_config['scs']
        #read input
        row = self.csirs_config["frequencyDomainAllocation"]["row"]
        periodicity = self.csirs_config["periodicity"]
        slotoffset = self.csirs_config["slotoffset"]

        #check if rhis is CSIRS slot by 38.211 7.4.1.5.3 Mapping to physical resources
        Nslot_in_frame = 10*carrier_scs/15        
        if (Nslot_in_frame*sfn + slot - slotoffset) % periodicity:
            #not CSIRS slot
            return fd_slot_data, RE_usage_inslot
        
        #matlab 5g toolbox use the common functions to process all row value
        # I think it is too complexed, difficult to design and also hard to understand
        # I would like to write separate function for each row to make it simple
        if row == 1:
            fd_slot_data, RE_usage_inslot = nr_csirs_row1_process.row1_process( \
                fd_slot_data, RE_usage_inslot,self.csirs_config,slot,self.carrier_prb_size)
        elif row == 2:
            fd_slot_data, RE_usage_inslot = nr_csirs_row2_process.row2_process( \
                fd_slot_data, RE_usage_inslot,self.csirs_config,slot,self.carrier_prb_size)
        elif row == 3:
            fd_slot_data, RE_usage_inslot = nr_csirs_row3_process.row3_process( \
                fd_slot_data, RE_usage_inslot,self.csirs_config,slot,self.carrier_prb_size)
        elif row == 4:
            fd_slot_data, RE_usage_inslot = nr_csirs_row4_process.row4_process( \
                fd_slot_data, RE_usage_inslot,self.csirs_config,slot,self.carrier_prb_size)
        elif row == 5:
            fd_slot_data, RE_usage_inslot = nr_csirs_row5_process.row5_process( \
                fd_slot_data, RE_usage_inslot,self.csirs_config,slot,self.carrier_prb_size)
            
        return fd_slot_data, RE_usage_inslot

    def channel_estimation(self, fd_slot, sfn, slot):
        """do channel estimation
        """
        pass

    def RI_PMI_CQI

if __name__ == "__main__":
    print("test nr CSIRS class and waveform generation")
    from tests.nr_csirs import test_nr_csirs
    file_lists = test_nr_csirs.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_csirs.test_nr_csirs(filename)

    aaaa=1

