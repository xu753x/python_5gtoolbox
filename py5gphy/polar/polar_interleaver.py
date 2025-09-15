# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.crc import crc

# 38.212 Table 5.3.1.1-1
pi_il_max_table = [0, 2, 4, 7, 9, 14, 19, 20, 24, 25, 26, 28, 31, 34,
        42, 45, 49, 50, 51, 53, 54, 56, 58, 59, 61, 62, 65, 66, 67, 69,
        70, 71, 72, 76, 77, 81, 82, 83, 87, 88, 89, 91, 93, 95, 98, 101,
        104, 106, 108, 110, 111, 113, 115, 118, 119, 120, 122, 123, 126,
        127, 129, 132, 134, 138, 139, 140, 1, 3, 5, 8, 10, 15, 21, 27, 29,
        32, 35, 43, 46, 52, 55, 57, 60, 63, 68, 73, 78, 84, 90, 92, 94, 96,
        99, 102, 105, 107, 109, 112, 114, 116, 121, 124, 128, 130, 133,
        135, 141, 6, 11, 16, 22, 30, 33, 36, 44, 47, 64, 74, 79, 85, 97,
        100, 103, 117, 125, 131, 136, 142, 12, 17, 23, 37, 48, 75, 80, 86,
        137, 143, 13, 18, 38, 144, 39, 145, 40, 146, 41, 147, 148, 149,
        150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162,
        163]

def interleave(inbits, K):
    """ polar interface following TS38211 5.3.1.1
    input:
        c: 
    """

    # gen pattern
    pitable = get_pattern_table(K)

    return inbits[pitable]

def deinterleave(ck_itrl, K):
    # gen pattern
    depitable = gen_deinterleave_table(K)
    ck = ck_itrl[depitable]
    return ck

def get_pattern_table(K):
    # gen pattern
    kilmax = 164
    assert K <= kilmax

    pitable = [0] * K
    k=0
    for m in range(kilmax):
        if pi_il_max_table[m] >= kilmax - K:
            pitable[k] = pi_il_max_table[m] - (kilmax - K)
            k += 1
    return pitable

def gen_deinterleave_table(K):
    pitable = get_pattern_table(K)
    depitable = [0]*K
    for m,v in enumerate(pitable):
        depitable[v] = m
    return depitable

def gen_crc_interleaver_table(K,crcpoly):
    """ gen interleave table 
        crcidx_matrix: CRC index matrix, -1 means not involved
            each column show that CRC input data indexs that are involed for this bit CRC calculation
    """
    L = crcpoly.size  # CRC size
    crcmatrix = np.zeros((K,L),'i2')
    crcidx_matrix = np.zeros((K,L),'i2')
    for n in range(K):
        inbits = np.zeros(K,'i1')
        inbits[n] = 1
        blkandcrc = crc_encode(inbits, crcpoly)
        crc_bits = blkandcrc[-L:]
        crcmatrix[n,:] = crc_bits
        crcidx_matrix[n,:] = crc_bits*(n+1)   

    crcidx_matrix = crcidx_matrix -1
    return crcmatrix, crcidx_matrix

def gen_polar_pitable(K, crcidx_matrix):
    """ K is data size, K=140 for 38.212 Table 5.3.1.1-1: Interleaving pattern
    """
    CRC_size =  crcidx_matrix.shape[1]
    pitable = -1*np.ones(CRC_size+K,'i2')
    pos = 0
    for n in range(CRC_size):
        #find crc input bit index that is used to calculate CRC bit n
        d1 = crcidx_matrix[:,n]
        d2 = d1[d1 >= 0] # 
        
        #exclude all values that exist in pitabe
        d3=[v for v in d2 if v not in pitable]
        pitable[pos:pos+len(d3)] = d3 #
        pitable[pos+len(d3)] = n + K #crc index
        pos = pos + len(d3) + 1
    
    return pitable

def crc_encode(blk, crcpoly):
    L = crcpoly.size  # CRC size

    A = blk.size  #  input data size

    blkandcrc = np.zeros(A + L, "i1")
    blkandcrc[0:A] = blk

    remainder = blkandcrc[0:L]
    for idx in range(0, A):
        firstbit = remainder[0]
        remainder = np.append(remainder[1:], blkandcrc[idx + L])
        if firstbit:
            remainder = np.bitwise_xor(remainder, crcpoly)

    blkandcrc[A:] = remainder
    return blkandcrc

