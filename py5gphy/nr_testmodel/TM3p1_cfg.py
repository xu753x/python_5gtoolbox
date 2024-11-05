# -*- coding:utf-8 -*-

import numpy as np
import copy
from py5gphy.nr_testmodel import TM1p1_cfg

def gen_TM3p1_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config):
    """38.141-1 4.9.2.2.5
    only difference between TM3p1 and TM1p1 is that TM3pa use 64QAM instead of QPSK
    """
    pdsch_config_list = TM1p1_cfg.gen_TM1p1_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config)
    for pdsch_config in pdsch_config_list:
        pdsch_config["mcs_index"] = 11 #TargetCodeRateby1024 = 466
    
    return pdsch_config_list