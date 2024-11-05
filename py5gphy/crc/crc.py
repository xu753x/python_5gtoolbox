# -*- coding:utf-8 -*-
import numpy as np

def nr_crc_encode(blk, poly, mask=0):
    """blkandcrc = nr_crc_encode(blk,poly,mask=0)
    calculate CRC for input blk and return a copy of blk and CRC parity bits.
      blk: 1xA int type 0/1 bit array
      poly: ('6','11','16','24A','24B','24C')
      mask: integer value usually RNTI, to xor mask CRC bits. mask value is applied to CRC bits MSB first
           if mask value is greater than CRC bit length, then LSB 'L' bits are used for mask
      blkandcrc: output 1x(A+L) int8 type 0/1 bit array
      example:
      blkandcrc = nr_crc_encode(np.array([1,1,1,1,0,0,0,0]), '16', 12345)
    """
    # make sure all input data value are 0 or 1
    assert (not np.any(np.nonzero(blk < 0))) and (
        not np.any(np.nonzero(blk > 1))
    )

    crcpoly = _get_crcpoly(poly)
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

    if mask:
        bitseq = [mask >> (23 - i) & 1 for i in range(0, 24)]  #'MSB first
        bitseq = bitseq[24 - L : 24]  # select L LSB bits
        remainder = np.bitwise_xor(remainder, bitseq)

    blkandcrc[A:] = remainder
    return blkandcrc

def nr_crc_decode(blkandcrc, poly, mask=0):
    """[blk, err] = nr_crc_decode(blk,poly,mask=0)
    check CRC error for input blk with associated CRC bits, and return a copy of blk and CRC error .
      blkandcrc: 1x(A+L) int type 0/1 bit array, data + CRC bits
      poly: ('6','11','16','24A','24B','24C')
      mask: integer value usually RNTI, to xor mask CRC bits. mask value is applied to CRC bits MSB first
           if mask value is greater than CRC bit length, then LSB 'L' bits are used for mask
      blk: output 1xA int8 type 0/1 bit array
      err: 0: no error, 1:error
      example:
      blk, err = nr_crc_decode(np.array([1,1,1,1,0,0,0,0]), '16', 12345)
    """
    # make sure all input data value are 0 or 1
    assert (not np.any(np.nonzero(blkandcrc < 0))) and (
        not np.any(np.nonzero(blkandcrc > 1))
    )

    crcpoly = _get_crcpoly(poly)
    L = crcpoly.size  # CRC size

    A = blkandcrc.size - L  # input data size

    blk = np.zeros(A, "i1")
    blk = blkandcrc[0:A]

    remainder = blkandcrc[0:L]
    for idx in range(0, A):
        firstbit = remainder[0]
        remainder = np.append(remainder[1:], blkandcrc[idx + L])
        if firstbit:
            remainder = np.bitwise_xor(remainder, crcpoly)

    if mask:
        bitseq = [mask >> (23 - i) & 1 for i in range(0, 24)]  #'MSB first
        bitseq = bitseq[24 - L : 24]  # select L LSB bits
        remainder = np.bitwise_xor(remainder, bitseq)

    # remainder should be all zero if CRC pass
    if np.count_nonzero(remainder):
        err = 1
    else:
        err = 0

    return blk, err

def _get_crcpoly(poly):
    """return CRC polynomial"""

    # fmt: off
    match poly.upper():
        case '6':
            crcpoly = np.array([1, 0, 0, 0, 0, 1],'i1')
        case '11':
            crcpoly = np.array([1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],'i1')
        case '16':
            crcpoly = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],'i1')
        case '24A':
            crcpoly = np.array([1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1],'i1')
        case '24B':
            crcpoly = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1],'i1')
        case '24C':
            crcpoly = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1],'i1')
        case _:
            assert False
    # fmt: on

    return crcpoly

if __name__ == "__main__":
    print("test crc encode")
    from tests.crc import test_crc
    testlists = [([1,1,1,1], 0, [1, 1, 1, 1, 0, 0, 1, 0, 1, 0]),
     ([1,0,1,1,0,1,1,0,1], 0, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0]),
     ([1,0,1,1,0,1,1,0,1], 1, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1]),
     ([1,0,1,1,0,1,1,0,1], 45678, [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0]),
     ([1,0,1,1,0,1,1,0], 200, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc6(blk, mask, expected)
    
    testlists = [([1, 0, 1, 1], 0, [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1]),
     ([1, 0, 1, 1], 12345, [1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 24, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc11(blk, mask, expected)

    testlists = [([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 12345, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc16(blk, mask, expected)
    
    testlists = [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc24A(blk, mask, expected)
    
    testlists = [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc24B(blk, mask, expected)
    
    testlists = [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1]),
     ]
    for blk, mask, expected in testlists:
        test_crc.test_crc24C(blk, mask, expected)
    
