# -*- coding:utf-8 -*-

import numpy as np

from py5gphy.polar import polar_path

class Pathlist ():
    """ polar SCL decoder path list
        N: polar length
        L: path list size
    """
    def __init__(self, LLR0, N, L):
        self.L = L
        self.paths = [polar_path.SCL_Path(LLR0, N) for m in range(L)]
        self.paths_status = [0]*L #0 is inactive, 1: active
        self.paths_status[0] = 1 #active first path
    
    def get_path(self,index):
        return self.paths[index]
    
    def active_path(self, index):
        self.paths_status[index] = 1
    
    def inactive_path(self, index):
        self.paths_status[index] = 0

    def get_path_status(self, index):
        return self.paths_status[index]

    def get_total_active_paths(self):
        return sum(self.paths_status)
    
    def get_inactive_path_idx(self):
        """ find first inactive path
            -1: no inacive path 
        """
        idx = self.paths_status.index(0) if 0 in self.paths_status else -1
        return idx

    def get_active_paths(self):
        active_paths = []
        for idx in range(self.L):
            if self.get_path_status(idx) == 1: #active
                active_paths.append([idx,self.get_path(idx)])
        return active_paths    