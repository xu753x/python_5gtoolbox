# -*- coding:utf-8 -*-

import numpy as np
import json

def read_DL_default_config_files():
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_DL_waveform_config.json", 'r') as f:
        DL_waveform_config = json.load(f)
    with open(path + "default_DL_carrier_config.json", 'r') as f:
        DL_carrier_config = json.load(f)
    with open(path + "default_pdsch_config.json", 'r') as f:
        pdsch_config = json.load(f)
    with open(path + "default_ssb_config.json", 'r') as f:
        ssb_config = json.load(f)
    with open(path + "default_coreset_config.json", 'r') as f:
        coreset_config = json.load(f)
    with open(path + "default_pdcch_config.json", 'r') as f:
        pdcch_config = json.load(f)
    with open(path + "default_search_space.json", 'r') as f:
        search_space_config = json.load(f)
    
    with open(path + "default_csirs_config.json", 'r') as f:
        csirs_config = json.load(f)
    with open(path + "default_csirs_report_config.json", 'r') as f:
        csirs_report_config = json.load(f)
    
    default_DL_config={}
    default_DL_config["DL_waveform_config"] = DL_waveform_config
    default_DL_config["DL_carrier_config"] = DL_carrier_config
    default_DL_config["pdsch_config"] = pdsch_config
    default_DL_config["ssb_config"] = ssb_config
    default_DL_config["coreset_config"] = coreset_config
    default_DL_config["pdcch_config"] = pdcch_config
    default_DL_config["search_space_config"] = search_space_config
    default_DL_config["csirs_config"] = search_space_config
    default_DL_config["csirs_report_config"] = search_space_config
    return default_DL_config

def read_UL_default_config_files():
    path = "py5gphy/nr_default_config/"
    
    with open(path + "default_UL_waveform_config.json", 'r') as f:
        UL_waveform_config = json.load(f)
    with open(path + "default_UL_carrier_config.json", 'r') as f:
        UL_carrier_config = json.load(f)
    with open(path + "default_prach_config.json", 'r') as f:
        prach_config = json.load(f)
    with open(path + "default_pusch_config.json", 'r') as f:
        pusch_config = json.load(f)
    with open(path + "default_pucch_format0_config.json", 'r') as f:
        pucch_format0_config = json.load(f)
    with open(path + "default_pucch_format1_config.json", 'r') as f:
        pucch_format1_config = json.load(f)
    with open(path + "default_pucch_format2_config.json", 'r') as f:
        pucch_format2_config = json.load(f)
    with open(path + "default_pucch_format3_config.json", 'r') as f:
        pucch_format3_config = json.load(f)
    with open(path + "default_pucch_format4_config.json", 'r') as f:
        pucch_format4_config = json.load(f)
        
    default_UL_config={}
    default_UL_config["UL_waveform_config"] = UL_waveform_config
    default_UL_config["UL_carrier_config"] = UL_carrier_config
    default_UL_config["prach_config"] = prach_config
    default_UL_config["pusch_config"] = pusch_config
    default_UL_config["pucch_format0_config"] = pucch_format0_config
    default_UL_config["pucch_format1_config"] = pucch_format1_config
    default_UL_config["pucch_format2_config"] = pucch_format2_config
    default_UL_config["pucch_format3_config"] = pucch_format3_config
    default_UL_config["pucch_format4_config"] = pucch_format4_config
    return default_UL_config