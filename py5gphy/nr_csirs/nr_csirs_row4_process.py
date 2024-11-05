import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nr_slot
from py5gphy.common import nrModulation

def row4_process(fd_slot_data, RE_usage_inslot,csirs_config,slot,carrier_prb_size):
    """ CSI RS row = 4 processing  based on 38.211 7.4.1.5 CSI reference signals"""
    #read input
    bitstring = csirs_config["frequencyDomainAllocation"]["bitstring"]
    firstOFDMSymbolInTimeDomain = csirs_config["firstOFDMSymbolInTimeDomain"]
    startingRB = csirs_config["startingRB"]
    nrofRBs = csirs_config["nrofRBs"]
    scramblingID = csirs_config["scramblingID"]
    
    cinit = ((2**10)*(14*slot + firstOFDMSymbolInTimeDomain + 1)*(2*scramblingID + 1) + scramblingID) % (2**31)
    #row 2 each PRB contain at most 1 csirs RE
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, 2*(startingRB + nrofRBs + 1)*2)
    CSIRS_seq = nrModulation.nrModulate(prbs_seq, 'QPSK')

    #7.4.1.5.3 Mapping to physical resources
    wfk = [[1,1],[1,-1]]
    wtL = 1
    k_prime = [0,1]
    L_prime = 0

    #find k0,first find rightmost '1' position in bitstring
    f1 =  len(bitstring) - 1 - bitstring.rindex('1')
    k0 = f1*4

    samples_per_symbol = carrier_prb_size*12

    for port in [0,1,2,3]:
        #port 0 use (k0,k0+1),wfk[0], port 1 use (k0,k0+1) and wfk[1]
        #port 2 use (k0+2,k0+3) and wfk[0],port 3 use (k0+2,k0+3) and wfk[1],
        kbar = k0 + int(port//2)*2
        sel_wfk = wfk[port % 2]

        #k_prime[0] mapping
        start_pos = samples_per_symbol*(firstOFDMSymbolInTimeDomain+L_prime) + startingRB*12 + k_prime[0] + kbar
        fd_slot_data[port,start_pos:start_pos+nrofRBs*12:12] = \
            sel_wfk[0]*wtL*CSIRS_seq[startingRB*2 + k_prime[0] : startingRB*2 + k_prime[0] + nrofRBs*2 : 2]

        RE_usage_inslot[port,start_pos:start_pos+nrofRBs*12:12] = nr_slot.get_REusage_value('CSI-RS')

        if port == 0:
            #k0+2 RE are reserved and PDSCH should not map to these REs
            RE_usage_inslot[port,start_pos+2:start_pos+nrofRBs*12:12] = nr_slot.get_REusage_value('CSI-RS-RSV')
        
        #k_prime[1] mapping
        start_pos = samples_per_symbol*(firstOFDMSymbolInTimeDomain+L_prime) + startingRB*12 + k_prime[1] + kbar
        fd_slot_data[port,start_pos:start_pos+nrofRBs*12:12] = \
            sel_wfk[1]*wtL*CSIRS_seq[startingRB*2 + k_prime[1] : startingRB*2 + k_prime[1] + nrofRBs*2 : 2]

        RE_usage_inslot[port,start_pos:start_pos+nrofRBs*12:12] = nr_slot.get_REusage_value('CSI-RS')
        if port == 0:
            #k0+3 RE are reserved and PDSCH should not map to these REs
            RE_usage_inslot[port,start_pos+2:start_pos+nrofRBs*12:12] = nr_slot.get_REusage_value('CSI-RS-RSV')
    
    return fd_slot_data, RE_usage_inslot