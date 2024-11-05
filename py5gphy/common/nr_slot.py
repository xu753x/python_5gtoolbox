# -*- coding:utf-8 -*-
import numpy as np

REusage_types = {0: 'empty',  #not used RE
                 10:'SSB', # RE used as SSB
                 11: 'SSB-PRB-RSV', #SSB may occupy partial of PRB REs, other RE is the PRB is reserved and can not be used by other channel
                 15:'CSI-RS',  #RE used by CSI-RS
                 16:'CSI-RS-RSV',  #if the RE is occupied by one antenna for CSI-RS, this RE on other antenna are reserved and can not be used for PDSCH
                 20: 'CORESET', # RE reserved by search space CORESET, PDSCH can not map to these RE
                 21: 'PDCCH-DMRS', # used by PDCCH DMRS
                 22: 'PDCCH-DATA', #used by PDCCH DATA
                30: 'PDSCH-DMRS-RSV', #PDSCH DMRS may occupy partial of PRB REs, other RE is the PRB is reserved and can not be used by other channel
                31:'PDSCH-DMRS', # used by PDSCH DMRS
                32:'PDSCH-DATA', #used by PDSCH DATA
                40: 'SRS', #used by SRS
                50: 'PUCCH-DATA', #used by PUCCH DATA
                51: 'PUCCH-DMRS', #
                60: 'PUSCH-DMRS-RSV', #PUSCH DMRS may occupy partial of PRB REs, other RE is the PRB is reserved and can not be used by other channel
                61:'PUSCH-DMRS', 
                62:'PUSCH-DATA', #used by ULSCH,UCI..
                63:'PUSCH-ULSCH', #used by ULSCH
                64:'PUSCH-HARQ-ACK', #used by PUSCH ACK 
                65:'PUSCH-HARQ-ACK-RSV', #reserved resources if ACK bits number = 0,1,2
                66:'PUSCH-CSI1', #used by CSI part 1
                67:'PUSCH-CSI2', #used by CSI part 2
                }

def init_fd_slot(num_of_ant, carrier_prbsize):
    """ init frequency domain slot data and RE occupation in the slot
    all values are set to zero
    fd_slot_data, RE_usage_inslot = init_fd_slot(num_of_ant, carrier_prbsize)
    input:
        num_of_ant,
        carrier_prbsize: carrier PRB size
    output:
        fd_slot_data: num_of_ant X (14symbol*12*prbsize) complex frequency domain all zero data
        RE_usage_inslot: num_of_ant X (14symbol*12*prbsize), 
            each value map to one RE occupation type
    """
    fd_slot_data = np.zeros((num_of_ant, 14*12*carrier_prbsize), 'c8')
    RE_usage_inslot = np.zeros([num_of_ant, 14*12*carrier_prbsize],'i1')

    return fd_slot_data, RE_usage_inslot

def get_REusage_type(value):
    assert value in list(REusage_types.keys())
    return REusage_types[value]

def get_REusage_value(type):
    assert type in list(REusage_types.values())
    return list(REusage_types.keys())[list(REusage_types.values()).index(type)]

def get_carrier_prb_size(scs, BW):
    #get carrier PRB size
    scs15_list = {5:25, 10:52, 15:79, 20:106, 25:133, 30:160, 35:188, 40:216, 45:242, 50:270}
    scs30_list = {5:11, 10:24, 15:38, 20:51, 25:65, 30:78, 35:92, 40:106, 45:119, 50:133, 
                  60:162, 70:189, 80:217, 90:245, 100:273}
    if scs == 15:
        carrier_prbsize = scs15_list[BW]
    else:
        carrier_prbsize = scs30_list[BW]
    return carrier_prbsize

if __name__ == "__main__":
    assert get_REusage_type(0) == 'empty'
    assert get_REusage_type(22) == 'PDCCH-DATA'
    assert get_REusage_value('empty') == 0
    assert get_REusage_value('PDCCH-DMRS') == 21