# -*- coding: utf-8 -*-
import numpy as np
import pytest

from py5gphy.channel_model import nr_spatial_correlation_matrix
# fmt: off

def test_DL_uniform_high_correlation():
    #refer to TS38.101-4 Table B.2.3.1.2-2: MIMO correlation matrices for high correlation
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([[1,0.9],[0.9,1]],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=1,  Polarization="uniform",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([[1,0.9],[0.9,1]],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1, 0.9, 0.9, 0.81],[0.9, 1, 0.81, 0.9],[0.9, 0.81, 1, 0.9],[0.81, 0.9, 0.9, 1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1.0000, 0.8999, 0.9883, 0.8894, 0.9542, 0.8587, 0.8999, 0.8099],
        [0.8999, 1.0000, 0.8894, 0.9883, 0.8587, 0.9542, 0.8099, 0.8999],
        [0.9883, 0.8894, 1.0000, 0.8999, 0.9883, 0.8894, 0.9542, 0.8587],
        [0.8894, 0.9883, 0.8999, 1.0000, 0.8894, 0.9883, 0.8587, 0.9542],
        [0.9542, 0.8587, 0.9883, 0.8894, 1.0000, 0.8999, 0.9883, 0.8894],
        [0.8587, 0.9542, 0.8894, 0.9883, 0.8999, 1.0000, 0.8894, 0.9883],
        [0.8999, 0.8099, 0.9542, 0.8587, 0.9883, 0.8894, 1.0000, 0.8999],
        [0.8099, 0.8999, 0.8587, 0.9542, 0.8894, 0.9883, 0.8999, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894, 0.9541, 0.9430, 0.9105, 0.8587, 0.8999, 0.8894, 0.8587, 0.8099],
        [0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430, 0.9430, 0.9541, 0.9430, 0.9105, 0.8894, 0.8999, 0.8894, 0.8587],
        [0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767, 0.9105, 0.9430, 0.9541, 0.9430, 0.8587, 0.8894, 0.8999, 0.8894],
        [0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882, 0.8587, 0.9105, 0.9430, 0.9541, 0.8099, 0.8587, 0.8894, 0.8999],
        [0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894, 0.9541, 0.9430, 0.9105, 0.8587],
        [0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430, 0.9430, 0.9541, 0.9430, 0.9105],
        [0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767, 0.9105, 0.9430, 0.9541, 0.9430],
        [0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882, 0.8587, 0.9105, 0.9430, 0.9541],
        [0.9541, 0.9430, 0.9105, 0.8587, 0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894],
        [0.9430, 0.9541, 0.9430, 0.9105, 0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430],
        [0.9105, 0.9430, 0.9541, 0.9430, 0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767],
        [0.8587, 0.9105, 0.9430, 0.9541, 0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882],
        [0.8999, 0.8894, 0.8587, 0.8099, 0.9541, 0.9430, 0.9105, 0.8587, 0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999],
        [0.8894, 0.8999, 0.8894, 0.8587, 0.9430, 0.9541, 0.9430, 0.9105, 0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541],
        [0.8587, 0.8894, 0.8999, 0.8894, 0.9105, 0.9430, 0.9541, 0.9430, 0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882],
        [0.8099, 0.8587, 0.8894, 0.8999, 0.8587, 0.9105, 0.9430, 0.9541, 0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_DL_uniform_medium_correlation():
    #refer to TS38.101-4 Table B.2.3.1.2-3: MIMO correlation matrices for medium correlation
    
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="medium")
    ref_R_spat = np.array([
        [1, 0.9, 0.3, 0.27],[0.9, 1, 0.27, 0.3],[0.3,0.27,1,0.9],[0.27,0.3,0.9,1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="medium")
    ref_R_spat = np.array([
        [1.0000, 0.9882, 0.9541, 0.8999, 0.3000, 0.2965, 0.2862, 0.2700],
        [0.9882, 1.0000, 0.9882, 0.9541, 0.2965, 0.3000, 0.2965, 0.2862],
        [0.9541, 0.9882, 1.0000, 0.9882, 0.2862, 0.2965, 0.3000, 0.2965],
        [0.8999, 0.9541, 0.9882, 1.0000, 0.2700, 0.2862, 0.2965, 0.3000],
        [0.3000, 0.2965, 0.2862, 0.2700, 1.0000, 0.9882, 0.9541, 0.8999],
        [0.2965, 0.3000, 0.2965, 0.2862, 0.9882, 1.0000, 0.9882, 0.9541],
        [0.2862, 0.2965, 0.3000, 0.2965, 0.9541, 0.9882, 1.0000, 0.9882],
        [0.2700, 0.2862, 0.2965, 0.3000, 0.8999, 0.9541, 0.9882, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="medium")
    ref_R_spat = np.array([
        [1.0000, 0.9000, 0.8748, 0.7873, 0.5856, 0.5271, 0.3000, 0.2700],
        [0.9000, 1.0000, 0.7873, 0.8748, 0.5271, 0.5856, 0.2700, 0.3000],
        [0.8748, 0.7873, 1.0000, 0.9000, 0.8748, 0.7873, 0.5856, 0.5271],        
        [0.7873, 0.8748, 0.9000, 1.0000, 0.7873, 0.8748, 0.5271, 0.5856],
        [0.5856, 0.5271, 0.8748, 0.7873, 1.0000, 0.9000, 0.8748, 0.7873],
        [0.5271, 0.5856, 0.7873, 0.8748, 0.9000, 1.0000, 0.7873, 0.8748],
        [0.3000, 0.2700, 0.5856, 0.5271, 0.8748, 0.7873, 1.0000, 0.9000],
        [0.2700, 0.3000, 0.5271, 0.5856, 0.7873, 0.8748, 0.9000, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_DL_uniform_mediumA_correlation():
    #refer to TS38.101-4 Table B.2.3.1.2-4: MIMO correlation matrices for medium correlation A
    
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="mediumA")
    ref_R_spat = np.array([
        [1, 0.9, 0.6561, 0.3874],[0.9,1, 0.9, 0.6561],[0.6561,0.9,1, 0.9],[0.3874,0.6561,0.9,1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="mediumA")
    ref_R_spat = np.array([
        [1.0000, 0.9000, 0.6561, 0.3874, 0.3000, 0.2700, 0.1968, 0.1162],
        [0.9000, 1.0000, 0.9000, 0.6561, 0.2700, 0.3000, 0.2700, 0.1968],
        [0.6561, 0.9000, 1.0000, 0.9000, 0.1968, 0.2700, 0.3000, 0.2700],
        [0.3874, 0.6561, 0.9000, 1.0000, 0.1162, 0.1968, 0.2700, 0.3000],
        [0.3000, 0.2700, 0.1968, 0.1162, 1.0000, 0.9000, 0.6561, 0.3874],
        [0.2700, 0.3000, 0.2700, 0.1968, 0.9000, 1.0000, 0.9000, 0.6561],
        [0.1968, 0.2700, 0.3000, 0.2700, 0.6561, 0.9000, 1.0000, 0.9000],
        [0.1162, 0.1968, 0.2700, 0.3000, 0.3874, 0.6561, 0.9000, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_DL_uniform_low_correlation():
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(4,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(8,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(8,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=4,  Polarization="uniform",direction="DL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(16,dtype=np.complex64))

def test_DL_cross_polar_high_correlation():
    #refer to TS36.101 Table B.2.3A.3-2: MIMO correlation matrices for high spatial correlation
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=2,  Polarization="cross-polar",direction="DL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1.0000, 0.0000, 0.9000, 0.0000, -0.3000, 0.0000, -0.2700, 0.0000],
        [0.0000, 1.0000, 0.0000, 0.9000, 0.0000, 0.3000, 0.0000, 0.2700],
        [0.9000, 0.0000, 1.0000, 0.0000, -0.2700, 0.0000, -0.3000, 0.0000],
        [0.0000, 0.9000, 0.0000, 1.0000, 0.0000, 0.2700, 0.0000, 0.3000],
        [-0.3000, 0.0000, -0.2700, 0.0000, 1.0000, 0.0000, 0.9000, 0.0000],
        [0.0000, 0.3000, 0.0000, 0.2700, 0.0000, 1.0000, 0.0000, 0.9000],
        [-0.2700, 0.0000, -0.3000, 0.0000, 0.9000, 0.0000, 1.0000, 0.0000],
        [0.0000, 0.2700, 0.0000, 0.3000, 0.0000, 0.9000, 0.0000, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_UL_uniform_high_correlation():
    #refer to TS38.104 Table G.2.3.1.2-2: MIMO correlation matrices for high correlation
    
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=2,  Polarization="uniform",direction="UL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1, 0.9],[0.9, 1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=2,  Polarization="uniform",direction="UL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1, 0.9, 0.9, 0.81],[0.9, 1, 0.81, 0.9],[0.9, 0.81, 1, 0.9],[0.81, 0.9, 0.9, 1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1.0000, 0.9883, 0.9542, 0.8999, 0.8999, 0.8894, 0.8587, 0.8099],
        [0.9883, 1.0000, 0.9883, 0.9542, 0.8894, 0.8999, 0.8894, 0.8587],
        [0.9542, 0.9883, 1.0000, 0.9883, 0.8587, 0.8894, 0.8999, 0.8894],
        [0.8999, 0.9542, 0.9883, 1.0000, 0.8099, 0.8587, 0.8894, 0.8999],
        [0.8999, 0.8894, 0.8587, 0.8099, 1.0000, 0.9883, 0.9542, 0.8999],
        [0.8894, 0.8999, 0.8894, 0.8587, 0.9883, 1.0000, 0.9883, 0.9542],
        [0.8587, 0.8894, 0.8999, 0.8894, 0.9542, 0.9883, 1.0000, 0.9883],
        [0.8099, 0.8587, 0.8894, 0.8999, 0.8999, 0.9542, 0.9883, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

        

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="high")
    ref_R_spat = np.array([
        [1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894, 0.9541, 0.9430, 0.9105, 0.8587, 0.8999, 0.8894, 0.8587, 0.8099],
        [0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430, 0.9430, 0.9541, 0.9430, 0.9105, 0.8894, 0.8999, 0.8894, 0.8587],
        [0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767, 0.9105, 0.9430, 0.9541, 0.9430, 0.8587, 0.8894, 0.8999, 0.8894],
        [0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882, 0.8587, 0.9105, 0.9430, 0.9541, 0.8099, 0.8587, 0.8894, 0.8999],
        [0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894, 0.9541, 0.9430, 0.9105, 0.8587],
        [0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430, 0.9430, 0.9541, 0.9430, 0.9105],
        [0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767, 0.9105, 0.9430, 0.9541, 0.9430],
        [0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882, 0.8587, 0.9105, 0.9430, 0.9541],
        [0.9541, 0.9430, 0.9105, 0.8587, 0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999, 0.9882, 0.9767, 0.9430, 0.8894],
        [0.9430, 0.9541, 0.9430, 0.9105, 0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541, 0.9767, 0.9882, 0.9767, 0.9430],
        [0.9105, 0.9430, 0.9541, 0.9430, 0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882, 0.9430, 0.9767, 0.9882, 0.9767],
        [0.8587, 0.9105, 0.9430, 0.9541, 0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000, 0.8894, 0.9430, 0.9767, 0.9882],
        [0.8999, 0.8894, 0.8587, 0.8099, 0.9541, 0.9430, 0.9105, 0.8587, 0.9882, 0.9767, 0.9430, 0.8894, 1.0000, 0.9882, 0.9541, 0.8999],
        [0.8894, 0.8999, 0.8894, 0.8587, 0.9430, 0.9541, 0.9430, 0.9105, 0.9767, 0.9882, 0.9767, 0.9430, 0.9882, 1.0000, 0.9882, 0.9541],
        [0.8587, 0.8894, 0.8999, 0.8894, 0.9105, 0.9430, 0.9541, 0.9430, 0.9430, 0.9767, 0.9882, 0.9767, 0.9541, 0.9882, 1.0000, 0.9882],
        [0.8099, 0.8587, 0.8894, 0.8999, 0.8587, 0.9105, 0.9430, 0.9541, 0.8894, 0.9430, 0.9767, 0.9882, 0.8999, 0.9541, 0.9882, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_UL_uniform_medium_correlation():
    #refer to TS38.104 Table G.2.3.1.2-2: MIMO correlation matrices for high correlation
    
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=2,  Polarization="uniform",direction="UL",MIMOCorrelation="medium")
    ref_R_spat = np.array([
        [1, 0.9, 0.3, 0.27],[0.9, 1, 0.27, 0.3],[0.3,0.27,1,0.9],[0.27,0.3,0.9,1]
        ],dtype=np.complex64)
    assert np.array_equal(R_spat,ref_R_spat)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="medium")
    
    #spec_ref_R_spat is provided by TS38.104 able G.2.3.1.2-3: MIMO correlation matrices for medium correlation 
    # and it is not positive semi-definite
    spec_ref_R_spat = np.array([
        [1.0000, 0.9884, 0.9543, 0.9000, 0.3000, 0.2965, 0.2863, 0.2700],
        [0.9884, 1.0000, 0.9884, 0.9543, 0.2965, 0.3000, 0.2965, 0.2863],
        [0.9543, 0.9884, 1.0000, 0.9884, 0.2863, 0.2965, 0.3000, 0.2965],
        [0.9000, 0.9543, 0.9884, 1.0000, 0.2700, 0.2863, 0.2965, 0.3000],
        [0.3000, 0.2965, 0.2863, 0.2700, 1.0000, 0.9884, 0.9543, 0.9000],
        [0.2965, 0.3000, 0.2965, 0.2863, 0.9884, 1.0000, 0.9884, 0.9543],
        [0.2863, 0.2965, 0.3000, 0.2965, 0.9543, 0.9884, 1.0000, 0.9884],
        [0.2700, 0.2863, 0.2965, 0.3000, 0.9000, 0.9543, 0.9884, 1.0000]
        ],dtype=np.complex64)
    
    #ref R_spat with value_a = 0.00010
    ref_R_spat = np.array([
        [1.0000, 0.9882, 0.9541, 0.8999, 0.3000, 0.2965, 0.2862, 0.2700],
        [0.9882, 1.0000, 0.9882, 0.9541, 0.2965, 0.3000, 0.2965, 0.2862],
        [0.9541, 0.9882, 1.0000, 0.9882, 0.2862, 0.2965, 0.3000, 0.2965],
        [0.8999, 0.9541, 0.9882, 1.0000, 0.2700, 0.2862, 0.2965, 0.3000],
        [0.3000, 0.2965, 0.2862, 0.2700, 1.0000, 0.9882, 0.9541, 0.8999],
        [0.2965, 0.3000, 0.2965, 0.2862, 0.9882, 1.0000, 0.9882, 0.9541],
        [0.2862, 0.2965, 0.3000, 0.2965, 0.9541, 0.9882, 1.0000, 0.9882],
        [0.2700, 0.2862, 0.2965, 0.3000, 0.8999, 0.9541, 0.9882, 1.0000]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_UL_uniform_low_correlation():
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(4,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(8,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=8,  Polarization="uniform",direction="UL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(16,dtype=np.complex64))

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=4, Nr=4,  Polarization="uniform",direction="UL",MIMOCorrelation="low")
    assert np.array_equal(R_spat,np.eye(16,dtype=np.complex64))

def test_customized_config():
    #[alpha,beta] value is directly provided in customized case
    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="customized",parameters=[0.9,0.9])
    ref_R_spat = np.array([[1,0.9],[0.9,1]],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

    R_spat = nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=2, Nr=2,  Polarization="uniform",direction="DL",MIMOCorrelation="customized",parameters=[0.9,0.9])
    ref_R_spat = np.array([
        [1, 0.9, 0.9, 0.81],[0.9, 1, 0.81, 0.9],[0.9, 0.81, 1, 0.9],[0.81, 0.9, 0.9, 1]
        ],dtype=np.complex64)
    assert np.allclose(R_spat,ref_R_spat,atol=1e-4)

def test_verify_positive_semi_definite():
    #verify that R_spat is positive semi-definite for any configuration
    #the function finishimg running without any assert indicate that R_spat is positive semi-definite for any configuration
    
    #DL, uniform,
    for Nt in [1,2,4]:
        for Nr in [1,2,4]:
            for MIMOCorrelation in ["high", "medium", "mediumA", "low"]:
                nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=Nt, Nr=Nr,Polarization="uniform",direction="DL",MIMOCorrelation=MIMOCorrelation)
    
    nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=1, Nr=8,  Polarization="uniform",direction="UL",MIMOCorrelation="high")
    #UL, uniform,
    for Nt in [1,2,4]:
        for Nr in [1,2,4,8]:
            for MIMOCorrelation in ["high", "medium", "low"]:
                nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=Nt, Nr=Nr,Polarization="uniform",direction="UL",MIMOCorrelation=MIMOCorrelation)
    
    # DL corss-polar
    for Nt in [2,4,8]:
        for Nr in [2,4]:
            for MIMOCorrelation in ["high", "medium", "low"]:
                nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=Nt, Nr=Nr,Polarization="cross-polar",direction="DL",MIMOCorrelation=MIMOCorrelation)
    
    # UL corss-polar
    for Nt in [1,2,4]:
        for Nr in [2,4,8]:
            for MIMOCorrelation in ["high", "medium", "low"]:
                nr_spatial_correlation_matrix.get_nr_MIMO_Rspat(Nt=Nt, Nr=Nr,Polarization="cross-polar",direction="UL",MIMOCorrelation=MIMOCorrelation)
# fmt: on

        
















