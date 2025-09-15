# -*- coding: utf-8 -*-
import numpy as np

from py5gphy.nr_waveform import nr_dl_waveform
from py5gphy.nr_testmodel import nr_testmodel_cfg

### the file is used to generate NR DL test models waveform
###

#select below test model config
scs = 15 #choose 15khz or 30khz
# below is BW:PRB size relation for 15khz scs
# scs15_list = {5:25, 10:52, 15:79, 20:106, 25:133, 30:160, 35:188, 40:216, 45:242, 50:270}
# below is BW:PRB size relation for 30khz scs
#scs30_list = {5:11, 10:24, 15:38, 20:51, 25:65, 30:78, 35:92, 40:106, 45:119, 50:133, 
#                  60:162, 70:189, 80:217, 90:245, 100:273}
#supported BW for 15khz scs: {5, 10, 15, 20, 25, 30, 35, 40, 45, 50}
#supported BW for 30khz scs {11, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100}
BW = 20 #BW in Mhz
Duplex_mode = "FDD" #Duplex_mode in ["TDD", "FDD"]
test_model = "NR-FR1-TM1.1" #test_model in ['NR-FR1-TM1.1','NR-FR1-TM2','NR-FR1-TM2a','NR-FR1-TM3.1','NR-FR1-TM3.1a' ]
ncellid = 1
carrier_frequency_in_mhz = 0 #choose 0 means no phase compensation

###main code####
#generate config
waveform_config, carrier_config, ssb_config, csirs_config_list, \
        coreset_config_list, search_space_list, pdcch_config_list, pdsch_config_list = \
        nr_testmodel_cfg.gen_nr_TM_cfg(scs, BW, Duplex_mode, test_model,ncellid, carrier_frequency_in_mhz)

#generate waveform Duration is 1 radio frame (10 ms) for FDD and 2 radio frames for TDD (20 ms) 
# from 38.141-1 4.9.2.2

#fd_waveform is frequency domain waveform after high-phy processing
# data size = number of subframes * number of slots per subframe * 14symbol * carrier_prbsize * 12

#td_waveform is timedomain waveform after IFFT, add CP, phase compensation
# with samplerate_in_mhz = (scs * (2 ** np.ceil(np.log2(carrier_prb_size*12/0.85))) * 1000)/(10 ** 6)
#data size = number of subframes * samplerate_in_mhz * 10^6

#dl_waveform is timedomain waveform after channel filter(one FIR and N halfband filter)
#sample rate is fixed to 245.76MHz
#data size = number of subframes * 245.76 * 10^6
[nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list] = nr_dl_waveform.gen_dl_channel_list(
    waveform_config,carrier_config,
    ssb_config,pdcch_config_list,
    search_space_list,coreset_config_list,
    csirs_config_list,pdsch_config_list
)
fd_waveform, td_waveform, dl_waveform = nr_dl_waveform.gen_dl_waveform(waveform_config, carrier_config,  
                nrSSB_list, nrPdsch_list, nrCSIRS_list, nrPDCCH_list )

pass