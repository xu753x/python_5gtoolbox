# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.crc import crc
from py5gphy.polar import nr_polar_encoder
from py5gphy.polar import nr_polar_ratematch

def nrDCIEncode(dcibits, rnti, E):
    """ DCI bit processing following to 38.212 7.3.2-7.3.4
    complete CRC, polar encode, polar rate matching
    """
    # CRC attachment, Section 7.3.2
    #add 24 '1' in front of input bits
    bits = [1]*24 + list(dcibits)
    blkandcrc = crc.nr_crc_encode(np.array(bits), '24C', mask = rnti)

    #remove first 24 '1' after crc
    cvec = blkandcrc[24:]

    #Channel coding, Section 7.3.3
    K = cvec.shape[0]
    nMax = 9
    iIL = 1
    encOut = nr_polar_encoder.encode_polar(cvec, E, nMax, iIL)

    # Rate matching, Section 7.3.4, [1]
    iBIL = 0
    fe = nr_polar_ratematch.ratematch_polar(encOut, K, E, iBIL)

    return fe

if __name__ == "__main__":
    print("test DCI encoder")
    from tests.nr_pdcch import test_nr_dci_encoder
    file_lists = test_nr_dci_encoder.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_nr_dci_encoder.test_nr_dci_encoder(filename)
