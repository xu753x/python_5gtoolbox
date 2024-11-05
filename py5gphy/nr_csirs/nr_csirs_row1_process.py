# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nr_slot
from py5gphy.common import nrModulation

def row1_process(fd_slot_data, RE_usage_inslot,csirs_config,slot,carrier_prb_size):
    """ CSI RS row = 1 processing based on 38.211 7.4.1.5 CSI reference signals"""
    #read input
    bitstring = csirs_config["frequencyDomainAllocation"]["bitstring"]
    firstOFDMSymbolInTimeDomain = csirs_config["firstOFDMSymbolInTimeDomain"]
    startingRB = csirs_config["startingRB"]
    nrofRBs = csirs_config["nrofRBs"]
    scramblingID = csirs_config["scramblingID"]

    cinit = ((2**10)*(14*slot + firstOFDMSymbolInTimeDomain + 1)*(2*scramblingID + 1) + scramblingID) % (2**31)
    #row 1 each PRB contain 3 csirs RE
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, 2*(startingRB + nrofRBs + 1)*3)
    sel_seq = prbs_seq[2*startingRB*3:]
    CSIRS_seq = nrModulation.nrModulate(sel_seq, 'QPSK')

    #7.4.1.5.3 Mapping to physical resources
    wfk = 1
    wtL = 1
    k_prime = 0
    L_prime = 0

    #find k0,first find rightmost '1' position in bitstring
    f1 =  len(bitstring) - 1 - bitstring.rindex('1')
    k0 = f1

    samples_per_symbol = carrier_prb_size*12
    
    if (startingRB+nrofRBs) > carrier_prb_size:
        nrofRBs = carrier_prb_size - startingRB

    #fill CSI-RS RE
    start_pos = samples_per_symbol*(firstOFDMSymbolInTimeDomain+L_prime) + startingRB*12 + k_prime + k0
    #row1 only support one antenna
    fd_slot_data[0,start_pos : start_pos + nrofRBs*12:4] = wfk*wtL*CSIRS_seq[k_prime:+k_prime+nrofRBs*3]
    RE_usage_inslot[0, start_pos : start_pos + nrofRBs*12:4]= nr_slot.get_REusage_value('CSI-RS')
    if RE_usage_inslot.shape[0] > 1:
        RE_usage_inslot[1:, start_pos : start_pos + nrofRBs*12:4]= nr_slot.get_REusage_value('CSI-RS-RSV')
    
    return fd_slot_data, RE_usage_inslot

