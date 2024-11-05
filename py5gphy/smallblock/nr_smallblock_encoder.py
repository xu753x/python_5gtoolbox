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

def encode_smallblock(inbits,Qm=2):
    """ encode small block length by 38.212 5.3.3
    dn = encode_smallblock(inbits)
    input:
        inbits: length 1-11 bit sequence
        Qm: modulation order in range[1,2,4,6,8], used for 1 bits and 2bits, 3-11 bits can ignore it
    output:
        dn: N length bit sequence, 
        (x,y) placeholder is set to (-1,-2) which will be replaced during PUSCH scrambling 38.211 6.3.1.1
    """
    K = inbits.size
    assert K < 12
    assert Qm in [1,2,4,6,8]
    
    offset = Qm // 2
    if K == 1:
        dn = np.array(_encoded_1bit_table[offset],'i1')
        dn[0] = inbits[0]
    elif K == 2:
        c0 = inbits[0]
        c1 = inbits[1]
        c2 = (c0+c1) % 2
        dn = np.array(_encoded_2bit_table[offset],'i1')
        dn[dn==0] = c0
        dn[dn==3] = c1
        dn[dn==5] = c2
    else:
        #bits length 3-11
        outd = _base_seq_table[:,0:K] @ inbits.T
        dn = outd % 2
    
    dn = dn.astype('i1')
    return dn


if __name__ == "__main__":
    print("test small block encoder")
    from tests.smallblock import test_smallblock_encoder
    file_lists = test_smallblock_encoder.get_testvectors()
    count = 1
    for filename in file_lists:
        print("count= {}, filename= {}".format(count, filename))
        count += 1
        test_smallblock_encoder.test_nr_smallblock_encode(filename)
    