# -*- coding:utf-8 -*-

import numpy as np
import math

from py5gphy.polar import frozen_table
from py5gphy.polar import gen_N_value
from py5gphy.polar import gen_kron_matrix 

def construct(K, E, nMax):
    """generate F table, qPC table and PCwm table
    [F, qPC, N, nPC, nPCwm] = construct(K, E, nMax)
    input:
        K: input bit size
        E: rate match output size
        nMax: maimum n value(either 9 or 10)
    output:
        F:np.array frozen table with total size N. 
          in F table, K entries is 0(information bits), N-K entries are 1(frozen bits)
        qPC: np.array, parity check bits table
        N: polar output size
        nPC: numbder of PC
        nPCwm: number of PCwm
    """
    
    assert nMax in [9, 10]

    # get N and n value 38.212 5.3.1
    [N, n] = gen_N_value.genNnvalue(K, E, nMax)

    #get nPC and nPCwm
    # MATLAB 5G toolbox has a small bug at here which is usually not triggered
    #the processing has issue if DL DCI K is in [18,25], 
    if nMax == 9:  # DL only , TS38.212 7.1.4 and 7.3.3, nMax =9 and iIL = 1( polar interleave)
        nPC = 0
        nPCwm = 0
    else:  #for nMax = 10, UL only, TS38.212 6.3.1.3.1 and 6.3.2.3.1, nMax = 10 and iIL =0(no polar interleave)
        # K value shall be in range [18:25] or >30
        assert (K in range(18,26)) or (K > 30)
        
        if (K >= 18) and (K <= 25):
            nPC = 3
            if ((E - K + 3) > 192 ):
                nPCwm = 1
            else:
                nPCwm = 0        

        if K > 30:
            nPC = 0
            nPCwm = 0
    
    #UE is not expected to be configured with K + nPC > E, 38.212 5.3.1
    assert K + nPC <= E

    # get QN table 5.3.1.2-1
    QNMax_table = frozen_table.frozen_pos_table
    idx = QNMax_table < N
    #QN_table is subset of QNMax_table with all elements less than N
    QN_table = QNMax_table[idx]

    #gen Jn table 38.212 5.4.1.1,
    ## table 5.4.1.1-1
    pi_table = [0,1,2,4, 3,5,6,7, 8,16,9,17, 10,18,11,19,    
          12,20,13,21, 14,22,15,23, 24,25,26,28, 27,29,30,31]
    
    Jn_table = np.zeros(N, 'i2')
    for m in range(N):
        idx = (32 * m) // N
        Jn_table[m] = pi_table[idx]*(N // 32) +  (m % (N // 32))

    # get frozen and information bit indices sets, qF and qI, TS38.212 5.4.1.1
    qFtmp = []
    if E < N:
        if (K/E) <= 7/16: # puncturing
            #for m in range(N - E):
            #    qFtmp.append(Jn_table[m])
            qFtmp.extend(Jn_table[0 : N-E])
            
            if E >= (3 * N /4):
                ulim = math.ceil(3*N/4 - E/2)
                qFtmp.extend(range(ulim))
            else:
                ulim = math.ceil(9*N/16 - E/4)
                qFtmp.extend(range(ulim))
            
            qFtmp = set(qFtmp)
        else:  # shorting
            #for m in range(E, N):
            #    qFtmp.append(Jn_table[m])
            qFtmp.extend(Jn_table[E : N])
            qFtmp = set(qFtmp)

    #get qI from qFtmp and QN_table, most reliable bits first in this table
    qI_table = np.zeros(K + nPC, 'i2')
    j = 0
    for m in range(N):
        ind = QN_table[N - 1 - m]
        if ind in qFtmp:
            continue
        qI_table[j] = ind
        j += 1
        if j == (K + nPC):
            break
    
        
    #get QF
    qF_table = np.setdiff1d(QN_table, qI_table, assume_unique=True)

    #set frozen bit in F to 1 and information bits in F to 0
    F = np.zeros(N, 'i1')
    F[qF_table] = 1

    # get qPC table in 38.212 5.3.1.2
    qPC = np.zeros(nPC, 'i2')
    if nPC > 0:
        #A number of nPC - nPCwm parity check bits are placed in the least reliable bit indices in qI_table
        qPC[0 : nPC - nPCwm] = qI_table[-(nPC-nPCwm) : ] # least reliables bits
        if nPCwm: #this value =  1 or 0
            #get G
            G = gen_kron_matrix.gen_kron(N)
            wg = G.sum(axis=1)  #row weight

            #QI -nPC most reliable bit indices
            qtildeI_table = qI_table[0 : qI_table.size-nPC] #most reliable bits

            wg_qtildeI_table = wg[qtildeI_table]

            #if there are more than nPCwm bit indices of the same minimum row weight in qtildeI_table
            #nPCwm other parity check bits are placed in the nPCwm bit indices of the highest reliability 
            # and the minimum row weight in wg_qtildeI_table
            minwt = np.min(wg_qtildeI_table)
            minidx = np.where(wg_qtildeI_table == minwt)

            # most reliable, minimum row weight is first value
            qPC[nPC - 1] = qtildeI_table[minidx[0][0]] #minidx is arrays
    
    return F, qPC, N, nPC, nPCwm
    
if __name__ == "__main__":

    #E = N, nMax=9, nPC = 0 
    F, qPC, N, nPC, nPCwm = construct(40, 64, 9)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'i1'))
    assert np.array_equal(qPC, np.array([], 'i2'))

    #E < N, nMax=9, nPC = 0 ,shorting
    F, qPC, N, nPC, nPCwm = construct(40, 60, 9)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1], 'i1'))
    assert np.array_equal(qPC, np.array([], 'i2'))
    assert nPCwm == 0

    #E < N, nMax=9, nPC = 0 ,puncturing,(K/E) <= 7/16 and E >= (3 * N /4):
    F, qPC, N, nPC, nPCwm = construct(30, 90, 9)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'i1'))
    assert np.array_equal(qPC, np.array([], 'i2'))
    assert nPCwm == 0

    #E < N, nMax=10, : nPC = 3,nPCwm = 0
    F, qPC, N, nPC, nPCwm = construct(20, 60, 10)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'i1'))
    assert np.array_equal(qPC, np.array([56, 23,52], 'i2'))
    assert nPCwm == 0

    #E < N, nMax=10, : nPC = 3,nPCwm = 1
    F, qPC, N, nPC, nPCwm = construct(20, 220, 10)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'i1'))
    assert np.array_equal(qPC, np.array([248, 231, 252], 'i2'))
    assert nPCwm == 1

    #E < N, nMax=10, : nPC = 0,nPCwm = 0
    F, qPC, N, nPC, nPCwm = construct(33, 150, 10)
    assert np.array_equal(F,np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'i1'))
    assert np.array_equal(qPC, np.array([], 'i2'))
    assert nPCwm == 0
    
    pass
    