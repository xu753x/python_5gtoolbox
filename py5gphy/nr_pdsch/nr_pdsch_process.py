# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nrModulation

def nr_pdsch_encode(g_seq, rnti, nID, Qm, num_of_layers, precoding_matrix, num_of_ant):
    """ PDSCH scrambling, modulation, layer mapping, precoding by 38.211 7.3.1
    support only one codeword
    pdsch_syms = nr_pdsch_encode()
    input:

    """
    G = g_seq.shape[0] #size of g_seq

    #7.3.1.1 scrambling
    cinit = rnti *(2**15) + nID
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, G)
    scrambled = (g_seq + prbs_seq) % 2

    #7.3.1.2 Modulation
    assert Qm in [2, 4, 6, 8]
    mod_table = {2:'QPSK', 4:'16QAM', 6:'64QAM', 8:'256QAM'}
    mod_data = nrModulation.nrModulate(scrambled, mod_table[Qm])

    #7.3.1.3 Layer mapping
    N = mod_data.shape[0]
    assert (N % num_of_layers) == 0

    d1 = mod_data.reshape(N // num_of_layers, num_of_layers)
    xi = d1.T

    #precoding
    precoded = np.zeros((num_of_ant, xi.shape[1]), 'c8')
    if not precoding_matrix:
        precoded[0:num_of_layers,:] = xi
        return precoded
    
    precoding_matrix = np.array(precoding_matrix)
    sel_pmi = precoding_matrix[0:num_of_ant,0:num_of_layers]
    precoded = sel_pmi @ xi

    return precoded

if __name__ == "__main__":
    print("test nr pdsch encoder")
    precoding_matrix = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    Qmtable = {'QPSK':2, '16QAM':4, '64QAM':6, '256QAM':8}
    from tests.nr_pdsch import nr_pdsch_testvectors
    from scipy import io
    import os
    curpath = "tests/nr_pdsch/testvectors"
    count = 1
    for f in os.listdir(curpath):
            if f.endswith(".mat") and f.startswith("nrPDSCH_testvec"):
                print("count= {}, filename= {}".format(count, f))
                count += 1
                matfile = io.loadmat(curpath + '/' + f)
                trblk_out,RM_out,layermap_out, fd_slot_data, waveform, pdsch_tvcfg = \
                    nr_pdsch_testvectors.read_dlsch_testvec_matfile(matfile)
                #read data from mat file16
                modulation = pdsch_tvcfg['Modulation']
                nlayers = pdsch_tvcfg['NumLayers']
                ncellid = 1
                rnti = pdsch_tvcfg['RNTI']
                
                blk_num = RM_out.shape[0]
                for m in range(blk_num):
                    inbits = RM_out[m,:]
                    precoded = nr_pdsch_encode(inbits, rnti, ncellid, Qmtable[modulation], \
                                           nlayers, precoding_matrix, nlayers)
                    outsym_ref = layermap_out[m*nlayers:(m+1)*nlayers,:]
                    assert np.allclose(precoded, outsym_ref,atol=1e-5)

                aaaa=1