def gen_CRC24C_init_crc_mask(mask=0):
    """generate crc mask 
       for DCI CRC, 24 '1' is added ahead of inbits, and CRC result need mask with RNTI
       
    """
    crc_mask = crc.nr_crc_encode(np.ones(24,'i1'), '24C', mask)
    return crc_mask

def get_distributed_crc_idx(K,n):
    """check if bit n is CRC bit 
    K is bit size including information bits and CRC bits
    """
    pitable = get_pattern_table(K)
    #CRC bits location is where value >= K-24
    crc_loc = [m for m,v in enumerate(pitable) if v >= K-24]
    if n in crc_loc:
        return crc_loc.index(n)
    else:
        return -1

def get_distributed_crc_bits_locs(K):
    """get 24 CRC bit locations in polar interleaver output
    K is bit size including information bits and CRC bits
    """
    pitable = get_pattern_table(K)
    #CRC bits location is where value >= K-24
    crc_loc = [m for m,v in enumerate(pitable) if v >= K-24]
    if n in crc_loc:
        return crc_loc.index(n)
    else:
        return -1

def interleaved_distributed_CRC24C_decode(inbits, phase, rnti):
    """ calculate CRC24C bit at phase location
    """
    #get CRC 24C poly
    poly_24C = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1],'i1')
    
    #calculate crcidx_matrix, each column x gives bit location that is used to calculate crc bit at x
    crcmatrix, crcidx_matrix = gen_crc_interleaver_table(inbits.size-24, poly_24C)
    
    #get CRC mask: CRC value with [np.ones(24), np.zeros(inbits.size)] 
    data = [1]*24 + list(np.zeros(inbits.size - 24))
    blkandcrc = crc.nr_crc_encode(np.array(data, 'i1'), '24C', rnti)
    crc_mask = blkandcrc[-24:]

    #first deinterleave inbits
    de_int = deinterleave(inbits, inbits.size)

    #get bits locations that is used to calculate CRC bit=phase
    
    line = crcidx_matrix[:,phase]
    locs = line[line>=0]
    
    #add data together with mod 2
    crc_bit = sum(de_int[locs]) % 2

    return (crc_bit + crc_mask[phase]) %2

def verify_interleaved_distributed_CRC24C_decode(dcibits, rnti):
    #add 24 '1' in front of input bits
    bits = [1]*24 + list(dcibits)
    blkandcrc = crc.nr_crc_encode(np.array(bits), '24C', mask = rnti)

    #remove first 24 '1' after crc
    cvec = blkandcrc[24:]
    crc_v = cvec[-24:]
    #interleave cvec
    K = cvec.size
    in_itrl = interleave(cvec, K)

    for n in range(K):
        #check if this is CRC bit
        crc_idx = get_distributed_crc_idx(K,n)
        if crc_idx >= 0:
            #this is CRC bit
            crc_bit = interleaved_distributed_CRC24C_decode(in_itrl, crc_idx, rnti)
            assert crc_bit == crc_v[crc_idx]

if __name__ == "__main__":
    crc_encode(np.array([1,0,0,0]), np.array([1, 0, 0, 1],'i1'))
    #the demo to show how to generate CRC interleaver table
    #CRC 5 and bit length = 8 is used in the demos
    crcmatrix, crcidx_matrix = gen_crc_interleaver_table(8,np.array([1, 0, 0, 1],'i1'))
    pitable = gen_polar_pitable(8,crcidx_matrix)

    #verify pitable generation
    # CRC interleaver table used by NR spec 38.212 Table 5.3.1.1-1: Interleaving pattern
    crcmatrix, crcidx_matrix = gen_crc_interleaver_table(140,np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1],'i1'))
    pitable = gen_polar_pitable(140, crcidx_matrix)
    assert np.array_equal(pitable, pi_il_max_table)

    #verify distributed CRC decode
    dcibits = np.array([0, 0, 1, 1, 0, 0, 0, 1], 'i1')
    rnti = 2345
    verify_interleaved_distributed_CRC24C_decode(dcibits, rnti)

    dcibits = np.array([0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1], 'i1')
    rnti = 0
    verify_interleaved_distributed_CRC24C_decode(dcibits, rnti)

    dcibits = np.array([0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1], 'i1')
    rnti = 45678
    verify_interleaved_distributed_CRC24C_decode(dcibits, rnti)

pass