# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_lowphy import tx_lowphy_process
from py5gphy.common import nr_slot
from py5gphy.nr_pusch import nr_pusch
from py5gphy.nr_pucch import nr_pucch_format0
from py5gphy.nr_pucch import nr_pucch_format1
from py5gphy.nr_pucch import nr_pucch_format2
from py5gphy.nr_pucch import nr_pucch_format3
from py5gphy.nr_pucch import nr_pucch_format4
from py5gphy.nr_srs import nr_srs

def gen_ul_waveform(waveform_config, carrier_config, 
                    nrPusch_list=[], nrSrs_list=[], nrPucchFormat0_list=[], nrPucchFormat1_list=[],nrPucchFormat2_list=[],nrPucchFormat3_list=[],nrPucchFormat4_list=[]):
    """ generate UL frequency domain and time domain waveform
    fd_waveform, td_waveform,ul_waveform = gen_ul_waveform()
    input:
        
    output:
        fd_waveform: frequency waveform, num_of_ant X slot-size array
        td_waveform: time waveform after IFFT, add CP, phase compensation, num_of_ant X slot-size array
                    sample rate = IFFT size * SCS
        ul_waveform: time domain waveform after channel filter and interpolation, sample rate is defind in waveform_config
    """
    #get info from waveform config
    samplerate_in_mhz = waveform_config["samplerate_in_mhz"]
    numofslots = waveform_config["numofslots"]
    startSFN = waveform_config["startSFN"]
    startslot = waveform_config["startslot"]
    assert samplerate_in_mhz in [7.68, 15.36, 30.72, 61.44, 122.88, 245.76]
    sample_rate_in_hz = int(samplerate_in_mhz*(10**6))

    #get info from carrier config
    num_of_ant = carrier_config["num_of_ant"]
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
        
    #init
    fd_slotsize = carrier_prbsize*12*14
    fd_waveform = np.zeros((num_of_ant, numofslots*fd_slotsize), 'c8')

    ifftsize = nr_slot.get_FFT_IFFT_size(carrier_prbsize)
    td_waveform_sample_rate_in_hz = ifftsize * scs * 1000

    td_slotsize = int(ifftsize * 15)
    td_waveform = np.zeros((num_of_ant, numofslots*td_slotsize), 'c8')

    for idx in range(numofslots):
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prbsize)
        
        #get sfn and slot
        sfn = startSFN + int((startslot+idx)//(scs/15*10))
        slot = (startslot+idx) % int(scs/15*10)

        for nrPusch in nrPusch_list:
            fd_slot_data, RE_usage_inslot = nrPusch.process(fd_slot_data, RE_usage_inslot, slot)
        
        for nrPucchFormat0 in nrPucchFormat0_list:
            fd_slot_data, RE_usage_inslot = nrPucchFormat0.process(fd_slot_data, RE_usage_inslot, sfn,slot)
        
        for nrPucchFormat1 in nrPucchFormat1_list:
            fd_slot_data, RE_usage_inslot = nrPucchFormat1.process(fd_slot_data, RE_usage_inslot, sfn,slot)
        
        for nrPucchFormat2 in nrPucchFormat2_list:
            fd_slot_data, RE_usage_inslot = nrPucchFormat2.process(fd_slot_data, RE_usage_inslot, sfn,slot)
        
        for nrPucchFormat3 in nrPucchFormat3_list:
            fd_slot_data, RE_usage_inslot = nrPucchFormat3.process(fd_slot_data, RE_usage_inslot, sfn,slot)
        
        for nrPucchFormat4 in nrPucchFormat4_list:
            fd_slot_data, RE_usage_inslot = nrPucchFormat4.process(fd_slot_data, RE_usage_inslot, sfn,slot)
        
        for nrSrs in nrSrs_list:
            fd_slot_data, RE_usage_inslot = nrSrs.process(fd_slot_data, RE_usage_inslot, sfn,slot)

        #save final fd_slot_data to fd_waveform
        fd_waveform[:, idx*fd_slotsize:(idx+1)*fd_slotsize] = fd_slot_data

        ## start DL low phy processing for the slot
        td_slot = tx_lowphy_process.Tx_low_phy(fd_slot_data, carrier_config)
        
        # slot level phase compensation
        if central_freq_in_hz:
            #carrier_frequency_in_mhz * 1e3 is usually even value, so slot_phase is always 1. we cam omit slot level phase compensation
            if scs == 15:
                # one slot = 1ms
                slot_phase = np.exp(-1j * 2 * np.pi * central_freq_in_hz / 1e3 * idx)
            else:
                # one slot = 0.5ms
                slot_phase = np.exp(-1j * 2 * np.pi * central_freq_in_hz / 1e3 / 2 * idx)
            td_slot = td_slot*slot_phase
        
        td_waveform[:, idx*td_slotsize:(idx+1)*td_slotsize] = td_slot

    ## start DUC processing,channel filter and oversample, output sample rate is fixed to 245.76MHz
    #oversample_rate must be 1,2,4,8,..
    ul_waveform = tx_lowphy_process.channel_filter(td_waveform, carrier_config, sample_rate_in_hz)
    
    return fd_waveform, td_waveform, ul_waveform

def gen_ul_channel_list(waveform_config, carrier_config, pusch_config_list=[], srs_config_list=[],
                    pucch_format0_config_list=[],pucch_format1_config_list=[],pucch_format2_config_list=[],
                    pucch_format3_config_list=[],pucch_format4_config_list=[]):
    #get info from waveform config
    samplerate_in_mhz = waveform_config["samplerate_in_mhz"]
    numofslots = waveform_config["numofslots"]
    startSFN = waveform_config["startSFN"]
    startslot = waveform_config["startslot"]
    assert samplerate_in_mhz in [7.68, 15.36, 30.72, 61.44, 122.88, 245.76]
    sample_rate_in_hz = int(samplerate_in_mhz*(10**6))

    #get info from carrier config
    num_of_ant = carrier_config["num_of_ant"]
    central_freq_in_hz = int(carrier_config["carrier_frequency_in_mhz"] * (10**6))
    scs = carrier_config['scs']
    BW = carrier_config['BW']
    carrier_prbsize = nr_slot.get_carrier_prb_size(scs, BW)
    
    #create object lists
    nrPusch_list = []
    for pusch_config in pusch_config_list:
        if pusch_config['enable'] == "True":
            nrPusch = nr_pusch.NrPUSCH(carrier_config,pusch_config)
            nrPusch_list.append(nrPusch)
    
    nrSrs_list = []
    for srs_config in srs_config_list:
        if srs_config['enable'] == "True":
            nrSrs = nr_srs.NrSRS(carrier_config,srs_config)
            nrSrs_list.append(nrSrs)
    
    nrPucchFormat0_list = []
    for pucch_format0_config in pucch_format0_config_list:
        if pucch_format0_config['enable'] == "True":
            nrPucchFormat0 = nr_pucch_format0.NrPUCCHFormat0(carrier_config,pucch_format0_config)
            nrPucchFormat0_list.append(nrPucchFormat0)
    
    nrPucchFormat1_list = []
    for pucch_format1_config in pucch_format1_config_list:
        if pucch_format1_config['enable'] == "True":
            nrPucchFormat1 = nr_pucch_format1.NrPUCCHFormat1(carrier_config,pucch_format1_config)
            nrPucchFormat1_list.append(nrPucchFormat1)
    
    nrPucchFormat2_list = []
    for pucch_format2_config in pucch_format2_config_list:
        if pucch_format2_config['enable'] == "True":
            nrPucchFormat2 = nr_pucch_format2.NrPUCCHFormat2(carrier_config,pucch_format2_config)
            nrPucchFormat2_list.append(nrPucchFormat2)
    
    nrPucchFormat3_list = []
    for pucch_format3_config in pucch_format3_config_list:
        if pucch_format3_config['enable'] == "True":
            nrPucchFormat3 = nr_pucch_format3.NrPUCCHFormat3(carrier_config,pucch_format3_config)
            nrPucchFormat3_list.append(nrPucchFormat3)
    
    nrPucchFormat4_list = []
    for pucch_format4_config in pucch_format4_config_list:
        if pucch_format4_config['enable'] == "True":
            nrPucchFormat4 = nr_pucch_format4.NrPUCCHFormat4(carrier_config,pucch_format4_config)
            nrPucchFormat4_list.append(nrPucchFormat4)

    return nrPusch_list, nrSrs_list, nrPucchFormat0_list, nrPucchFormat1_list,nrPucchFormat2_list,nrPucchFormat3_list,nrPucchFormat4_list

if __name__ == "__main__":
    print("test nr UL waveform")

    #this test is passed
    print("test nr PUCCH format 4 only waveform")
    from tests.nr_waveform import test_nr_pucchformat4_only
    file_lists = test_nr_pucchformat4_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat4_only.test_nr_pucchformat4_only(filename)

    #this test is passed
    print("test nr PUCCH format 3 only waveform")
    from tests.nr_waveform import test_nr_pucchformat3_only
    file_lists = test_nr_pucchformat3_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat3_only.test_nr_pucchformat3_only(filename)

    #this test is passed
    print("test nr PUCCH format 2 only waveform")
    from tests.nr_waveform import test_nr_pucchformat2_only
    file_lists = test_nr_pucchformat2_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat2_only.test_nr_pucchformat2_only(filename)

    #this test is passed
    print("test nr PUCCH format 1 only waveform")
    from tests.nr_waveform import test_nr_pucchformat1_only
    file_lists = test_nr_pucchformat1_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat1_only.test_nr_pucchformat1_only(filename)

    #this test is passed
    print("test nr PUCCH format 0 only waveform")
    from tests.nr_waveform import test_nr_pucchformat0_only
    file_lists = test_nr_pucchformat0_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pucchformat0_only.test_nr_pucchformat0_only(filename)

    #this test is passed
    print("test nr SRS only waveform")
    from tests.nr_waveform import test_srs_only
    file_lists = test_srs_only.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_srs_only.test_nr_srs_only(filename)

    #this test is passed
    print("test nr PUSCH only waveform")
    from tests.nr_waveform import test_pusch_only
    file_lists = test_pusch_only.get_pusch_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_pusch_only.test_nr_pusch_only(filename)