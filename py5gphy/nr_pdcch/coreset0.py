# -*- coding:utf-8 -*-

import numpy as np

def gen_coreset0_config(ssb_lowest_prb,pdcch_ConfigSIB1, scs, PCI):
    """generate CORESET0 config from SSB parameter
    """
    coreset_cfg = {}
    
    #38.213 Table 13-1: Set of resource blocks and slot symbols of CORESET for Type0-PDCCH search space set
    #when {SS/PBCH block, PDCCH} SCS is {15, 15} kHz for frequency bands with minimum channel
    #bandwidth 5 MHz or 10 MHz
    # num of RB, num of symbol, offset for each pdcch_ConfigSIB1 index
    set_15khz = [[24, 2, 0 ],
        [24, 2, 2 ],
        [24, 2, 4 ],
        [24, 3, 0 ],
        [24, 3, 2 ],
        [24, 3, 4 ],
        [48, 1, 12],
        [48, 1, 16],
        [48, 2, 12],
        [48, 2, 16],
        [48, 3, 12],
        [48, 3, 16],
        [96, 1, 38],
        [96, 2, 38],
        [96, 3, 38]]
    #38.213 Table 13-4: Set of resource blocks and slot symbols of CORESET for Type0-PDCCH search space set
    #when {SS/PBCH block, PDCCH} SCS is {30, 30} kHz for frequency bands with minimum channel
    #bandwidth 5 MHz or 10 MHz
    #38.101-1 Table 5.3.5-1 Channel bandwidths for each NR band list all BW supported by each band
    #minimum channel bandwidth 40MHz only happened on n76 which is for DL only and 
    # almost never used by product
    # num of RB, num of symbol, offset for each pdcch_ConfigSIB1 index
    set_30khz = [[24, 2, 0 ],
		[24, 2, 1 ],
		[24, 2, 2 ],
		[24, 2, 3 ],
		[24, 2, 4 ],
		[24, 3, 0 ],
		[24, 3, 1 ],
		[24, 3, 2 ],
		[24, 3, 3 ],
		[24, 3, 4 ],
		[48, 1, 12],
		[48, 1, 14],
		[48, 1, 16],
		[48, 2, 12],
		[48, 2, 14],
		[48, 2, 16]

    ]

    if scs == 15:
        sel_set = set_15khz
        assert pdcch_ConfigSIB1 < 15
    else:
        sel_set = set_30khz
        assert pdcch_ConfigSIB1 < 16

    coreset_cfg["coreset_id"] = 0

    N_CORESET_RB = sel_set[pdcch_ConfigSIB1, 0]
    N_CORESET_sym = sel_set[pdcch_ConfigSIB1, 1]
    offset = sel_set[pdcch_ConfigSIB1, 2]

    CORESET_startingPRB = ssb_lowest_prb + offset
    
    coreset_cfg["frequencyDomainResources"] = [1]*(N_CORESET_RB // 6) \
                            + [0]*(45 - (N_CORESET_RB // 6))
    coreset_cfg["symduration"] = N_CORESET_sym

    # by 38.211 7.3.2.2
    coreset_cfg["CCE_REG_mapping_type"] = "interleaved"
    coreset_cfg["REG_bundle_size"] = 6
    coreset_cfg["interleaver_size"] = 2
    coreset_cfg["shift_index"] = PCI
    coreset_cfg["precoder_granularity"] = "sameAsREG-bundle"
    coreset_cfg["PDCCH_DMRS_Scrambling_ID"] = PCI
    coreset_cfg["CORESET_startingPRB"] = CORESET_startingPRB

    return coreset_cfg
