# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_equalization import ZF
from py5gphy.channel_equalization import MMSE
from py5gphy.channel_equalization import ML
from py5gphy.channel_equalization import ML2
from py5gphy.channel_equalization import MMSE_ML
from py5gphy.channel_equalization import opt_rank2_ML
from py5gphy.demodulation import nr_Demodulation

def channel_equ_and_demod(Y, H, cov, modtype, CEQ_config):
    """ channel equalization and demodulation
    """
    if CEQ_config["algo"] == "ZF":
        s_est, noise_var = ZF.ZF(Y, H, cov)
        de_hardbits,LLR_a = nr_Demodulation.nrDemodulate(s_est,modtype,noise_var)
    elif CEQ_config["algo"] == "ZF-IRC":
        s_est, noise_var = ZF.ZF_IRC(Y, H, cov)
        de_hardbits,LLR_a = nr_Demodulation.nrDemodulate(s_est,modtype,noise_var)
    elif CEQ_config["algo"] == "MMSE":
        s_est, noise_var = MMSE.MMSE(Y, H, cov)
        de_hardbits,LLR_a = nr_Demodulation.nrDemodulate(s_est,modtype,noise_var)
    elif CEQ_config["algo"] == "MMSE-IRC":
        s_est, noise_var = MMSE.MMSE_IRC(Y, H, cov)
        de_hardbits,LLR_a = nr_Demodulation.nrDemodulate(s_est,modtype,noise_var)
    elif CEQ_config["algo"] == "ML-IRC-soft":
        s_est, noise_var,de_hardbits, LLR_a = ML.ML_IRC(Y, H,  cov, modtype,"soft")
    elif CEQ_config["algo"] == "ML-soft":
        s_est, noise_var,de_hardbits, LLR_a = ML.ML(Y, H,  cov, modtype,"soft")
    elif CEQ_config["algo"] == "ML-IRC-hard":
        s_est, noise_var,de_hardbits, LLR_a = ML.ML_IRC(Y, H,  cov, modtype,"hard")
    elif CEQ_config["algo"] == "ML-hard":
        s_est, noise_var,de_hardbits, LLR_a = ML.ML(Y, H,  cov, modtype,"hard")
    elif CEQ_config["algo"] == "MMSE-ML":
        s_est, noise_var,de_hardbits, LLR_a = MMSE_ML.MMSE_ML(Y, H,  cov, modtype)
    elif CEQ_config["algo"] == "MMSE-ML-IRC":
        s_est, noise_var,de_hardbits, LLR_a = MMSE_ML.MMSE_ML_IRC(Y, H,  cov, modtype)
    elif CEQ_config["algo"] == "opt-rank2-ML":
        s_est, noise_var,de_hardbits, LLR_a = opt_rank2_ML.opt_rank2_ML(Y, H,  cov, modtype)
    elif CEQ_config["algo"] == "opt-rank2-ML-IRC":
        s_est, noise_var,de_hardbits, LLR_a = opt_rank2_ML.opt_rank2_ML_IRC(Y, H,  cov, modtype)
    elif CEQ_config["algo"] == "ML2-IRC-soft":
        s_est, noise_var,de_hardbits, LLR_a = ML2.ML_IRC(Y, H,  cov, modtype,"soft")
    elif CEQ_config["algo"] == "ML2-soft":
        s_est, noise_var,de_hardbits, LLR_a = ML2.ML(Y, H,  cov, modtype,"soft")
    else:
        assert 0  
    
    return s_est, noise_var, de_hardbits,LLR_a

def cov_inverse_decompose(cov):
    """inverse cov and then decompose it to U^HU = inv_cov
    """
    #need comp if matrix is non-singular matrix
    #if np.linalg.matrix_rank(cov) < cov.shape[0]:
    while np.linalg.matrix_rank(cov) < cov.shape[0]:
        #add small values to make cov inversable
        cov = cov + np.abs(cov).max()*0.0012*np.identity(cov.shape[0],'c8')
        
    inv_cov = np.linalg.inv(cov)
    
    #eigenvectors @ np.diag(eigenvalues) @ eigenvectors.conj().T = inv_cov
    eigenvalues, eigenvectors = np.linalg.eigh(inv_cov)

    s1=np.diag(np.emath.sqrt(eigenvalues))
    #U^H @ U = inv_cov
    U = (eigenvectors @ s1).conj().T 

    return U

