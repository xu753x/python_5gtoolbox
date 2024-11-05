# -*- coding:utf-8 -*-

import numpy as np
from py5gphy.common import nrPRBS

def Group_and_sequence_hopping(pucch_GroupHopping, hoppingId, slot, nhop):
    """ calculate u,v based on 6.3.2.2.1 Group and sequence hopping"""
    if pucch_GroupHopping == 'neither':
        fgh = 0
        fss = hoppingId % 30
        v = 0
    elif pucch_GroupHopping == 'enable':
        c_init = int(hoppingId // 30)
        N = 8*(2*20+2) 
        cseq = nrPRBS.gen_nrPRBS(c_init, N)
        sel_seq = cseq[8*(slot*2 + nhop) : 8*(slot*2 + nhop)+8]
        fgh = sum(sel_seq*(2**np.arange(8))) % 30
        fss = hoppingId % 30
        v = 0
    elif pucch_GroupHopping == 'disable':
        fgh = 0
        fss = hoppingId % 30
        c_init = (2**5)*int(hoppingId // 30) + int(hoppingId % 30)
        N = 2*slot + nhop + 1
        cseq = nrPRBS.gen_nrPRBS(c_init, N)
        v = cseq[-1]
    else:
        assert 0

    u = (fgh + fss) % 30
    return u, v

def cyclic_shift_hopping(m0, mcs, slot, sym, hoppingId):
    """calculate cyclic shift value 38.211 6.3.2.2.2 Cyclic shift hopping"""
    c_init = hoppingId
    N = 8*14*20
    cseq = nrPRBS.gen_nrPRBS(c_init, N)
    sel_seq = cseq[8*14*slot + 8*sym : 8*14*slot + 8*sym + 8]
    ncs = sum(sel_seq*(2**np.arange(8))) 

    d1 = (m0 + mcs + ncs) % 12
    alpha = 2*np.pi*d1/12
    return alpha

def format34_sym_info(nrofSymbols, startingSymbolIndex, additionalDMRS, intraSlotFrequencyHopping):
    """ return DMRS and non-DMRS sym list
    38.211 6.4.1.3.3 Demodulation reference signal for PUCCH formats 3 and 4
    """
    #Table 6.4.1.3.3.2-1: DM-RS positions for PUCCH format 3 and 4.
    table6413321 = [
        #from nrofSymbols = 5:14
		[[0, 3	],[0, 3       ]],
		[[1, 4	],[1, 4       ]],
		[[1, 4	],[1, 4       ]],
		[[1, 5	],[1, 5       ]],
		[[1, 6	],[1, 6       ]],
		[[2, 7	],[1, 3, 6, 8 ]],
		[[2, 7	],[1, 3, 6, 9 ]],
		[[2, 8	],[1, 4, 7, 10]],
		[[2, 9	],[1, 4, 7, 11]],
		[[3, 10	],[1, 5, 8, 12]]]

    if nrofSymbols == 4:
        if intraSlotFrequencyHopping == 'disabled':
            dmrs_syms = [1]
        else:
            dmrs_syms = [0, 2]
    else: 
        if additionalDMRS == 'true':
            dmrs_syms = table6413321[nrofSymbols-5][1]
        else:
            dmrs_syms = table6413321[nrofSymbols-5][0]
    
    nonDMRSsyms = [x + startingSymbolIndex for x in range(nrofSymbols) if x not in dmrs_syms]
    DMRSsyms = [x + startingSymbolIndex for x in dmrs_syms]
    return DMRSsyms, nonDMRSsyms

