# -*- coding:utf-8 -*-
import numpy as np

"""
3GPP define MIMO Channel Correlation Matrices in
TS36.101 B2.3 for LTE DL
TS36.104 B2.5 for LTE UL
TS38.101-4 B2.3 for NR DL
TS38.104 G2.3 for NR UL
this implementation mostly refer to TS38.101-4 and TS38.104
with exception that:
for DL cross polarized antennas , refer to TS36.101 B2.3A.2
ATTN:
TS38.104 Table G.2.3.1.2-3: MIMO correlation matrices for medium correlation 
provided R_spat for 2x4 case is not positive semi-definite
add value_a = 0.00010 to fix it
"""
def get_nr_MIMO_Rspat(Nt, Nr,  Polarization="uniform",direction="DL",MIMOCorrelation="customized",parameters=[0,0]):
    """ get MIMO Channel Correlation Matrices
    input:
    Nt: tx antenna number, in [1,2,4,8] different option for different Polarization
    Nr: Rx antenna number,in [1,2,4,8]
    MIMOCorrelation: per spec
        if direction= DL and Polarization="uniform"
            MIMOCorrelation is in ["high", "medium", "mediumA", "low"]
        if direction= DL and Polarization="cross-polar"
            MIMOCorrelation is in ["high", "mediumA", "low"]
        if direction= UL and Polarization="uniform"
            MIMOCorrelation is in ["high", "medium","low"]
        if direction= UL and Polarization="cross-polar"
            MIMOCorrelation is in ["high", "mediumA", "low"]
        if MIMOCorrelation = "customized"
            use [alpha, beta ] defined in parameters input
    Polarization: "uniform" or "cross-polar"
    direction: "DL" or "UL"
    parameters: include [alpha, beta] values
    
    output:
        R_spat: MIMO Channel Correlation Matrices with size of (Nt*Nr) X (Nt*Nr)
    """

    #validate input parameters
    assert Polarization in ["uniform", "cross-polar"]
    assert direction in ["DL", "UL"]

    #get 
    if MIMOCorrelation == "customized":
        assert len(parameters) == 2
        alpha, beta  = parameters

        R_tx = _gen_correlation_matrix(Nt,alpha) #Tx correlation matrix
        R_rx = _gen_correlation_matrix(Nr,beta) #Rx correlation matrix
        R_spat = np.kron(R_tx, R_rx)        

        value_a = 0.00012
        R_spat = (R_spat + value_a*np.eye(Nt*Nr,dtype=np.complex64))/(1+value_a)
    else:
        if Polarization == "uniform" and direction=="DL":
            R_spat = _Rspat_for_uniform_DL(Nt, Nr,MIMOCorrelation)
        elif Polarization == "uniform" and direction=="UL":
            R_spat = _Rspat_for_uniform_UL(Nt, Nr,MIMOCorrelation)
        elif Polarization == "cross-polar" and direction=="DL":
            R_spat = _Rspat_for_cross_polar_DL(Nt, Nr,MIMOCorrelation)
        elif Polarization == "cross-polar" and direction=="UL":
            R_spat = _Rspat_for_cross_polar_UL(Nt, Nr,MIMOCorrelation)
        else:
            assert 0
            
    #check if R_spat is _is_positive_semidefinite(matrix, tol=1e-8):
    assert _is_positive_semidefinite(R_spat, tol=3e-8) == True

    return R_spat

