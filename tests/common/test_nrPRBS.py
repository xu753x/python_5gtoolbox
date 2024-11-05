# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.common import nrPRBS

def get_testvectors():
    testcases = [
        [[10,20], [0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1]],
        [[12345,32], [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0]],
    ]
    return testcases

@pytest.mark.parametrize("ins, expected", get_testvectors())
def test_nrPRBS(ins, expected):
    
    seq = nrPRBS.gen_nrPRBS(ins[0], ins[1])
    seq_ref = np.array(expected, 'i1')
    
    assert np.array_equal(seq, seq_ref)