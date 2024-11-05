# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.nr_ssb import nr_ssb
from py5gphy.nr_lowphy import dl_lowphy_process
from py5gphy.common import nr_slot
from py5gphy.nr_pdsch import nr_pdsch
from py5gphy.nr_pdcch import nr_pdcch
from py5gphy.nr_pdcch import nr_searchspace
from py5gphy.nr_csirs import nr_csirs

def gen_dl_waveform(waveform_config, carrier_config, ssb_config, 
                    pdcch_config_list, search_space_list, coreset_config_list, 
                    csirs_config_list, pdsch_config_list):
    """ generate DL frequency domain and time domain waveform
    fd_waveform, td_waveform,dl_waveform = gen_dl_waveform()
    input:
        waveform_config:
        carrier_config:
        ssb_config:
    output:
        fd_waveform: frequency waveform, num_of_ant X slot-size array
        td_waveform: time waveform after IFT, add CP, phase compensation, num_of_ant X slot-size array
                    sample rate = IFFT size * SCS
        dl_waveform: time domain waveform after channel filter and interpolation, sample rate is defind in DL_waveform_config
    """
    #get info from waveform config
    samplerate_in_mhz = waveform_config["samplerate_in_mhz"]
    numofsubframes = waveform_config["numofsubframes"]
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

    numofslots = int(numofsubframes * scs / 15)

    #create object lists
    nrSSB_list = []
    if ssb_config['enable'] == "True":
        nrSSB = nr_ssb.NrSSB(carrier_config, ssb_config)
        nrSSB_list.append(nrSSB)


    nrPdsch_list = []
    for pdsch_config in pdsch_config_list:
        if pdsch_config['enable'] == "True":
            nrPdsch = nr_pdsch.Pdsch(pdsch_config, carrier_config)
            nrPdsch_list.append(nrPdsch)
    
    nrCSIRS_list = []
    for csirs_config in csirs_config_list:
        if csirs_config['enable'] == "True":
            nrCSIRS = nr_csirs.NrCSIRS(carrier_config, csirs_config)
            nrCSIRS_list.append(nrCSIRS)

    nrSearchSpace_list = []
    for search_space_config in search_space_list:
        if search_space_config['enable'] == "True":
            #find coreset config with coresetid = controlResourceSetId
            controlResourceSetId = search_space_config["controlResourceSetId"]
            sel_coreset_config = None
            for coreset_config in coreset_config_list:
                coreset_id = coreset_config["coreset_id"]
                if coreset_id == controlResourceSetId:
                    sel_coreset_config = coreset_config
                    break
            if sel_coreset_config == None:
                assert 0

            nrSearchSpace = nr_searchspace.NrSearchSpace(carrier_config, search_space_config, sel_coreset_config)
            nrSearchSpace_list.append(nrSearchSpace)

    nrPDCCH_list = []
    for pdcch_config in pdcch_config_list:
        if pdcch_config['enable'] == "True":
            #find search space the PDCCH belong to
            pdcch_searchSpaceId = pdcch_config["searchSpaceId"]
            sel_nrSearchSpace = None
            for nrSearchSpace in nrSearchSpace_list:
                controlResourceSetId = nrSearchSpace.search_space_config["controlResourceSetId"]
                if pdcch_searchSpaceId == controlResourceSetId:
                    sel_nrSearchSpace = nrSearchSpace
                    break
            if sel_nrSearchSpace == None:
                assert 0

            nrPDCCH = nr_pdcch.Pdcch(pdcch_config, nrSearchSpace) 
            nrPDCCH_list.append(nrPDCCH)
    
    #init
    fd_slotsize = carrier_prbsize*12*14
    fd_waveform = np.zeros((num_of_ant, numofslots*fd_slotsize), 'c8')

    td_slotsize = int(sample_rate_in_hz / 1000*15/scs)
    td_waveform = np.zeros((num_of_ant, numofslots*td_slotsize), 'c8')

    for idx in range(numofslots):
        fd_slot_data, RE_usage_inslot = nr_slot.init_fd_slot(num_of_ant, carrier_prbsize)
        
        #get sfn and slot
        sfn = startSFN + int((startslot+idx)//(scs/15*10))
        slot = (startslot+idx) % int(scs/15*10)

        for nrSSB in nrSSB_list:
            fd_slot_data, RE_usage_inslot = nrSSB.process(fd_slot_data, RE_usage_inslot, sfn,slot)

        for nrCSIRS in nrCSIRS_list:
            fd_slot_data, RE_usage_inslot = nrCSIRS.process(fd_slot_data, RE_usage_inslot,sfn,slot)

        #for nrSearchSpace in nrSearchSpace_list:
        #    RE_usage_inslot = nrSearchSpace.process(RE_usage_inslot, sfn, slot)
        
        for nrPDCCH in nrPDCCH_list:
            fd_slot_data, RE_usage_inslot = nrPDCCH.process(fd_slot_data, RE_usage_inslot,sfn,slot)

        for nrPdsch in nrPdsch_list:
            fd_slot_data, RE_usage_inslot = nrPdsch.process(fd_slot_data, RE_usage_inslot,slot)

        #save final fd_slot_data to fd_waveform
        fd_waveform[:, idx*fd_slotsize:(idx+1)*fd_slotsize] = fd_slot_data

        ## start DL low phy processing for the slot
        td_slot = dl_lowphy_process.DL_low_phy(fd_slot_data, carrier_config, sample_rate_in_hz)
        
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
    dl_waveform = dl_lowphy_process.channel_filter(td_waveform, carrier_config, sample_rate_in_hz)
    
    return fd_waveform, td_waveform, dl_waveform


if __name__ == "__main__":
    print("test nr DL waveform")
    from tests.nr_waveform import test_nr_dl_waveform
    file_lists = test_nr_dl_waveform.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dl_waveform.test_DL_waveform(filename)
        
    #this test is passed
    print("test nr PDSCH only waveform")
    from tests.nr_waveform import test_pdsch_only
    file_lists = test_pdsch_only.get_pdsch_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_pdsch_only.test_nr_pdsch_only(filename)

    #this test is passed
    print("test nr PDCCH only waveform")
    from tests.nr_waveform import test_pdcch_only
    file_lists = test_pdcch_only.get_pdcch_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_pdcch_only.test_nr_pdcch_only(filename)

    #this test is passed
    print("test nr CSI RS only waveform")
    from tests.nr_waveform import test_csirs_only
    file_lists = test_csirs_only.get_csirs_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_csirs_only.test_nr_csirs_only(filename)
    
    #this test is passed
    print("test nr SSB only waveform")
    from tests.nr_waveform import test_dl_ssb_only
    file_lists = test_dl_ssb_only.get_ssb_highphy_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_dl_ssb_only.test_dl_ssb_only(filename)

    