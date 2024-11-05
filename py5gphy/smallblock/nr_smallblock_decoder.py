# -*- coding:utf-8 -*-
import numpy as np

#table 5.3.3.1-1
_encoded_1bit_table = [[0], 
        [0,-2],
        [0,-2,-1,-1],
        [0,-2,-1,-1,-1,-1],
        [0,-2,-1,-1,-1,-1,-1,-1]]
#table 5.3.3.2-1
_encoded_2bit_table = [[0,3,5],
        [0,3,5,0,3,5],
        [0,3,-1,-1,5,0,-1,-1,3,5,-1,-1],
        [0,3,-1,-1,-1,-1,5,0,-1,-1,-1,-1,3,5,-1,-1,-1,-1],
        [0,3,-1,-1,-1,-1,-1,-1,5,0,-1,-1,-1,-1,-1,-1,3,5,-1,-1,-1,-1,-1,-1]]
#table 5.3.3.3-1
_base_seq_table = np.array(
    [
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, ],
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, ],
        [1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, ],
        [1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, ],
        [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, ],
        [1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, ],
        [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, ],
        [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, ],
        [1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, ],
        [1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, ],
        [1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, ],
        [1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, ],
        [1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, ],
        [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, ],
        [1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, ],
        [1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, ],
        [1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, ],
        [1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, ],
        [1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, ],
        [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, ],
        [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, ],
        [1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, ],
        [1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, ],
        [1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, ],
        [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, ],
        [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, ],
        [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, ],
        [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, ],
        [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, ],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, ],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ]
    ]
)

def decode_smallblock(dn,K,Qm=2):
    """ decode small block length by 38.212 5.3.3
    ck = encode_smallblock(dn)
    input:
        dn: input bit sequence
        K: output bit length
        Qm: modulation order in range[1,2,4,6,8], used for 1 bits and 2bits, 3-11 bits can ignore it
    output:
        ck: K length bit sequence, 
        
    """
    N = dn.size
    assert K < 12
    assert Qm in [1,2,4,6,8]
    if K == 1:
        assert N == Qm
    elif K == 2:
        assert N == 3*Qm
    else:
        assert N == 32
    
    if K == 1:
        ck = dn[0:1]
    elif K == 2:
        ck = dn[0:2]
    else:
        #bits length 3-11
        #_base_seq_table[0:K,0:K] is singular matrix, can not use below
        #inverse matrix method to estimate ck
        #H = _base_seq_table[0:K,0:K]
        #outd = np.linalg.solve(H, dn[0:K].T) #outd = H\dn(0:K);
        #ck = np.round(outd) % 2

        #use ML to search best match sequence
        M = 2 ** K
        for m in range(M):
            #convert int m to K size bit list
            bitformat = "{" + f"0:0{K}b" + "}"
            bitseq = np.array([int(x) for x in bitformat.format(m)],'i1')
            outd =  _base_seq_table[:,0:K] @ bitseq
            dn_cal = np.round(outd) % 2
            dn_cal = dn_cal.astype('i1')
            if np.array_equal(dn, dn_cal):
                ck = bitseq
                break
    
    ck = ck.astype('i1')
    return ck


if __name__ == "__main__":
    from scipy import io
    import os
    curpath = "tests/smallblock/testvectors"
    for f in os.listdir(curpath):
            if f.endswith(".mat") and f.startswith("smallblock_encode_testvec"):
                matfile = io.loadmat(curpath + '/' + f)
                #read data from mat file
                ck_ref = matfile['inbits'][0]
                dn = matfile['dn'][0]
                K = matfile['K'][0][0]
                Qm = matfile['Qm'][0][0]
                
                if K <= 2:
                    ck = decode_smallblock(dn, K, Qm)
                else:
                    ck = decode_smallblock(dn, K)

                assert np.array_equal(ck, ck_ref)

    
    pass
