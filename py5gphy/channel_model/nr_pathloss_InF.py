# -*- coding:utf-8 -*-
import numpy as np

class NrPathlossInF():
    """ InF : Indoor Factory refer to Table 7.4.1-1: Pathloss models
        #InF-SL	Indoor Factory with Sparse clutter and Low base station height (both Tx and Rx are below the average height of the clutter)
        #InF-DL	Indoor Factory with Dense clutter and Low base station height (both Tx and Rx are below the average height of the clutter)
        #InF-SH	Indoor Factory with Sparse clutter and High base station height (Tx or Rx elevated above the clutter)
        #InF-DH	Indoor Factory with Dense clutter and High base station height (Tx or Rx elevated above the clutter)
        InF-HH	Indoor Factory with High Tx and High Rx (both elevated above the clutter)
    """
    def __init__(self, d3D=20, type = 'SL'):
        self.config = {}
        self.config["d3D"] = d3D #distance from BS antenna to UT antenna
        self.config["type"] = type

        #validate
        assert (d3D >=1) and (d3D <= 150)
        assert type in ['SL', 'DL', 'SH', 'DH', 'HH']

    def get_config(self):
        return self.config
    
    def cal(self, freq_in_Hz, LOS):
        """ return :
                pathloss without shadow fading,  
                shadow fading std(standard deviation)
                LOS probability
        """
        d3D = self.config["d3D"]
        type = self.config["type"]

        #validate
        assert (d3D >=1) and (d3D <= 150)
        assert type in ['SL', 'DL', 'SH', 'DH', 'HH']

        fc = freq_in_Hz/1e9 #get freq_in_Hz in GHz

        #LOD probability, Table 7.4.2-1 LOS probability
        Pr_LOS = 1 # to make it simple
        
        #LOS
        SF_std = 4.3
        PL_InF_LOS = 31.84 + 21.5*np.log10(d3D) + 19.0*np.log10(fc)
                            
        if LOS == False:
            #NLOS
            if type == 'SL':
                PL_InF_NLOS = 33 + 25.5*np.log10(d3D) + 20.0*np.log10(fc)
                SF_std = 5.7
            elif type == 'DL':
                PL_InF_NLOS = 18.6 + 35.7*np.log10(d3D) + 20.0*np.log10(fc)
                SF_std = 7.2
            elif type == 'SH':
                PL_InF_NLOS = 32.4 + 23.0*np.log10(d3D) + 20.0*np.log10(fc)
                SF_std = 5.8
            elif type == 'DH':
                PL_InF_NLOS = 33.63 + 21.9*np.log10(d3D) + 20.0*np.log10(fc)
                SF_std = 4.0
            else:
                #HH, not defined NLOS in the table, keep LOS value
                PL_InF_NLOS = PL_InF_LOS
                                
            PL_InF_NLOS = max(PL_InF_LOS, PL_InF_NLOS)                
            return [PL_InF_NLOS, SF_std, Pr_LOS]
        else:
            #LOS
            return [PL_InF_LOS, SF_std, Pr_LOS]

if __name__ == "__main__":
    nrPathlossInF = NrPathlossInF()

    print(nrPathlossInF.get_config())
    
    freq_in_Hz = 2e9
    LOS = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    LOS = False
    nrPathlossInF.config["type"] = 'SL'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    nrPathlossInF.config["type"] = 'DL'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    nrPathlossInF.config["type"] = 'SH'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    nrPathlossInF.config["type"] = 'DH'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    nrPathlossInF.config["type"] = 'HH'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInF.cal(freq_in_Hz, LOS)

    
    pass