def _Rspat_for_uniform_DL(Nt, Nr,MIMOCorrelation):
    #TS38.101-4 B.2.3.1
    assert MIMOCorrelation in ["high", "medium", "mediumA", "low"]
    assert Nt in [1,2,4] #Table B.2.3.1.1-1 gNB correlation matrix
    assert Nr in [1,2,4] #Table B.2.3.1.1-2 UE correlation matrix
        
    #Table B.2.3.1.2-1
    TableB_2_3_1_2_1 = { "low": [0,0], "medium": [0.3,0.9],"mediumA":[0.3,0.3874],"high": [0.9,0.9]}
    alpha, beta = TableB_2_3_1_2_1[MIMOCorrelation]

    R_tx = _gen_correlation_matrix(Nt,alpha) #gNB correlation matrix
    R_rx = _gen_correlation_matrix(Nr,beta) #UE correlation matrix
    
    #TS38.104 Table G.2.3.1.1-3: correlation matrices
    R_spat = np.kron(R_tx, R_rx)

    #Where the value "a" is a scaling factor such that the smallest value is used to obtain a positive 
    # semi-definite result. For the 4x2 high correlation case, a=0.00010. For the 4x4 high correlation case, a=0.00012.
    # The same method is used to adjust the 2x4 and 4x4 medium correlation matrix in Table B.2.3.1.2-3 to 
    # insure the correlation matrix is positive semi-definite after round-off to 4 digit precision with a 
    # = 0.00010 and a = 0.00012
    if Nt==4 and Nr==2 and MIMOCorrelation in ["high"]:
        value_a = 0.00010
    elif Nt==4 and Nr==4 and MIMOCorrelation in ["high"]:
        value_a = 0.00012
    elif Nt==2 and Nr==4 and MIMOCorrelation in ["medium"]:
        value_a = 0.00010
    elif Nt==4 and Nr==4 and MIMOCorrelation in ["medium"]:
        value_a = 0.00012
    else:
        value_a = 0
    
    #The values in Table B.2.3.1.2-2 have been adjusted for the 4x2 and 4x4 high correlation cases to 
    # insure the correlation matrix is positive semi-definite after round-off to 4 digit precision
    R_spat = (R_spat + value_a*np.eye(Nt*Nr,dtype=np.complex64))/(1+value_a)
    
    #this round-off to 4 digit precision causes non positive semi-definite for some configuration that is not mentioned in the spec, so disable it
    #R_spat = np.round(R_spat, decimals=4)

    return R_spat

def _Rspat_for_uniform_UL(Nt, Nr,MIMOCorrelation):
    #TS38.104 G.2.3.1 MIMO Correlation Matrices using Uniform Linear Array (ULA)
    assert Nt in [1,2,4] #based on Table G.2.3.1.1-2: UE correlation matrix
    assert Nr in [1,2,4,8] #based on Table G.2.3.1.1-1: gNB correlation matrix

    #G.2.3.1.2 MIMO Correlation Matrices at High, Medium and Low Level
    #Table G.2.3.1.2-1: Correlation for High Medium and Low Level
    assert MIMOCorrelation in ["high", "medium", "low"]
    TableG_2_3_1_2_1 = { "low": [0,0], "medium": [0.9,0.3],"high": [0.9,0.9]}
    alpha, beta = TableG_2_3_1_2_1[MIMOCorrelation]

    R_tx = _gen_correlation_matrix(Nt,beta) #UE correlation matrix
    R_rx = _gen_correlation_matrix(Nr,alpha) #gNB correlation matrix
    
    #TS38.104 Table G.2.3.1.1-3: correlation matrices
    R_spat = np.kron(R_tx, R_rx)

    #Where the value "a" is a scaling factor such that the smallest value is used to obtain a positive 
    # semi-definite result. For the 2x4 high correlation case, a=0.00010. For the 4x4 high correlation case, a=0.00012.
    # The same method is used to adjust the 4x4 medium correlation matrix in Table G.2.3.1.2-3 to insure 
    # the correlation matrix is positive semi-definite after round-off to 4-digit precision with a =0.00012.
    if Nt==2 and Nr==4 and MIMOCorrelation in ["high"]:
        value_a = 0.00010
    elif Nt==4 and Nr==4 and MIMOCorrelation in ["high"]:
        value_a = 0.00012
    elif Nt==4 and Nr==4 and MIMOCorrelation in ["medium"]:
        value_a = 0.00012
    elif Nt==2 and Nr==4 and MIMOCorrelation in ["medium"]:
        #TS38.104 Table G.2.3.1.2-3: MIMO correlation matrices for medium correlation 
        #provided R_spat for 2x4 case is not positive semi-definite, add value_a = 0.00010 to fix it
        value_a = 0.00010
    elif Nr == 8:
        value_a = 0.00010
    else:
        value_a = 0
    
    #The values in Table G.2.3.1.2-2 have been adjusted for the 2x4 and 4x4 high correlation cases to 
    # insure the correlation matrix is positive semi-definite after round-off to 4-digit precision. 
    R_spat = (R_spat + value_a*np.eye(Nt*Nr,dtype=np.complex64))/(1+value_a)
    #this round-off to 4 digit precision causes non positive semi-definite for some configuration that is not mentioned in the spec, so disable it
    #R_spat = np.round(R_spat, decimals=4)
    
    return R_spat

