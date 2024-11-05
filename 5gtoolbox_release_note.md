# V1.0.0
* support Release 15
* support sub6GHz only, not support mmwave
* support one carrier contain only one BWP
* support 1/2/4 antenna
* support 15khz and 30khz scs, 
* all channel share the same scs
* do not support Phase-tracking reference signals which is used for mmwave
* PDSCH only support non-interleaved VRB-to-PRB mapping, not support interleaved VRB-to-PRB mapping
* only suport PDSCH/PUSCH PDSCH mapping type A, and l0 = 2, not support PDSCH mapping type B
* only support PDSCH/PUSCH DM-RS configuration type 1, not support PDSCH DM-RS configuration type 2
* only support PDSCH/PUSCH single-symbol DM-RS, not support double-symbol DM-RS
* only finish DL/UL transmission, do not support DL/UL receiver