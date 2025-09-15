# -*- coding:utf-8 -*-

import numpy as np
import math
from scipy.signal import upfirdn
from scipy.signal import remez

from py5gphy.nr_prach import nr_prach

def gen_prach_waveform(waveform_config, carrier_config, prach_config,prach_parameters):
    """ generate PRACH time domain waveform
    td_waveform = gen_prach_waveform()

    """
    #get info from waveform config
    samplerate_in_mhz = waveform_config["samplerate_in_mhz"]
    numofslots = waveform_config["numofslots"]
    startSFN = waveform_config["startSFN"]
    assert samplerate_in_mhz in [7.68, 15.36, 30.72, 61.44, 122.88, 245.76]
    sample_rate_in_hz = int(samplerate_in_mhz*(10**6))
    sample_size_in_one_sfn = int(sample_rate_in_hz/100) #
        
    #number of system frame
    numof_sfn = math.ceil(numofslots*carrier_config["scs"]/15/10)

    nrprach = nr_prach.Prach(carrier_config, prach_config, prach_parameters)
    td_waveform = np.zeros((1, numof_sfn*sample_size_in_one_sfn), 'c8')
    prach_data_list = []
    for m in range(numof_sfn):
        sfn = m + startSFN 

        prach_waveform, prach_data, prach_active = nrprach.process(sfn)
        
        #both waveform and prach_data are time domain data with sample rate = 30.72MHz
        #save prach_data if not empty
        if prach_active:
            if prach_data_list:
                prach_data_list = np.vstack((prach_data_list,prach_data))
            else:
                prach_data_list = np.zeros((1,prach_data.size),'c8')
                prach_data_list[0,:] = prach_data
        
        #upsample 30.72MHz waveform to waveform_config sample rate and then save to td_waveform
        oversample_rate = int(samplerate_in_mhz/30.72)
        assert oversample_rate > 0
        reps = int(np.log2(oversample_rate))

        outd = _upsample(prach_waveform,reps)

        td_waveform[0,m*sample_size_in_one_sfn:(m+1)*sample_size_in_one_sfn] = outd

    
    return td_waveform, prach_data_list

def _upsample(prach_waveform,reps):
    #generate half band filter
    #A half band filter can be designed using the Parks-McCellen equilripple design methods by having equal offsets of 
    # the pass-band and stop-band (from filter specification) and equal weights of the pass-band and stop-band
    numtaps = 55 #for half band filter, (numtaps+1) must be divisble by 4
    Fpass = 0.21 #should be less than 0.25
    halfband_filtercoeff = remez(numtaps, [0, Fpass, 0.5-Fpass, 0.5], [1,0])

    outd = prach_waveform
    input_size = outd.size
    for m in range(reps):
        outd = upfirdn(halfband_filtercoeff, outd, up=2)
        offset = int(halfband_filtercoeff.size // 2 )
        outd = outd[offset : offset + 2*input_size]
        input_size *= 2
    
    return outd

if __name__ == "__main__":
    print("test nr PRACH waveform")

    from tests.nr_waveform import test_nr_prach_waveform
    file_lists = test_nr_prach_waveform.get_nr_prach_testvector()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_prach_waveform.test_nr_prach_waveform(filename)