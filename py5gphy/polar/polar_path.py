# -*- coding:utf-8 -*-

import numpy as np

class SC_Path_no_opt ():
    """ define Polar SC decoder path without path buffer optimization, buffer size = N*log2(N)
        based on "List Decoding of Polar Codes" from Algorithm1 to Algorithm 4
        one path include both LLR matrix and bit matrix
    """
    def __init__(self, LLR0, N):
        """  N is polar decode input size 
            LLR0 is layer 0 LLR values
        """
        m = int(np.ceil(np.log2(N))) #m = log2(N)
        #define m+1 layer X N value per layer, for layer n, there are total 2^(m-n) branch with 2^n value per each branch
        #LLR is LLR values for each layers, B is estimated hard bits estimatio for each layers
        self.LLR = np.zeros((m+1,N))
        self.LLR[0,:] = LLR0
        self.B = -1*np.ones((m+1,N),'i2')
        self.m = m
        self.N = N
    
    def setB(self,value, layer, branch, phase):
        offset = branch * 2**layer + phase
        self.B[layer][offset] = value
    
    def getB(self, layer, branch, phase):
        offset = branch * 2**layer + phase
        return self.B[layer][offset] 
    
    def setLLR(self,value, layer, branch, phase):
        offset = branch * 2**layer + phase
        self.LLR[layer][offset] = value
    
    def getLLR(self, layer, branch, phase):
        offset = branch * 2**layer + phase
        return self.LLR[layer][offset]

    def get_u_seq(self):
        """ return polar decoded bits, which is all values in layer=m"""
        u_seq = self.B[self.m,:]
        return u_seq

class SC_Path_opt1 ():
    """ define Polar SC decoder path with path buffer optimization, 
        LLR buffer size = 2*N-1, B buffer size = N+2*(2N-1)
        based on "List Decoding of Polar Codes" from Algorithm5 to Algorithm 7
        one path include both LLR matrix and bit matrix
    """
    def __init__(self, LLR0, N):
        """  N is polar decode input size 
            LLR0 is layer 0 LLR values
        """
        m = int(np.ceil(np.log2(N))) #m = log2(N)
        #there are total m+1 layers, for layer n, branch number = 2^(m-n) 
        #LLR is LLR values for each layers, B is estimated hard bits estimatio for each layers
        #LLR of each branch need one value size, B ofeach branch need two value size
        #
        self.LLR = np.zeros(2*N-1)
        self.LLR[0:N] = LLR0
        self.B = -1*np.ones(2*(2*N-1),'i2')
        self.U = -1*np.ones(N,'i2') #decoded bit seq, 
        self.m = m
        self.N = N
    
    def setB(self,value, layer, branch, phase):
        #each branch has two B value, put even value on position 0, put odd value on position 1
        offset = 2*(2**(self.m+1) - 2**(self.m+1-layer))  + branch*2 + (phase % 2)
        self.B[offset] = value
        if layer == self.m:
            self.U[phase] = value
    
    def getB(self, layer, branch, phase):
        #each branch has two B value, put even value on position 0, put odd value on position 1
        offset = 2*(2**(self.m+1) - 2**(self.m+1-layer))  + branch*2 + (phase % 2)
        return self.B[offset] 
    
    def setLLR(self,value, layer, branch, phase):
        #each branch has one LLR value
        offset = (2**(self.m+1) - 2**(self.m+1-layer))  + branch
        self.LLR[offset] = value
    
    def getLLR(self, layer, branch, phase):
        #each branch has one LLR value
        offset = (2**(self.m+1) - 2**(self.m+1-layer))  + branch
        return self.LLR[offset]
    
    def get_u_seq(self):
        """ return polar decoded bits, which is all values in layer=m"""
        return self.U

