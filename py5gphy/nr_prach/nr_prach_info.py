# -*- coding:utf-8 -*-

import numpy as np
import pickle

def get_kbar_NRARB(LRA, prach_fRA, carrier_scs):
    """ get kbar following to 38.211 table 6.3.3.2-1
    do not support format 3
    """
    assert LRA in [139, 839]
    assert carrier_scs in [15,30]

    if LRA == 839:
        if carrier_scs == 15:
            NRARB = 6
            kbar = 7
        else:
            NRARB = 3
            kbar = 1
    else:
        #LRA = 139
        if (prach_fRA == 15) and (carrier_scs == 15):
            NRARB = 12
        elif (prach_fRA == 15) and (carrier_scs == 30):
            NRARB = 6
        elif (prach_fRA == 30) and (carrier_scs == 15):
            NRARB = 24
        elif (prach_fRA == 30) and (carrier_scs == 30):
            NRARB = 12
        kbar = 2
    
    return kbar,NRARB

def get_prach_config_info(prach_ConfigurationIndex,duplex_type):
    """ check 38.211 table 6.3.3.2-2 or table 6.3.3.2-3
    to get PRACH configuration info"""
    if duplex_type == "TDD":
        with open('py5gphy/nr_prach/Randomaccessconfigurations_table_FR1_TDD.pickle', 'rb') as handle:
            Randomaccessconfigurations_table = pickle.load(handle)
    else:
        with open('py5gphy/nr_prach/Randomaccessconfigurations_table_FR1_FDD.pickle', 'rb') as handle:
            Randomaccessconfigurations_table = pickle.load(handle)
    
    assert prach_ConfigurationIndex in range(256)

    row = Randomaccessconfigurations_table[prach_ConfigurationIndex]
    assert row[0] == prach_ConfigurationIndex

    prach_info = {}
    prach_info["preamble_formats"] = row[1]
    prach_info["x"] = row[2]
    prach_info["y"] = row[3]
    prach_info["subframe_numbers"] = row[4]
    prach_info["start_symbol"] = row[5]
    prach_info["nprachslot_insubframe"] = row[6]
    prach_info["NRASlot_t"] = row[7]
    prach_info["NRA_dur"] = row[8]

    return prach_info

def get_prach_format_info(preamble_format,msg1_SubcarrierSpacing):
    """ get PRACH preamble format info following to 38.211 table 6.3.3.1-1, 6.3.3.1-2
    not support format 3
    """
    assert preamble_format != '3'
    
    if preamble_format in ['0','1','2','3']:
        LRA = 839
    else:
        LRA = 139
        
    match preamble_format:
        case '0':
            Nu = 24576
            NRA_CP = 3168
        case '1':
            Nu = 2*24576
            NRA_CP = 21024
        case '2':
            Nu = 4*24576
            NRA_CP = 4688
        case 'A1':
            Nu = 2*2048
            NRA_CP = 288
        case 'A2':
            Nu = 4*2048
            NRA_CP = 576
        case 'A3':
            Nu = 6*2048
            NRA_CP = 864
        case 'B1':
            Nu = 2*2048
            NRA_CP = 216
        case 'B2':
            Nu = 4*2048
            NRA_CP = 360
        case 'B3':
            Nu = 6*2048
            NRA_CP = 504
        case 'B4':
            Nu = 12*2048
            NRA_CP = 936
        case 'C0':
            Nu = 2048
            NRA_CP = 1240
        case 'C2':
            Nu = 4*2048
            NRA_CP = 2048

    if msg1_SubcarrierSpacing == 30:
        Nu = Nu // 2
        NRA_CP = NRA_CP // 2        
    return LRA, Nu, NRA_CP
        
def get_PRACH_txinfo(selected_format,ActivePRACHslotinSubframe,nRA_t,start_symbol,nprachslot_insubframe, \
                     msg1_SubcarrierSpacing,Nu,NRA_CP,NRA_dur):
    """ get PRACH transmit info, including:
    (1) pRACH slots in the subframe, (2) PRACH occupied symbols, (3)CP len 
    following to 38.211 5.3.2
    return value:
        nRA_slot: PRACH slot id, 0 or 1
        prach_first_symbol: first prach symbol in the subframe, 0-13 for scs <=15KHz, 0-27 for scs=30khz
        NRA_CP_L: PRACH CP length in 30.72MHz sample rate 
        tRA_start: PRACH start position in the subframe in 30.72MHz sample rate 
    """            
    #below define 14 saymbol samples for 15khz scs and 30khz scs
    #the sample rate is fixed to 30.72MHz
    scs15_symbol_samples = [2208, 2192, 2192, 2192, 2192, 2192, 2192, 2208, 2192, 2192, 2192, 2192, 2192, 2192]
    scs30_symbol_samples = [1112, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096, 1096]

    if selected_format in ['0', '1', '2', '3']:
        NRA_CP_L = NRA_CP
        nRA_slot = 0
        prach_first_symbol = start_symbol
        tRA_start = sum(scs15_symbol_samples[0:prach_first_symbol])
        return nRA_slot, prach_first_symbol, NRA_CP_L,tRA_start
    
    #below for format A0-C2
    #get nRA_slot
    if msg1_SubcarrierSpacing == 15:
        nRA_slot = 0
    elif (msg1_SubcarrierSpacing == 30) and (nprachslot_insubframe == 1):
        nRA_slot = 1
    else:
        nRA_slot = ActivePRACHslotinSubframe
    
    #get prach symbol
    prach_first_symbol = start_symbol + nRA_t*NRA_dur + 14*nRA_slot  
    
    if msg1_SubcarrierSpacing == 15:
        tRA_start = sum(scs15_symbol_samples[0:prach_first_symbol])
        tRA_last = tRA_start + Nu + NRA_CP
    elif msg1_SubcarrierSpacing == 30:
        if prach_first_symbol >= 14:
            tRA_start = sum(scs30_symbol_samples[0:prach_first_symbol-14]) + 30720//2
        else:
            tRA_start = sum(scs30_symbol_samples[0:prach_first_symbol])
        tRA_last = tRA_start + Nu + NRA_CP

    # calculate NRA_CP_L = NRA_CP + n*16
    #for Δf RA ∈ {15,30,60,120}kHz , n is the number of times the interval 
    #[tRA_start, tRA_start+(NRA_u+NRA_CP)*Tc
    #overlaps with either time instance 0 or time instance 0.5 ms in a subframe    
    #get n in NRA_CP_L = NRA_CP + n*16
    n = 0
    if tRA_start == 0:
        n += 1
        if tRA_last >= 15360: #0.5ms
            n += 1
    else:
        if (tRA_start<= 15360) and (tRA_last >= 15360):
            n += 1
    
    NRA_CP_L = NRA_CP + n*16
    return nRA_slot, prach_first_symbol, NRA_CP_L,tRA_start
