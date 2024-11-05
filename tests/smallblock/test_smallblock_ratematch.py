# -*- coding: utf-8 -*-
import pytest
import os
from zipfile import ZipFile 
from scipy import io
import numpy as np

from py5gphy.smallblock import nr_smallblock_ratematch

@pytest.mark.parametrize(
    "ins, M, expected",
    [([1,0,0,1], 3, [1,0,0]),
     ([1,0,0,1], 6, [1,0,0,1,1,0]),
     ],
)
def test_smallblock_ratematch(ins, M, expected):
    fe = nr_smallblock_ratematch.ratematch_smallblock(np.array(ins), M)
    np.array_equal(fe, np.array(expected))