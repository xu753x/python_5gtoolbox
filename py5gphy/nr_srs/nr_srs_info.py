# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.common import nrPRBS
from py5gphy.nr_srs import nr_srs_tables

def get_nrsrs_info(srs_config,slot):
    """ generate paraneters used for SRS processing"""

    #get input
    NSRS_ap = srs_config["nrofSRSPorts"]
    KTC = srs_config["KTC"]
    kTC_bar = srs_config["combOffset"]
    n_cs_SRS = srs_config["cyclicShift"]
    L0 = 14 - 1 - srs_config["startPosition"]
    nrofSymbols = srs_config["nrofSymbols"]
    repetitionFactor = srs_config["repetitionFactor"]
    nRRC = srs_config["freqDomainPosition"]
    nshift = srs_config["freqDomainShift"]
    cSRS = srs_config["cSRS"]
    bSRS = srs_config["bSRS"]
    bhop = srs_config["bhop"]
    assert bhop >= bSRS  #only support fequency hopping is disabled
    groupOrSequenceHopping = srs_config["groupOrSequenceHopping"]
    sequenceId = srs_config["sequenceId"]
    
    ### from 38.211 6.4.1.4.3 Mapping to physical resources

    #read row Table 6.4.1.4.3-1: SRS bandwidth configuration 
    srs_BW_config = nr_srs_tables.get_srs_bw_config(cSRS)
    mSRS_bs = np.array([srs_BW_config[1],srs_BW_config[3],srs_BW_config[5],srs_BW_config[7]])
    Nbs = np.array([srs_BW_config[2],srs_BW_config[4],srs_BW_config[6],srs_BW_config[8]])

    #get nb for bSRS from 0 to 3, for frequency hopping is disabled
    nbs = np.floor(4*nRRC/mSRS_bs) % Nbs
    
    #####cal The frequency-domain starting position####
    #get kTC_pi
    #maximum number of syclic shift
    if KTC == 2:
        ncs_max_SRS = 8
    elif KTC == 4:
        ncs_max_SRS = 12
    kTC_pis = np.array([kTC_bar]*NSRS_ap)
    if (n_cs_SRS>= ncs_max_SRS/2) and (NSRS_ap == 4):
        kTC_pis[1] = (kTC_bar + KTC/2) % KTC
        kTC_pis[3] = (kTC_bar + KTC/2) % KTC
    
    #get k0_pi_bar
    k0_pi_bars = nshift*12 + kTC_pis

    #The length of the sounding reference signal sequence
    MSRS_sc_bs = mSRS_bs*12/KTC

    #get frequency-domain starting position
    k0_pis = k0_pi_bars + sum(KTC*MSRS_sc_bs[0:bSRS+1]*nbs[0:bSRS+1])

    ### from 38.211 6.4.1.4.2 Mapping to physical resources
    #parameters used for SRS sequence generation 38.211 6.4.1.4.2
    MSRS_sc_b = MSRS_sc_bs[bSRS]
    srs_symbols = [L0 + m for m in range(nrofSymbols)]
    
    ncs_i_SRS = [(n_cs_SRS + ncs_max_SRS*p/NSRS_ap) % ncs_max_SRS for p in range(NSRS_ap)]
    alpha_list = 2*np.pi * np.array(ncs_i_SRS) / ncs_max_SRS

    #default value for groupOrSequenceHopping = 'neither'
    fgh_list = [0]*nrofSymbols
    v_list = np.array([0]*nrofSymbols)
    if groupOrSequenceHopping == 'groupHopping':
        for Lq in range(nrofSymbols):
            fgh_list[Lq] = _gen_fgh(slot,L0, Lq,sequenceId)
    elif groupOrSequenceHopping == 'sequenceHopping':
        if MSRS_sc_b >= 6*12:
            for Lq in range(nrofSymbols):
                v_list[Lq] = _gen_v(slot,L0, Lq,sequenceId)
    u_list = (np.array(fgh_list)+sequenceId) % 30

    info = {}
    info['alpha_list'] = alpha_list
    info['u_list'] = u_list.astype(np.int16)
    info['v_list'] = v_list.astype(np.int16)
    info['MSRS_sc_b'] = int(MSRS_sc_b)
    info['k0_pis'] = k0_pis.astype(np.int16)
    info['srs_symbols'] = srs_symbols
    
    return info

def _gen_fgh(slot,L0, Lq,sequenceId):
    """generate fgh when groupOrSequenceHopping equals 'groupHopping',
    """
    #generate one frame of pseudo-random sequence
    seq = nrPRBS.gen_nrPRBS(sequenceId, 8*20*14)

    sel_seq = seq[8*(slot*14+L0+Lq):8*(slot*14+L0+Lq)+8]
    fgh = sum(sel_seq*(2**np.arange(8))) % 30
    return fgh

def _gen_v(slot,L0, Lq,sequenceId):
    """generate v when groupOrSequenceHopping equals 'sequenceHopping',
    when MSRS_sc_b >= 6*12
    """
    #generate one frame of pseudo-random sequence
    seq = nrPRBS.gen_nrPRBS(sequenceId, 20*14)

    v = seq[slot*14+L0+Lq]
    return v