def _Rspat_for_cross_polar_DL(Nt, Nr,MIMOCorrelation):
    #TS38.101-4 B.2.3.2 is not very clear and I would like support only 1-D antenna
    #so this part refer to TS36.101 B.2.3A.2 Spatial Correlation Matrices using cross polarized antennas at eNB and UE sides
        
    assert Nt in [2,4,8] #based on B.2.3A.2.1
    assert Nr in [2,4] #based on TB.2.3A.2.2
    #Table B.2.3A.3-1
    assert MIMOCorrelation in ["high", "medium", "low"]
    TableB_2_3A_2_1 = { "low": [0,0,0], "medium": [0.3,0.6,0.2],"high": [0.9,0.9,0.3]}
    alpha, beta,gamma = TableB_2_3A_2_1[MIMOCorrelation]

    R_tx = _gen_correlation_matrix(Nt//2,alpha) #gNB correlation matrix
    R_rx = _gen_correlation_matrix(Nr//2,beta) #UE correlation matrix
    # polarization correlation matrix in TS38.101-4 B.2.3.2.1 Definition of MIMO Correlation Matrices using cross polarized antennas
    T_m = np.array([[1,0,-gamma,0], [0,1,0,gamma], [-gamma,0,1,0], [0,gamma,0,1]])

    P = _gen_permutation_matrix(Nt, Nr)
    #channel spatial correlation matrix
    # refer to TS38.104 G.2.3.2.1 Definition of MIMO Correlation Matrices using cross polarized antennas
    tmp1 = np.kron(R_tx, T_m)
    tmp1 = np.kron(tmp1, R_rx)
    R_spat = (P @ tmp1) @ P.T

    #Where the value “a” is a scaling factor such that the smallest value is used to obtain a positive 
    # semi-definite result. For the 8x2 high spatial correlation case, a=0.00010.
    if Nt==8 and Nr==2 and MIMOCorrelation in ["high"]:
        value_a = 0.00010
    else:
        value_a = 0

    #The values in Table B.2.3A.3-2 have been adjusted to insure the correlation matrix is positive 
    # semi-definite after roundoff to 4 digit precision. This is done using the equation:
    R_spat = (R_spat + value_a*np.eye(Nt*Nr,dtype=np.complex64))/(1+value_a)
    #this round-off to 4 digit precision causes non positive semi-definite for some configuration that is not mentioned in the spec, so disable it
    #R_spat = np.round(R_spat, decimals=4)

    return R_spat

def _Rspat_for_cross_polar_UL(Nt, Nr,MIMOCorrelation):
    #TS38.104 G.2.3.2 Multi-Antenna channel models using cross polarized antennas
    assert Nt in [1,2,4] #based on G.2.3.2.2.1 Spatial Correlation Matrices at UE side
    assert Nr in [2,4,8] #based on G.2.3.2.2.2 Spatial Correlation Matrices at gNB side

    #G.2.3.2.3 MIMO Correlation Matrices using cross polarized antennas only define low correlation case,refer to TS38.101-4 Table B.2.3A.3-1 to add "high", "medium" cases
        
    assert MIMOCorrelation in ["high", "medium", "low"]
    TableB_2_3A_2_1 = { "low": [0,0,0], "medium": [0.3,0.6,0.2],"high": [0.9,0.9,0.3]}
    alpha, beta,gamma = TableB_2_3A_2_1[MIMOCorrelation]

    #The MIMO channel correlation matrices defined in G.2.3.2 apply to two cases as presented below:
    #- One TX antenna and multiple RX antennas case, with cross polarized antennas used at gNB
    #- Multiple TX antennas and multiple RX antennas case, with cross polarized antennas used at both UE and gNB
    if Nt == 1:
        #one Tx antnna is not cross polarized antennas
        R_tx = _gen_correlation_matrix(Nt,beta) #UE correlation matrix
    else:
        R_tx = _gen_correlation_matrix(Nt//2,beta) #UE correlation matrix
    R_rx = _gen_correlation_matrix(Nr//2,alpha) #gNB correlation matrix
    #TS38.104 Table G.2.3.2.1-1: Polarization correlation matrix
    if Nt == 1:
        T_m = np.array([[1,-gamma], [-gamma,1]])
    else:
        T_m = np.array([[1,-gamma,0,0], [-gamma,1,0,0], [0,0,1,gamma],[0,0,gamma,1]])
    
    P = _gen_permutation_matrix(Nt, Nr)

    #channel spatial correlation matrix
    # refer to TS38.104 G.2.3.2.1 Definition of MIMO Correlation Matrices using cross polarized antennas
    tmp1 = np.kron(R_tx, T_m)
    tmp1 = np.kron(tmp1, R_rx)
    R_spat = (P @ tmp1) @ P.T

    #Where the value “a” is a scaling factor such that the smallest value is used to obtain a positive 
    # semi-definite result. For the 8x2 high spatial correlation case, a=0.00010.
    if Nt==2 and Nr==8 and MIMOCorrelation in ["high"]:
        value_a = 0.00010
    else:
        value_a = 0

    #The values in Table B.2.3A.3-2 have been adjusted to insure the correlation matrix is positive 
    # semi-definite after roundoff to 4 digit precision. This is done using the equation:
    R_spat = (R_spat + value_a*np.eye(Nt*Nr,dtype=np.complex64))/(1+value_a)
    #this round-off to 4 digit precision causes non positive semi-definite for some configuration that is not mentioned in the spec, so disable it
    #R_spat = np.round(R_spat, decimals=4)

    return R_spat


def _gen_permutation_matrix(Nt, Nr):
    #permutation matrix based on TS38.104 G.2.3.2.1 Definition of MIMO Correlation Matrices using cross polarized antennas
    # which is the same with permutation matrix defined in TS38.101-4 B.2.3.2.1 Definition of MIMO Correlation Matrices using cross polarized antennas
    P = np.zeros((Nt*Nr,Nt*Nr))
    for i in range(1, Nr+1):
        for j in range(1,int(np.ceil(Nt/2))+1): #be careful, this is ceil(Nt/2)
            a = (j-1)*Nr + i
            b = 2*(j-1)*Nr + i
            P[a-1,b-1] = 1
        
    if Nt > 1:
        for i in range(1, Nr+1):
            for j in range(Nt//2+1, Nt+1):
                a = (j-1)*Nr + i
                b = 2*(j-Nt//2)*Nr -Nr + i
                P[a-1,b-1] = 1
    
    return P

def _is_positive_semidefinite(matrix, tol=1e-8):
    """
    Checks if a symmetric matrix is positive semidefinite.

    Args:
        matrix (np.ndarray): The square matrix to check.
        tol (float): Tolerance for eigenvalue comparison to zero.

    Returns:
        bool: True if the matrix is positive semidefinite, False otherwise.
    """
    # Ensure the matrix is symmetric (or approximately symmetric)
    # This check is good practice, though eigvalsh assumes symmetry.
    if not np.allclose(matrix, matrix.T):
        print("Warning: Matrix is not symmetric. Results may be unreliable.")

    # Calculate eigenvalues of the symmetric matrix
    eigenvalues = np.linalg.eigvalsh(matrix)

    # Check if all eigenvalues are non-negative within a tolerance
    return np.all(eigenvalues >= -tol)

def _gen_correlation_matrix(size, delta):
    """ generate corrlation matrix based on TS38.104 Table G.2.3.1.1-1: gNB correlation matrix
        it can also be used for UE correlation matrix and cross-polar gNB and UE correlation matrix
    """
    assert size in [1,2,4,8]
    R = np.eye(size,dtype=np.complex64) 
    
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

def gen_corr_MIMO_channel(R_spat,Nr,Nt,N):
    """generate N size of NrXNt corrH with Rspat correlation"""
    assert R_spat.shape[0] == Nr*Nt
    
    rng = np.random.default_rng()
    H = rng.normal(0,1,(Nr*Nt,N))

    #cholesky only support 2-D dimension
    L = np.linalg.cholesky(R_spat)
    vec_H = L @ H

    corrH = np.zeros((N,Nr,Nt),'c8')
    for n in range(N):
        corrH[n] = vec_H[:,n].reshape((Nr,Nt),order='F')
    
    return corrH


def Rspat_est(corrH):
    """ estimate RSpat from channel estimation result"""
    N,Nr,Nt = corrH.shape

    est_R_spat = np.zeros((Nr*Nt,Nr*Nt),'c8')
    
    for idx in range(N):
        sel_H = corrH[idx,:,:]
        #column first,[[1,2,3],[4,5,6]] reshape to [1,4,2,5,3,6]T
        vec_H = sel_H.reshape((Nr*Nt,1),order='F')
        est_R_spat += vec_H @ vec_H.conj().T

    #average
    est_R_spat = est_R_spat/(N)
    return est_R_spat

if __name__ == "__main__":
    """ run test"""
    
    Nr=2
    Nt=2
    R_spat = get_nr_MIMO_Rspat(Nt, Nr,  Polarization="uniform",direction="DL",MIMOCorrelation="customized",parameters=[0,0])
    corrH = gen_corr_MIMO_channel(R_spat,Nr,Nt,2000)
    est_R_spat = Rspat_est(corrH)
    
    assert np.array_equal(_gen_correlation_matrix(1,0), np.eye(1,dtype=np.complex64) )
    
    assert np.array_equal(_gen_correlation_matrix(2,0.2), np.array([[1,0.2],[0.2,1]],dtype=np.complex64))
    
    assert np.array_equal(_gen_correlation_matrix(2,0.2j), np.array([[1,0.2j],[-0.2j,1]],dtype=np.complex64))
    
    assert np.array_equal(_gen_correlation_matrix(4,0.3), 
            np.array([[1,0.3**(1/9),0.3**(4/9),0.3],    
                      [0.3**(1/9),1,0.3**(1/9),0.3**(4/9)], 
                      [0.3**(4/9),0.3**(1/9),1,0.3**(1/9)], 
                      [0.3,0.3**(4/9),0.3**(1/9),1]],dtype=np.complex64))
    
    assert np.array_equal(_gen_correlation_matrix(8,0.3), 
            np.array([[1,0.3**(1/49),0.3**(4/49),0.3**(9/49),0.3**(16/49),0.3**(25/49),0.3**(36/49),0.3],    
                      [0.3**(1/49),1,0.3**(1/49),0.3**(4/49),0.3**(9/49),0.3**(16/49),0.3**(25/49),0.3**(36/49)], 
                      [0.3**(4/49),0.3**(1/49),1,0.3**(1/49),0.3**(4/49),0.3**(9/49),0.3**(16/49),0.3**(25/49)], 
                      [0.3**(9/49),0.3**(4/49),0.3**(1/49),1,0.3**(1/49),0.3**(4/49),0.3**(9/49),0.3**(16/49)],
                      [0.3**(16/49),0.3**(9/49),0.3**(4/49),0.3**(1/49),1,0.3**(1/49),0.3**(4/49),0.3**(9/49)],
                      [0.3**(25/49),0.3**(16/49),0.3**(9/49),0.3**(4/49),0.3**(1/49),1,0.3**(1/49),0.3**(4/49)],
                      [0.3**(36/49),0.3**(25/49),0.3**(16/49),0.3**(9/49),0.3**(4/49),0.3**(1/49),1,0.3**(1/49)],
                      [0.3,0.3**(36/49),0.3**(25/49),0.3**(16/49),0.3**(9/49),0.3**(4/49),0.3**(1/49),1]],
                      dtype=np.complex64))

    from tests.channel_model import test_nr_spatial_correlation_matrix
    test_nr_spatial_correlation_matrix.test_verify_positive_semi_definite()

    test_nr_spatial_correlation_matrix.test_DL_uniform_high_correlation()
    test_nr_spatial_correlation_matrix.test_DL_uniform_medium_correlation()
    test_nr_spatial_correlation_matrix.test_DL_uniform_mediumA_correlation()
    test_nr_spatial_correlation_matrix.test_DL_uniform_low_correlation()

    test_nr_spatial_correlation_matrix.test_DL_cross_polar_high_correlation()

    test_nr_spatial_correlation_matrix.test_UL_uniform_high_correlation()
    test_nr_spatial_correlation_matrix.test_UL_uniform_medium_correlation()
    test_nr_spatial_correlation_matrix.test_UL_uniform_low_correlation()

    test_nr_spatial_correlation_matrix.test_customized_config()

    #verify 

    pass
    