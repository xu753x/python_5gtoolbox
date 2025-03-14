# -*- coding:utf-8 -*-
import numpy as np
import scipy as sp

def gen_DL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization):
    """refer to 38.101 V18.6.0 B.2.3(uniform linear arrays) and B.2.3A(cross-polar)
    Nt: gNB Number of transmit antennas
    Nr: UE Number of receive antennas
    MIMOCorrelation:"high", "medium", "low"
    Polarization: "uniform" or "cross-polar"
    """

    assert Polarization in ["uniform", "cross-polar"]
    
    if Polarization == "uniform":
        #refer to 36.101 B.2.3 MIMO Channel Correlation Matrices for uniform linear arrays at both eNodeB and UE
        assert MIMOCorrelation in ["high", "medium", "mediumA", "mediumB","low"]
        assert Nt in [1,2,4,8] #based on Table B.2.3.1-1 eNodeB correlation matrix
        assert Nr in [1,2,4,8] #based on Table B.2.3.1-2 UE correlation matrix
        
        #Table B.2.3.2-1
        TableB_2_3_2_1 = { "low": [0,0], "medium": [0.3,0.9],"mediumA":[0.3,0.3874],"mediumB":[0.3,0.005154],"high": [0.9,0.9]}
        alpha, beta = TableB_2_3_2_1[MIMOCorrelation]
        
        #Table B.2.3.1-1 eNodeB correlation matrix
        R_eNB = _gen_correlation_matrix(Nt,alpha)
        
        #Table B.2.3.1-2 UE correlation matrix
        R_UE = _gen_correlation_matrix(Nr,beta)
        
        #Table B.2.3.1-3: spat R correlation matrices
        R_spat = np.kron(R_eNB, R_UE)
    else:
        ##Polarization = "cross-polar", refer to B.2.3A MIMO Channel Correlation Matrices using cross polarized antennas
        assert MIMOCorrelation in ["high", "mediumA", "low"]
        assert Nt in [2,4,8] #based on Table B.2.3.1-1 eNodeB correlation matrix
        assert Nr in [2,4] #based on Table B.2.3.1-2 UE correlation matrix
        
        #refer to 36.101 Table_B_2_3A_3_1, "low" corelation defined in 36.104 Low spatial correlation"
        Table_B_2_3A_3_1 = {"low":[0,0,0], "mediumA":[0.3,0.6,0.2], "high":[0.9, 0.9,0.3]}
        alpha, beta, gamma = Table_B_2_3A_3_1[MIMOCorrelation]

        #36.101 B.2.3A.2.1 Spatial Correlation Matrices at eNB side
        R_eNB = _gen_correlation_matrix(Nt//2, alpha)
        
        #36.101 B.2.3A.2.2 Spatial Correlation Matrices at UE side
        R_UE = _gen_correlation_matrix(Nr//2,beta)

        #polarization correlation matrix
        T_m = np.array([[1,0,-gamma,0], [0,1,0,gamma], [-gamma,0,1,0], [0,gamma,0,1]])

        #permutation matrix
        #P matrix index defined in 36.101 start from 1, not 0, a and b value should minus 1
        P = np.zeros((Nt*Nr,Nt*Nr))
        for i in range(1, Nr+1):
            for j in range(1,Nt//2+1):
                a = (j-1)*Nr + i
                b = 2*(j-1)*Nr + i
                P[a-1,b-1] = 1
        
        for i in range(1, Nr+1):
            for j in range(Nt//2+1, Nt+1):
                a = (j-1)*Nr + i
                b = 2*(j-Nt//2)*Nr -Nr + i
                P[a-1,b-1] = 1
        
        #channel spatial correlation matrix
        tmp1 = np.kron(R_eNB, T_m)
        tmp1 = np.kron(tmp1, R_UE)
        R_spat = (P @ tmp1) @ P.T
    return R_spat

def gen_UL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization):
    """refer to 38.104 V18.5.0 B.5(uniform linear arrays) and B.5A(cross-polar)
    Nt: UE Number of transmit antennas
    Nr: eNB Number of receive antennas
    MIMOCorrelation:"high", "medium", "low"
    Polarization: "uniform" or "cross-polar"
    """

    assert Polarization in ["uniform", "cross-polar"]
    
    if Polarization == "uniform":
        #refer to 36.104 Table B.5.2-1 Correlation for High Medium and Low Level for uniform linear arrays at both eNodeB and UE
        assert MIMOCorrelation in ["high", "medium","low"]
        assert Nr in [1,2,4] #based on Table B.5.1-1 eNodeB correlation matrix
        assert Nt in [1,2,4] #based on Table B.5.1-2 UE correlation matrix
        
        #Table B.5.2-1 Correlation for High Medium and Low Level
        Table_B_5_2_1 = { "low": [0,0], "medium": [0.9,0.3],"high": [0.9,0.9]}
        alpha, beta = Table_B_5_2_1[MIMOCorrelation]
        
        #Table B.5.1-1 eNodeB correlation matrix
        R_eNB = _gen_correlation_matrix(Nr,alpha)
        
        #Table B.5.1-2 UE correlation matrix
        R_UE = _gen_correlation_matrix(Nt,beta)
        
        #Table B.5.1-3:: spat R correlation matrices
        R_spat = np.kron(R_UE, R_eNB)
    else:
        ##Polarization = "cross-polar", refer to B.5A Multi-Antenna channel models using cross polarized antennas
        assert MIMOCorrelation in ["high", "mediumA", "low"]
        assert Nt in [1,2,4] #based on B.5A.2.1 Spatial Correlation Matrices at UE side
        assert Nr in [2,4,8] #based on B.5A.2.2 Spatial Correlation Matrices at eNB side
        
        #refer to 36.104 Table B.5A.3-1 which defined only low correlation case,
        # "mediumA" and "high" correlation case refer to 36.101 Table_B_2_3A_3_1
        Table_B_2_3A_3_1 = {"low":[0,0,0], "mediumA":[0.3,0.6,0.2], "high":[0.9, 0.9,0.3]}
        alpha, beta, gamma = Table_B_2_3A_3_1[MIMOCorrelation]

        #36.104 B.5A.2.2 Spatial Correlation Matrices at eNB side
        R_eNB = _gen_correlation_matrix(Nr//2, alpha)
        
        #36.104 B.5A.2.1 Spatial Correlation Matrices at UE side
        if Nt == 1:
            R_UE = _gen_correlation_matrix(Nt,beta)
        else:
            R_UE = _gen_correlation_matrix(Nt//2,beta)

        #polarization correlation matrix,Table B.5A.1-1 Polarization correlation matrix
        if Nt == 1:
            T_m = np.array([[1,-gamma], [-gamma,1]])
        else:
            T_m = np.array([[1,-gamma,0,0], [-gamma,1,0,0], [0,0,1,gamma], [0,0,gamma,1]])

        #permutation matrix PUL
        PUL = np.zeros((Nt*Nr,Nt*Nr))
        for i in range(1, Nr+1):
            for j in range(1,int(np.ceil(Nt/2))+1):
                a = (j-1)*Nr + i
                b = 2*(j-1)*Nr + i
                PUL[a-1,b-1] = 1
        
        for i in range(1, Nr+1):
            for j in range(int(np.ceil(Nt/2))+1, Nt+1):
                a = (j-1)*Nr + i
                b = (2*j-Nt)*Nr -Nr + i
                PUL[a-1,b-1] = 1
        
        #channel spatial correlation matrix
        tmp1 = np.kron(R_UE, T_m)
        tmp1 = np.kron(tmp1, R_eNB)
        R_spat = (PUL @ tmp1) @ PUL.T
    
    return R_spat

def _gen_correlation_matrix(size, delta):
    """ generate corrlation matrix based on Table B.2.3.1-1 eNodeB correlation matrix
        it can also be used for UE correlation matrix and cross-polar gNB and UE correlation matrix
    """
    assert size in [1,2,4,8]
    R = np.eye(size) 
    
    if size == 1:
        return R
    
    if size == 2:
        R[0,1] = delta
        R[1,0] = delta.conjugate()
        return R
    
    #for size = 4 and 8 case
    step = 1/((size-1)**2) #step = 1/9 for size 4 and 1/49 for size 8
    
    #first generate upper triangle matrix
    seq = np.arange(1,size)**2 #1,4,9,16,25,..
    for line in range(size-1):
        #fill [line, line+1:] value
        R[line, line+1:size] = delta ** (step*seq[0 : size-line-1])
    
    #fill lower triangle with conjugate
    for col in range(size-1):
        R[col+1:, col] = R[col,col+1:].conjugate()
    
    return R

def get_scaling_of_delays_reference():
    """return DS_desired example from 38.901 7.7.3 Table 7.7.3-1
        it is used to guide how to choose DS_desired
    """
    DS_desired_in_ns_Table_7_7_3_1 = {
        "Very short":10, "Short":30, "Nominal":100, "Long":300, "Very long":1000 
        }
    
    return DS_desired_in_ns_Table_7_7_3_1

def gen_H_from_R_spat(R_spat, Nt, Nr):
    """generate H matrix based on channel_spatial_correlation_matrix(R_spat), 
        Nt: Number of transmit antennas
        Nr: Number of receive antennas
        H is Nr X Nt matrix
    the algorighm:
        R_spat = E(vec(H) (vec(H))^H)
        vec(H) is Vectorization H with column first, for examplem vec([[1,2],[3,4]]) = [1;3;2;4]
        L = Cholesky decomposition of R_spat with R_spat = L * L^H, L is  lower triangular matrix
        vec(H) = L* random.normal(mu=0, sigma = 1m size = Nt*Nr) -> L*N(0,1) normal distribution
    """
    L = np.linalg.cholesky(R_spat)
    vec_H = L @ np.random.normal(size=Nt*Nr)
    # reshape vec_H to Nr X Nt matrix
    H = vec_H.reshape((Nr, Nt), order='F')
    return H

if __name__ == "__main__":
    """ run test"""
    print(get_scaling_of_delays_reference())
    
    #gen_H_from_R_spat test
    Nt=2
    Nr=4
    R_spat = gen_DL_channel_spatial_correlation_matrix(Nt, Nr, "medium", "uniform")
    H = gen_H_from_R_spat(R_spat, Nt, Nr)
    
    #run gen_DL_channel_spatial_correlation_matrix, Polarization= "uniform"
    Polarization = "uniform"
    for MIMOCorrelation in ["medium", "mediumA", "mediumB","low","high"]:
        for Nt in [1,2,4,8]:
            for Nr in [1,2,4,8]:
                R_spat = gen_DL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
                print(R_spat)
    
    #run gen_DL_channel_spatial_correlation_matrix, Polarization= "cross-polar"
    Polarization = "cross-polar"
    for MIMOCorrelation in ["mediumA", "low","high"]:
        for Nt in [2,4,8]:
            for Nr in [2,4]:
                R_spat = gen_DL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
                #print(R_spat)
    
    #run gen_UL_channel_spatial_correlation_matrix, Polarization= "uniform"
    Polarization = "uniform"
    for MIMOCorrelation in ["medium", "low","high"]:
        for Nt in [1,2,4]:
            for Nr in [1,2,4]:
                R_spat = gen_UL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
                #print(R_spat)

    #run gen_UL_channel_spatial_correlation_matrix, Polarization= "cross-polar"
    Polarization = "cross-polar"
    for MIMOCorrelation in ["mediumA", "low","high"]:
        for Nt in [1,2,4]:
            for Nr in [2,4,8]:
                R_spat = gen_UL_channel_spatial_correlation_matrix(Nt, Nr, MIMOCorrelation, Polarization)
                print(R_spat)
    pass