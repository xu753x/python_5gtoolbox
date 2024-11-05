# -*- coding:utf-8 -*-

import numpy as np
import math

def get_wm_list(intraSlotFrequencyHopping,nrofSymbols,timeDomainOCC):
    """generate both PUCCH DMRS and non-DMRS symbol wm value 
    """
    #generate NPUCCH_1_SF_m values for PUCCH data and DMRS
    #based on 38.211 Table 6.3.2.4.1-1: Number of PUCCH symbols and the corresponding
    # and 38.211 Table 6.4.1.3.1.1-1: Number of DM-RS symbols and the corresponding 

    nrofPUCCHdataSymbols = math.floor(nrofSymbols/2)
    if intraSlotFrequencyHopping == 'enabled':
        
        NPUCCH_1_SF_0 = math.floor(nrofPUCCHdataSymbols/2)
        NPUCCH_1_SF_1 = nrofPUCCHdataSymbols - NPUCCH_1_SF_0
        
        nrofPUCCHDMRSSymbols = nrofSymbols - nrofPUCCHdataSymbols
        #38.211 Table 6.4.1.3.1.1-1: Number of DM-RS symbols and the corresponding 
        #Intra-slot hopping and m_prime=0 
        intraSlotFrequencyHopping_m0 = [1,1,2,2,2,2,3,3,3,3,4]
        NPUCCHDMRS_1_SF_0 = intraSlotFrequencyHopping_m0[nrofSymbols-4]
        NPUCCHDMRS_1_SF_1 = nrofPUCCHDMRSSymbols - NPUCCHDMRS_1_SF_0
    else:
        NPUCCH_1_SF_0 = nrofPUCCHdataSymbols
        NPUCCH_1_SF_1 = 0
        nrofPUCCHDMRSSymbols = nrofSymbols - nrofPUCCHdataSymbols
        NPUCCHDMRS_1_SF_0 = nrofPUCCHDMRSSymbols
        NPUCCHDMRS_1_SF_1 = 0
    
    wm_list = np.zeros(nrofSymbols, 'c8')
    #first hop PUCCH data wm value
    ph_list = np.array(_get_ph_list(NPUCCH_1_SF_0, timeDomainOCC))
    wm = np.exp(1j*2*np.pi*ph_list/NPUCCH_1_SF_0)
    wm_list[1:NPUCCH_1_SF_0*2:2] = wm

    if NPUCCH_1_SF_1 > 0: #second hop
        ph_list = np.array(_get_ph_list(NPUCCH_1_SF_1, timeDomainOCC))
        wm = np.exp(1j*2*np.pi*ph_list/NPUCCH_1_SF_1)
        wm_list[NPUCCH_1_SF_0*2+1:nrofSymbols:2] = wm
    
    #first hop PUCCH DMRS wm value
    ph_list = np.array(_get_ph_list(NPUCCHDMRS_1_SF_0, timeDomainOCC))
    wm = np.exp(1j*2*np.pi*ph_list/NPUCCHDMRS_1_SF_0)
    wm_list[0:NPUCCHDMRS_1_SF_0*2:2] = wm

    if NPUCCHDMRS_1_SF_1 > 0: #second hop
        ph_list = np.array(_get_ph_list(NPUCCHDMRS_1_SF_1, timeDomainOCC))
        wm = np.exp(1j*2*np.pi*ph_list/NPUCCHDMRS_1_SF_1)
        wm_list[NPUCCHDMRS_1_SF_0*2:nrofSymbols:2] = wm
    
    return wm_list, NPUCCH_1_SF_0, NPUCCHDMRS_1_SF_0
    
def _get_ph_list(sym_size, timeDomainOCC):
    """ from 38.211 Table 6.3.2.4.1-2: Orthogonal sequences
    get ph list 
    """
    table632412 = [
        [[0]], \
        [[0, 0],[0,1]], \
        [[0,0,0],[0,1,2],[0,2,1]], \
        [[0,0,0,0],[0,2,0,2],[0,0,2,2],[0,2,2,0]], \
        [[0,0,0,0,0],[0,1,2,3,4],[0,2,4,1,3],[0,3,1,4,2],[0,4,3,2,1]], \
        [[0,0,0,0,0,0],[0,1,2,3,4,5],[0,2,4,0,2,4],[0,3,0,3,0,3],[0,4,2,0,4,2],[0,5,4,3,2,1]], \
        [[0,0,0,0,0,0,0],[0,1,2,3,4,5,6],[0,2,4,6,1,3,5],[0,3,6,2,5,1,4],[0,4,1,5,2,6,3],[0,5,3,1,6,4,2],[0,6,5,4,3,2,1]]]

    assert sym_size in range(1,8)
    sel1 = table632412[sym_size - 1]
    assert timeDomainOCC < len(sel1) 
    ph_list = sel1[timeDomainOCC]
    assert len(ph_list) == sym_size
    return ph_list
