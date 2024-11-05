# -*- coding:utf-8 -*-

import numpy as np
import math

def get_precoding_matrix(num_of_layers, nNrOfAntennaPorts, nPMI):
    """ for codebook based transmission only
    """
    if num_of_layers == 1 and nNrOfAntennaPorts == 1:
        W = np.array([1],'c8')
        return W
    
    if num_of_layers == 1 and nNrOfAntennaPorts == 2:
        # 38.211 Table 6.3.1.5-1: Precoding matrix W for single-layer transmission using two antenna ports.
        assert nPMI <= 5
        table63151 = np.array([[1,0],[0,1],[1,1],[1,-1],[1,1j],[1,-1j]],'c8')/math.sqrt(2)
        W = np.zeros((2,1),'c8')
        W[0] = table63151[nPMI][0]
        W[1] = table63151[nPMI][1]
        return W
    
    if num_of_layers == 2 and nNrOfAntennaPorts == 2:
        # 38.211 Table 6.3.1.5-4: Precoding matrix W for two-layer transmission using two antenna ports 
        # with transform precoding disabled
        assert nPMI <= 2
        if nPMI == 0:
            W = np.array([[1,0],[0,1]],'c8')/math.sqrt(2)
        elif nPMI == 1:
            W = np.array([[1,1],[1,-1]],'c8')/2
        elif nPMI == 2:
            W = np.array([[1,1],[1j,-1j]],'c8')/2
        return W
