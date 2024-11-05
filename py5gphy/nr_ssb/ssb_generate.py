# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.common import nrPRBS
from py5gphy.common import nrModulation
from py5gphy.nr_ssb import nrBCH
from py5gphy.nr_ssb import nrPBCH

def gen_ssblock(bchmib, ssb_config, LMax,pci, sfn, HRF, iSSB):
    """ generate SSB block including PSS,SSS,PBCH and PBCH DMRS
    ssb_block = gen_ssblock(self, pci)
    input:
        pci: physical layer cell identity in range 0 - 1007
        sfn: system frame number
        HRF: half frame bit, 0 if first half frame, 1 for second half frame
    output:
        ssb_block: 4 symbol X 20 PRB mapped SSB block


    """
    v = pci % 4  #38.212 7.4.3.1 for mapping
    ssb_block = np.zeros((4,20*12),'c8') #4 symbol x 20*12 sc 
    
    # PSS process
    dPSS = _PSS_generation(pci)
    ssb_block[0,56:183] = dPSS # map PSS to physical resources refer to 38.211 7.4.3

    # SSS process
    dSSS = _SSS_generation(pci)
    ssb_block[2,56:183] = dSSS # map PSS to physical resources refer to 38.211 7.4.3

    # PBCH
    #bchmib = nrBCH.genBCHMIB(self.ssb_config, sfn)
    rm_bitseq = nrBCH.nrBCHencode(bchmib, ssb_config, sfn,HRF,pci)
    dPBCH = nrPBCH.nrPBCHencode(rm_bitseq, pci, iSSB)

    #PNCH DMRS
    assert HRF < 2
    if LMax == 4:
        ibar_SSB = (iSSB % 4) + 4*HRF
    else:
        ibar_SSB = iSSB % 8
    cinit = (((ibar_SSB+1)*(pci // 4 + 1)) << 11) + ((ibar_SSB + 1) << 6) + (pci % 4)
    prbs_seq = nrPRBS.gen_nrPRBS(cinit, 2*144)
    dPBCHDMRS = nrModulation.nrModulate(prbs_seq, 'QPSK')

    #symbol 1 resource mapping
    mask = np.ones(240, dtype=bool)
    mask[v:240:4] = False
    ssb_block[1,mask] = dPBCH[0:240 - 240//4]
    ssb_block[1,mask==False] = dPBCHDMRS[0:240//4]
    
    #symbol 2 
    pbch_offset = 240 - 240//4 
    pbchdmrs_offset = 240//4
    mask = np.ones(48, dtype=bool)
    mask[v:48+v:4] = False
    
    tmp = ssb_block[2,0:48]
    tmp[mask] = dPBCH[pbch_offset+0:pbch_offset+48-48//4]
    tmp[mask==False] = dPBCHDMRS[pbchdmrs_offset+0:pbchdmrs_offset+48//4]
    tmp = ssb_block[2,192:240]
    tmp[mask] = dPBCH[pbch_offset+48-48//4:pbch_offset+96-96//4]
    tmp[mask==False] = dPBCHDMRS[pbchdmrs_offset+48//4:pbchdmrs_offset+96//4]
    
    #symbol 3
    pbch_offset = pbch_offset + (96 - 96//4)
    pbchdmrs_offset = pbchdmrs_offset + 96//4
    mask = np.ones(240, dtype=bool)
    mask[v:240:4] = False
    ssb_block[3, mask] = dPBCH[pbch_offset : pbch_offset + 240 - 240//4]
    ssb_block[3, mask==False] = dPBCHDMRS[pbchdmrs_offset : pbchdmrs_offset + 240//4]

    return ssb_block

def _PSS_generation(pci):
    # PSS generation

    nID2 = pci % 3
    #generate 127 xn sequence
    xn = np.zeros(127,'i1')
    xn[0:7] = [0,1,1,0,1,1,1]
    for i in range(0,127-7):
        xn[i+7] = (xn[i+4] + xn[i]) % 2
    
    idxlist = (np.arange(127) + 43*nID2) % 127
    dPSS = (1-2*xn[idxlist])
    return dPSS

def _SSS_generation(pci):
    #generate 127 x0n sequence
    x0n = np.zeros(127,'i1')
    x0n[0] = 1
    for i in range(0,127-7):
        x0n[i+7] = (x0n[i+4] + x0n[i]) % 2
    
    #generate 127 x1n sequence
    x1n = np.zeros(127,'i1')
    x1n[0] = 1
    for i in range(0,127-7):
        x1n[i+7] = (x1n[i+1] + x1n[i]) % 2
    
    nID2 = pci % 3
    nID1 = pci // 3
    m0 = 15*(nID1 // 112) + 5*nID2
    m1 = nID1 % 112
    idx0list = (np.arange(127) + m0) % 127
    idx1list = (np.arange(127) + m1) % 127

    dSSS = (1-2*x0n[idx0list]) * (1-2*x1n[idx1list])
    return dSSS


if __name__ == "__main__":
    print("test PSS SSS generation")
    dPSS_ref = np.array([1, -1, -1, 1, -1, -1, -1, -1, 1, 1, -1, -1, -1, 1, 1, -1, 1, -1, 1, -1, -1, 1, 1, -1, -1, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, -1, 1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1, -1, 1, 1, -1, 1, 1, -1, -1, 1, -1, 1, 1, -1, -1, -1, -1, 1, -1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, -1, 1, 1, 1, -1, -1, -1, 1, -1, -1, 1, 1, 1, -1, 1, -1, 1, 1, -1, 1, -1, -1, -1, -1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 1, -1],'i1')
    assert np.array_equal(_PSS_generation(0),dPSS_ref)

    dPSS_ref = np.array([1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1, -1, 1, 1, -1, 1, 1, -1, -1, 1, -1, 1, 1, -1, -1, -1, -1, 1, -1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, -1, 1, 1, 1, -1, -1, -1, 1, -1, -1, 1, 1, 1, -1, 1, -1, 1, 1, -1, 1, -1, -1, -1, -1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 1, -1, 1, -1, -1, 1, -1, -1, -1, -1, 1, 1, -1, -1, -1, 1, 1, -1, 1, -1, 1, -1, -1, 1, 1, -1, -1, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, -1],'i1')
    assert np.array_equal(_PSS_generation(1),dPSS_ref)

    dPSS_ref = np.array([-1, -1, -1, -1, -1, -1, 1, 1, 1, -1, -1, -1, 1, -1, -1, 1, 1, 1, -1, 1, -1, 1, 1, -1, 1, -1, -1, -1, -1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 1, -1, 1, -1, -1, 1, -1, -1, -1, -1, 1, 1, -1, -1, -1, 1, 1, -1, 1, -1, 1, -1, -1, 1, 1, -1, -1, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, -1, 1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1, -1, 1, 1, -1, 1, 1, -1, -1, 1, -1, 1, 1, -1, -1, -1, -1, 1, -1, -1, -1, 1, 1, 1, 1, -1],'i1')
    assert np.array_equal(_PSS_generation(2),dPSS_ref)

    dSSS_ref = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1, -1, 1, 1, 1, -1, 1, -1, 1, -1, 1, 1, -1, -1, 1, 1, 1, -1, -1, -1, 1, -1, 1, -1, 1, 1, 1, 1, 1, 1, 1, -1, -1, 1, 1, 1, -1, 1, -1, -1, -1, -1, -1, -1, -1, -1, 1, -1, 1, 1, -1, 1, 1, 1, 1, -1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, -1, 1, 1, -1, -1, -1, -1, 1, 1, -1, -1, -1, -1, -1, 1, 1, 1, -1, 1, -1, 1, 1, 1, 1, 1, -1, -1, 1, 1, 1, -1, 1, 1, 1, -1, 1, 1, -1, -1, -1, 1, -1, -1, -1],'i1')
    assert np.array_equal(_SSS_generation(0),dSSS_ref)

    dSSS_ref = np.array([1, 1, -1, 1, 1, 1, -1, 1, -1, -1, -1, 1, -1, -1, -1, 1, 1, 1, -1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1, -1, 1, 1, -1, -1, -1, 1, -1, 1, -1, -1, -1, 1, -1, 1, 1, 1, 1, -1, 1, -1, -1, 1, 1, 1, -1, 1, -1, 1, -1, -1, -1, 1, -1, 1, -1, -1, 1, -1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, 1, 1, 1, 1, 1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1, -1, -1, 1, -1, -1, -1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1, 1, 1, 1], 'i1')
    assert np.array_equal(_SSS_generation(57),dSSS_ref)

    dSSS_ref = np.array([1, 1, -1, -1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 1, 1, 1, 1, -1, 1, 1, 1, -1, -1, 1, -1, -1, -1, -1, 1, -1, 1, 1, -1, 1, -1, 1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1, 1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, -1, -1, 1, 1, -1, 1, -1, 1, 1, 1, 1, -1, 1, 1, 1, 1, -1, 1, -1, 1, 1, 1, -1, 1, 1, -1, -1, -1, -1, 1, 1, 1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, 1, 1, -1, -1], 'i1')
    assert np.array_equal(_SSS_generation(580),dSSS_ref)
    
    print("test SSB generation")
    from tests.nr_ssb import test_ssb_generation
    test_ssb_generation.test_SSB_generate()

    