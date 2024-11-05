# -*- coding:utf-8 -*-

#list all the testvectors folder.
testvectors_path = [
    "tests/nr_pusch/testvectors_ulsch_without_uci",
    "tests/nr_pusch/testvectors_ulsch_with_uci",
    "tests/nr_pusch/testvectors_pusch",
    "tests/nr_pucch/testvectors_format0",
    "tests/nr_pucch/testvectors_format1",
    "tests/nr_pucch/testvectors_format2",
    "tests/nr_pucch/testvectors_format3",
    "tests/nr_pucch/testvectors_format4",
    "tests/nr_srs/testvectors",
    "tests/nr_prach/testvectors_prach_seq",
    "tests/nr_prach/testvectors_prach",
    "tests/nr_csirs/testvectors",
    "tests/common/testvectors_lowPAPR",
    "tests/common/testvectors_modulation",
    "tests/ldpc/testvectors",
    "tests/polar/testvectors",
    "tests/smallblock/testvectors",
    "tests/nr_pdsch/testvectors_dlsch",
    "tests/nr_pdsch/testvectors",
    "tests/nr_lowphy/testvectors",
    "tests/nr_pdcch/testvectors",
    "tests/nr_ssb/testvectors",
    "tests/nr_ssb/testvectors_highphy",
    "tests/nr_waveform/testvectors",
    "tests/nr_pdsch/testvectors_short_pdsch",
    "tests/nr_testmodel/testvectors"
]

def read_testvectors_path():
    return testvectors_path