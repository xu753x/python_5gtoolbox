# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.smallblock import nr_smallblock_ratematch
from py5gphy.smallblock import nr_smallblock_raterecover

@pytest.mark.parametrize(
    "ins, M, expected",
    [([1,0,0,1], 3, [1,0,0]),
     ([1,0,0,1], 6, [1,0,0,1,1,0]),
     ],
)
def test_smallblock_raterecover(ins, M, expected):
    expecteda = np.array(expected)
    insa = np.array(ins)
    
    N = insa.size
    LLRin = 1 - 2*expecteda.astype('i1')
    
    dn = nr_smallblock_raterecover.raterecover_smallblock(LLRin, N)

    fe = nr_smallblock_ratematch.ratematch_smallblock(dn, M)
    np.array_equal(fe, np.array(expected))