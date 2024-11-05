# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nrModulation
import math

def nr_pusch_process(g_seq, rnti, nID, Qm, num_of_layers,nTransPrecode, RBSize, nNrOfAntennaPorts, precoding_matrix):
    """ 38.211 6.3.1
    """
    G = g_seq.shape[0] #size of g_seq

    #6.3.1.1 scrambling
    cinit = rnti *(2**15) + nID
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, G)
    scrambled = np.zeros(G,'i1')
    for m in range(G):
        if g_seq[m] == -1: # x UCI placeholder bits
            scrambled[m] = 1
        else:
            if g_seq[m] == -2: #y UCI placeholder bits
                scrambled[m] = scrambled[m-1]
            else:
                scrambled[m] = (g_seq[m] + prbs_seq[m]) % 2
    
    #6.3.1.2 Modulation
    assert Qm in [1, 2, 4, 6, 8]
    mod_table = {1: 'pi/2-bpsk', 2:'QPSK', 4:'16QAM', 6:'64QAM', 8:'256QAM'}
    mod_data = nrModulation.nrModulate(scrambled, mod_table[Qm])

    #6.3.1.3 Layer mapping
    N = mod_data.shape[0]
    assert (N % num_of_layers) == 0

    d1 = mod_data.reshape(N // num_of_layers, num_of_layers)
    xi = d1.T

    #6.3.1.4 Transform precoding
    if nTransPrecode == 0: 
        #If transform precoding is not enabled
        yi = xi
    else:
        #transform precoding is enabled and no PTRS
        assert num_of_layers == 1
        MPUSCHSC = RBSize * 12
        numsym = int(xi.size // MPUSCHSC)
        assert xi.size % MPUSCHSC == 0
        yi = np.zeros((1,xi.shape[1]), 'c8')
        offset = 0
        for sym in range(numsym):
            fftin = xi[0,sym*MPUSCHSC : (sym+1)*MPUSCHSC]
            fftout = np.fft.fft(fftin) / math.sqrt(MPUSCHSC)
            yi[0,sym*MPUSCHSC : (sym+1)*MPUSCHSC] = fftout
    
    #6.3.1.5 Precoding
    precoded = np.zeros((nNrOfAntennaPorts, yi.shape[1]), 'c8')
    precoded = precoding_matrix @ yi
    
    return precoded

if __name__ == "__main__":
    print("test nr PUSCH process from scrambling to precoding")
    from tests.nr_pusch import test_nr_pusch_process
    file_lists = test_nr_pusch_process.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_pusch_process.test_nr_pusch_process(filename)