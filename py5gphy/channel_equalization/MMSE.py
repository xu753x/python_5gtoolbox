# -*- coding:utf-8 -*-

import numpy as np

def MMSE_IRC(Y,H,cov):
    """ MMSE IRC channel equalization
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
        #for Nr = NL =1, ZF and MMSE have the same result
        assert np.abs(H) > 0 #H should not be zero
        s_est = Y / H
        noise_var = cov/(H.conj().T * H)
        return s_est, noise_var

    #below processing isfor Nr > 1 case

    #need comp if matrix is non-singular matrix
    if np.linalg.matrix_rank(cov) < cov.shape[0]:
        #add small values to make cov inversable
        cov = cov + np.abs(cov).max()*0.0012*np.identity(cov.shape[0],'c8')
    inv_cov = np.linalg.inv(cov)

    W1 = H.conj().T @ inv_cov @ H 
    W1 = W1+ np.identity(W1.shape[0],'c8')

    #need comp if matrix is non-singular matrix
    if np.linalg.matrix_rank(W1) < W1.shape[0]:
        #add small values to make cov inversable
        W1 = W1 + np.abs(W1).max()*0.0012*np.identity(W1.shape[0],'c8')
    inv_W1 = np.linalg.inv(W1)
    
    W = inv_W1 @ H.conj().T @ inv_cov

    s_hat = W @ Y

    comp = 1 - np.diagonal(inv_W1) #get compensation value
    #compensate
    s_est = s_hat / comp
        
    noise_var = 1/comp - 1 #get matrix diagonal

    return s_est, noise_var.real

def MMSE(Y,H,cov):
    """ MMSE channel equalization
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
        #for Nr = NL =1, ZF and MMSE have the same result
        assert np.abs(H) > 0 #H should not be zero
        s_est = Y / H
        noise_var = cov/(H.conj().T * H)
        return s_est, noise_var

    #below processing isfor Nr > 1 case

    sigma_2 = np.mean(np.diagonal(cov))    
    W1 = H.conj().T @ H /sigma_2 + np.identity(NL, 'c8')

    #need comp if matrix is non-singular matrix
    if np.linalg.matrix_rank(W1) < W1.shape[0]:
        #add small values to make cov inversable
        W1 = W1 + np.abs(W1).max()*0.0012*np.identity(W1.shape[0],'c8')
    inv_W1 = np.linalg.inv(W1)
    
    W = inv_W1 @ H.conj().T / sigma_2

    s_hat = W @ Y

    comp = 1 - np.diagonal(inv_W1) #get compensation value
    #compensate
    s_est = s_hat / comp
        
    noise_var = 1/comp - 1 #get matrix diagonal

    return s_est, noise_var.real
