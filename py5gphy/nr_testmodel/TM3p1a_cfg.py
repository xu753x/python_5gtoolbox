# -*- coding:utf-8 -*-

import numpy as np
import copy
from py5gphy.nr_testmodel import TM1p1_cfg

def gen_TM3p1a_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config):
    """38.141-1 4.9.2.2.5
    only difference between TM3p1a and TM1p1 is that TM3pa use 256QAM instead of QPSK
    """
    pdsch_config_list = TM1p1_cfg.gen_TM1p1_pdsch_cfg_list(carrier_prb_size,Duplex_mode,scs,ref_pdsch_config)
    for pdsch_config in pdsch_config_list:
        pdsch_config["mcs_index"] = 20 #TargetCodeRateby1024 = 682.5
    
    return pdsch_config_list