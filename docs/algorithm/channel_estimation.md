# steps
* LS estimate
* time offset estimate
* freq offset estimate, and also estimate rho
* time offset comp
* freq offset comp
* freq channel est per symbol using DFT or DCT
* time domain channel estimation extension

## DFT
* extend extra points on both side
* symmetrix extension
* IDFT or DCT
* remove noise: outside boundary, lower than threshold
* padding with zero to 4x length
* dft or IDCT
* get estimated H
* noise matrix est