class SC_Path_opt2 ():
    """ define Polar SC decoder path with path buffer optimization method 2, 
        there are N B value in layer 0 which is not necessary. removing layer0 B value can reduce B buffer size to N+2*(N-1)
        for SCL decoder, all path shared the same layer0 LLR value.LLR buffer doesn;t need N layer0 LLR value which can reduce LLR buffer size to N-1
        one path include both LLR matrix and bit matrix
    """
    def __init__(self, LLR0, N):
        """  N is polar decode input size 
            LLR0 is layer 0 LLR values
        """
        m = int(np.ceil(np.log2(N))) #m = log2(N)
        #there are total m+1 layers, for layer n, branch number = 2^(m-n) 
        #LLR is LLR values for each layers, B is estimated hard bits estimatio for each layers
        #LLR of each branch need one value size, B ofeach branch need two value size
        #
        self.LLR = np.zeros(N-1)
        self.LLR0 = LLR0
        self.B = -1*np.ones(2*(N-1),'i2')
        self.U = -1*np.ones(N,'i2') #decoded bit seq, 
        self.m = m
        self.N = N
    
    def setB(self,value, layer, branch, phase):
        #each branch has two B value, put even value on position 0, put odd value on position 1
        if layer == 0:
            return
        offset = 2*(2**self.m - 2**(self.m-(layer-1)))  + branch*2 + (phase % 2)
        self.B[offset] = value
        if layer == self.m:
            self.U[phase] = value
    
    def getB(self, layer, branch, phase):
        #each branch has two B value, put even value on position 0, put odd value on position 1
        if layer == 0:
            return -1
        offset = 2*(2**self.m - 2**(self.m-(layer-1)))  + branch*2 + (phase % 2)
        return self.B[offset] 
    
    def setLLR(self,value, layer, branch, phase):
        #each branch has one LLR value
        if layer == 0:
            assert 0
        offset = (2**self.m - 2**(self.m-(layer-1)))  + branch
        self.LLR[offset] = value
    
    def getLLR(self, layer, branch, phase):
        #each branch has one LLR value
        if layer == 0:
            return self.LLR0[branch]
        offset = (2**self.m - 2**(self.m-(layer-1)))  + branch
        return self.LLR[offset]
    
    def get_u_seq(self):
        """ return polar decoded bits, which is all values in layer=m"""
        return self.U
    
    def clone(self, clone2path):
        clone2path.LLR = self.LLR.copy()
        clone2path.B = self.B.copy()
        clone2path.U = self.U.copy()
        clone2path.m = self.m
        clone2path.N = self.N

class SCL_Path (SC_Path_opt2):
    """ define SCL Polar decoder path based on SC_Path_opt2
        and add Path Metric(PM) related processing
        PM calculation is based on "LLR-Based Successive Cancellation List Decoding of Polar Codes" equation 12
        
    """
    def __init__(self, LLR0, N):
        super().__init__(LLR0,N)
        self.PM = 0 #currect PM
        self.nextPM = [0,0] #next stage PM for u=0 and u= 1
    
    def clone(self,clone2path):
        super().clone(clone2path)
        clone2path.PM = self.PM
        clone2path.nextPM = self.nextPM.copy()

    def update_BandPM(self,phase,u):
        """ set B on the phase of layer m, and then update PM
        """
        self.setB(u, self.m, 0, phase)
        LLR = self.getLLR(self.m,0,phase)
        if u != (1-np.sign(LLR))/2:
            self.PM = self.PM + abs(LLR)
    
    def gen_nextPM(self,phase):
        """ generate next stage PM values for u=0 and u=1
        nextPM[0] is u=0 PM, nextPM[1] is u=1 PM
        """
        LLR = self.getLLR(self.m,0,phase)
        
        if 0 == (1-np.sign(LLR))/2: #u=0 a
            self.nextPM[0] = self.PM
            self.nextPM[1] = self.PM + abs(LLR)
        else:
            self.nextPM[0] = self.PM + abs(LLR)
            self.nextPM[1] = self.PM
