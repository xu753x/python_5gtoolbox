# -*- coding:utf-8 -*-
import numpy as np
import math

def nrModulate(inbits, modtype):
    """modulation refer to 38.211 5.1 Modulation mapper
    mod_data = nrModulate(inbits, modtype)
    """
    modtype = modtype.lower()
    assert modtype in ["pi/2-bpsk", "bpsk", "qpsk", "16qam", "64qam", "256qam", "1024qam"], "modulation type is incorrect"

    b = inbits.astype('f') #convert to float32
    N = b.size
    
    if modtype == "bpsk":
        mod_data = ((1-2*b) + 1j*(1-2*b))/math.sqrt(2)         
    elif modtype == "pi/2-bpsk":
        d1 = ((1-2*b) + 1j*(1-2*b))/math.sqrt(2)
        d2 = ((2*b-1) + 1j*(1-2*b))/math.sqrt(2)
        mod_data = d1
        mod_data[1::2] = d2[1::2]        
    elif modtype == "qpsk":
        assert N % 2 == 0, "length of databits must be multiple of 2"
        mod_data = ((1-2*b[0::2]) + 1j*(1-2*b[1::2]))/math.sqrt(2)        
    elif modtype == "16qam":
        assert N % 4 == 0, "length of databits must be multiple of 4"
        mod_data = ((1-2*b[0::4]) * (2 - (1-2*b[2::4])) 
               + 1j*(1-2*b[1::4]) * (2 - (1-2*b[3::4]))
                    )/math.sqrt(10)                
    elif modtype == "64qam":
        assert N % 6 == 0, "length of databits must be multiple of 6"
        mod_data = ((1-2*b[0::6]) * (4 - (1-2*b[2::6])*(2-(1-2*b[4::6]))) 
               + 1j*(1-2*b[1::6]) * (4 - (1-2*b[3::6])*(2-(1-2*b[5::6])))
                    )/math.sqrt(42)        
    elif modtype == "256qam":
        assert N % 8 == 0, "length of databits must be multiple of 8"
        mod_data = ((1-2*b[0::8]) * (8 - (1-2*b[2::8])*(4 - (1-2*b[4::8])*(2-(1-2*b[6::8]))))
               + 1j*(1-2*b[1::8]) * (8 - (1-2*b[3::8])*(4 - (1-2*b[5::8])*(2-(1-2*b[7::8]))))
                    )/math.sqrt(170)
    elif modtype == "1024qam":
        assert N % 10 == 0, "length of databits must be multiple of 10"
        mod_data = ((1-2*b[0::10]) * (16 - (1-2*b[2::10])*(8 - (1-2*b[4::10])*(4 - (1-2*b[6::10])*(2-(1-2*b[8::10])))))
               + 1j*(1-2*b[1::10]) * (16 - (1-2*b[3::10])*(8 - (1-2*b[5::10])*(4 - (1-2*b[7::10])*(2-(1-2*b[9::10])))))
                    )/math.sqrt(682)
    return mod_data


if __name__ == "__main__":
    from scipy import io
    import os
    
    print("test nr modulation")
    from tests.common import test_nrModulation
    file_lists = test_nrModulation.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nrModulation.test_nr_modulation(filename)
