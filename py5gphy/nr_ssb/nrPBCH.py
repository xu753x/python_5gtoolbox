# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nrModulation

def nrPBCHencode(rm_bitseq, NcellID, iSSB):
    """ PBCH scrambling and mofulation, refer to 38.211 7.3.3.1 and 7.3.3.2
    mod_data = nrPBCH(rm_bitseq, NcellID, v)
    input:
        rm_bitseq: 864 bits sequence after BCH rate match
        NcellID: physical layer cell identity (0...1007)
        iSSB is the 2 (LMax=4) or 3(LMax=8) LSBs (0...7) of the SS/PBCH block index
    output:
        mod_data: 432 length of modulated complex data
    """
    E = 864
    prbs_seq = nrPRBS.gen_nrPRBS(NcellID,E*(iSSB+1))
    sel_seq = prbs_seq[E*iSSB : E*(iSSB+1)]
    scrambled = (rm_bitseq + sel_seq) % 2

    # QPSK modulation
    mod_data = nrModulation.nrModulate(scrambled, 'QPSK')
    return mod_data

if __name__ == "__main__":
    print("test nr PBCH")
    from tests.nr_ssb import test_nrPBCH
    file_lists = test_nrPBCH.get_pbch_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nrPBCH.test_nrPBCH(filename)