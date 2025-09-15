# -*- coding:utf-8 -*-
import numpy as np

from py5gphy.channel_model import nr_pathloss_RMa
from py5gphy.channel_model import nr_pathloss_InF
from py5gphy.channel_model import nr_pathloss_InH
from py5gphy.channel_model import nr_pathloss_UMa
from py5gphy.channel_model import nr_pathloss_UMi

class NrPathloss():
    """ NR Pathloss class
    refer to  3GPP TR 38.901 V16.1.0 (2019-12) 7.4
    """
    def __init__(self, Scenario="RMa", freq_in_Hz=3e9, LOS=True):
        self.set_Scenario(Scenario, freq_in_Hz, LOS)
    
    def set_Scenario(self,Scenario, freq_in_Hz=3e9, LOS=True):
        #Scenario ('UMa'(default),'UMi','RMa','InH','InF-SL','InF-DL','InF-SH','InF-DH','InF-HH')
        #UMa	Urban Macro, 
        # UMi	Urban Micro, 
        # RMa	Rural Macro
        #InH	Indoor Hotspot, 
        #InF-SL	Indoor Factory with Sparse clutter and Low base station height (both Tx and Rx are below the average height of the clutter)
        #InF-DL	Indoor Factory with Dense clutter and Low base station height (both Tx and Rx are below the average height of the clutter)
        #InF-SH	Indoor Factory with Sparse clutter and High base station height (Tx or Rx elevated above the clutter)
        #InF-DH	Indoor Factory with Dense clutter and High base station height (Tx or Rx elevated above the clutter)

        self.Scenario = Scenario

        if Scenario == 'RMa':
            self.PLmodel = nr_pathloss_RMa.NrPathlossRMa()
        elif Scenario == 'UMa':
            self.PLmodel = nr_pathloss_UMa.NrPathlossUMa()
        elif Scenario == 'UMi':
            self.PLmodel = nr_pathloss_UMi.NrPathlossUMi()
        elif Scenario == 'InH':
            self.PLmodel = nr_pathloss_InH.NrPathlossInH()
        elif Scenario == 'InF':
            self.PLmodel = nr_pathloss_InF.NrPathlossInF()
        else:
            assert 0

        self.freq_in_Hz = freq_in_Hz
        self.LOS = True #line of sight

    def get_supported_Scenario_list(self):
        return ['UMa','UMi','RMa','InH','InF']
    
    def get_config(self):
        """ return Scenario, Scenario, config, freq_in_Hz, LOS
        """
        config = self.PLmodel.get_config()
        return {"Scenario":self.Scenario, "Scenario_config":config, "freq_in_Hz":self.freq_in_Hz, "LOS":self.LOS}

    def gen_pathloss_info(self):
        """ return [PL_no_shadow, SF_std, Pr_LOS]
        Table 7.4.1-1: Pathloss models
        """
        return self.PLmodel.cal(self.freq_in_Hz, self.LOS)
    
    def gen_new_pathloss(self):
        """generate pathloss based on PL_no_shadow and shadow fading standard deviation
            pathloss = PL_no_shadow + shadow-variable, 
            shadow-variable is (0, SF_std) Gaussian process
        """
        [PL_no_shadow, SF_std, Pr_LOS] = self.gen_pathloss_info()
        PL_with_shadow = PL_no_shadow + np.random.normal(0, 10**(SF_std/10), 1)
        return PL_with_shadow

if __name__ == "__main__":
    nrPathloss = NrPathloss()
    print(nrPathloss.get_supported_Scenario_list())
    print(nrPathloss.get_config())
    print(nrPathloss.gen_pathloss_info())
    print(nrPathloss.gen_new_pathloss())

    nrPathloss.set_Scenario("UMi")
    print(nrPathloss.get_config())

    nrPathloss.set_Scenario("UMa")
    print(nrPathloss.get_config())

    nrPathloss.set_Scenario("InH")
    print(nrPathloss.get_config())

    nrPathloss.set_Scenario("InF")
    print(nrPathloss.get_config())
    pass