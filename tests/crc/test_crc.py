# -*- coding: utf-8 -*-
import numpy as np
import pytest

from py5gphy.crc import crc


# fmt: off
@pytest.mark.parametrize(
    "blk, mask, expected",
    [([1,1,1,1], 0, [1, 1, 1, 1, 0, 0, 1, 0, 1, 0]),
     ([1,0,1,1,0,1,1,0,1], 0, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0]),
     ([1,0,1,1,0,1,1,0,1], 1, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1]),
     ([1,0,1,1,0,1,1,0,1], 45678, [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0]),
     ([1,0,1,1,0,1,1,0], 200, [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1]),
     ],
)
def test_crc6(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '6', mask), np.array(expected,'i1'))
    
    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '6', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '6', mask)
    assert err == 1

@pytest.mark.parametrize(
    "blk, mask, expected",
    [([1, 0, 1, 1], 0, [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1]),
     ([1, 0, 1, 1], 12345, [1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 24, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0]),
     ([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1]),
     ],
)
def test_crc11(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '11', mask), np.array(expected,'i1'))

    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '11', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '11', mask)
    assert err == 1

@pytest.mark.parametrize(
    "blk, mask, expected",
    [([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1, 1,1,0,1], 12345, [0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0]),
     ],
)
def test_crc16(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '16', mask), np.array(expected,'i1'))

    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '16', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '16', mask)
    assert err == 1

@pytest.mark.parametrize(
    "blk, mask, expected",
    [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1]),
     ],
)
def test_crc24A(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '24A', mask), np.array(expected,'i1'))

    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '24A', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '24A', mask)
    assert err == 1

@pytest.mark.parametrize(
    "blk, mask, expected",
    [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]),
     ],
)
def test_crc24B(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '24B', mask), np.array(expected,'i1'))

    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '24B', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '24B', mask)
    assert err == 1

@pytest.mark.parametrize(
    "blk, mask, expected",
    [([0, 0, 1, 1, 0, 0, 0, 1], 0, [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1]),
     ([0, 0, 1, 1, 0, 0, 0, 1], 45678, [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1]),
     ],
)
def test_crc24C(blk, mask, expected):
    assert np.array_equal(crc.nr_crc_encode(np.array(blk,'i1'), '24C', mask), np.array(expected,'i1'))

    blk, err = crc.nr_crc_decode(np.array(expected, 'i1'), '24C', mask)
    assert err == 0

    new_in = expected
    new_in[2] = new_in[2] ^ 1
    blk, err = crc.nr_crc_decode(np.array(new_in,'i1'), '24C', mask)
    assert err == 1

# fmt: on
