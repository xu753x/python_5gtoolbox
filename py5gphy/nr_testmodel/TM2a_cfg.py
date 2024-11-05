# -*- coding:utf-8 -*-

import numpy as np
import copy
from py5gphy.nr_testmodel import TM2_cfg

def gen_TM2a_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config):
    """38.141-1 4.9.2.2.4
    only difference between TMa and TM2a is that TM2a use 256QAM while TM2 use 64QAM
    """
    pdsch_config_list = TM2_cfg.gen_TM2_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config)
    for pdsch_config in pdsch_config_list:
        pdsch_config["mcs_index"] = 20 #TargetCodeRateby1024 = 682.5
    
    return pdsch_config_list