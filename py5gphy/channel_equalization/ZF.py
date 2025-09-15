# -*- coding:utf-8 -*-

import numpy as np

def ZF_IRC(Y,H,cov):
    """ ZF IRC channel equalization
    input:
        Y: Nr X 1 vector, recriving data
        H: Nr X NL matrix, channel estimation
        cov: Nr X Nr noise-interference covriance matrix
        where Nr is Rx antenna num, NL is Tx layer number
    output:
        s_est: NL X 1 estimated signal vector
        noise_var:Nt X 1 noise variance for each layer
    """

    Nr, NL = H.shape
    assert Nr >= NL
    assert Nr == Y.size
    assert Nr == cov.shape[0] and Nr == cov.shape[1]

    if Nr == 1:
        assert np.abs(H) > 0 #H should not be zero
        s_est = Y / H
        noise_var = cov/(H.conj().T * H)
        return s_est, noise_var

    #below processing isfor Nr > 1 case

    W1 = H.conj().T @ H

    #check W1 rank to make sure it is non-singular matrix and can do matrix inverse
    if np.linalg.matrix_rank(W1) < W1.shape[0]:
        #add small values to make W1 inversable
        W1 = W1 + np.abs(W1).max()*0.0012*np.identity(NL,'c8')
    
    W = np.linalg.inv(W1) @ H.conj().T 

    s_est = W @ Y

    N1 = W @ cov @ W.conj().T #noise cov after ZF 

    noise_var = np.diagonal(N1) #get matrix diagonal

    return s_est, noise_var.real

def ZF(Y,H,cov):
    """ ZF channel equaliztion,
    the difference between ZF and ZF_IRC is the noise_var estimation
    """
    Nr, NL = H.shape
    assert Nr >= NL
    assert Nr == Y.size
    assert Nr == cov.shape[0] and Nr == cov.shape[1]

    if Nr == 1:
        assert np.abs(H) > 0 #H should not be zero
        s_est = Y / H
        noise_var = cov/(H.conj().T * H)
        return s_est, noise_var

    #below processing isfor Nr > 1 case

    W1 = H.conj().T @ H

    #check W1 rank to make sure it is non-singular matrix and can do matrix inverse
    if np.linalg.matrix_rank(W1) < W1.shape[0]:
        #add small values to make W1 inversable
        W1 = W1 + np.abs(W1).max()*0.0012*np.identity(NL,'c8')
    
    W2 = np.linalg.inv(W1)

    s_est = W2 @ H.conj().T  @ Y

    sigma_2 = np.mean(np.diagonal(cov))    

    noise_var = sigma_2*np.diagonal(W2) #get matrix diagonal

    return s_est, noise_var.real