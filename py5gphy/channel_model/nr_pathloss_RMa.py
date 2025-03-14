# -*- coding:utf-8 -*-
import numpy as np

class NrPathlossRMa():
    """ RMa : Rural Macro refer to Table 7.4.1-1: Pathloss models
    """
    def __init__(self, hBS=35, hUT=1.5, W=20, h=5, d2D=20):
        self.config = {}
        self.config["hBS"] = hBS #BS antenna height in meter
        self.config["hUT"] = hUT #UE height in meter
        self.config["W"] = W #avg. street width
        self.config["h"] = h #avg. building height
        self.config["d2D"] = d2D

        #validate
        assert (h>=5) and (h<=50)
        assert (W>=5) and (W<=50)
        assert (hBS>=10) and (hBS<=150)
        assert (hUT>=1) and (hUT<=10)
        assert (d2D >=10) and (d2D <= 10*1000)

    def get_config(self):
        return self.config
    
    def cal_dBP(self, freq_in_Hz):
        """ calculate breakpoint, refer to Table 7.4.1-1: Pathloss models note 5"""
        dBP = 2 * np.pi * self.config["hBS"] * self.config["hUT"] * freq_in_Hz / (3e8)
        return dBP
    
    def cal(self, freq_in_Hz, LOS):
        """ return :
                pathloss without shadow fading,  
                shadow fading std(standard deviation)
                LOS probability
        """
        hBS = self.config["hBS"]
        hUT = self.config["hUT"]
        W= self.config["W"]
        h= self.config["h"]
        d2D = self.config["d2D"]

        fc = freq_in_Hz/1e9 #get freq_in_Hz in GHz

        #LOD probability, Table 7.4.2-1 LOS probability
        if d2D <= 10:
            Pr_LOS = 1
        else:
            Pr_LOS = np.exp(-(d2D-10)/1000)

        d3D = np.sqrt(d2D**2 + (hBS-hUT)**2)
        dBP = self.cal_dBP(freq_in_Hz)
        if d2D <= dBP:
            #PL1
            PL_RMa_LOS = 20*np.log10(40*np.pi*d3D*fc/3) + min(0.03 * h**1.72, 10)*np.log10(d3D) \
                - min(0.044 * h**1.72, 14.77) + 0.002*np.log10(h)*d3D
            SF_std = 4
        else:
            #PL2
            PL1_dBP = 20*np.log10(40*np.pi*dBP*fc/3) + min(0.03 * h**1.72, 10)*np.log10(dBP) \
                - min(0.044 * h**1.72, 14.77) + 0.002*np.log10(h)*dBP
            PL_RMa_LOS = PL1_dBP + 40*np.log10(d3D/dBP)
            SF_std = 6
        
        if LOS == False:
            #NLOS
            PL_RMa_NLOS = 161.04 - 7.11*np.log10(W) + 7.5*np.log10(h) \
                        - (24.37 - 3.7 * (h/hBS)**2) * np.log10(hBS) \
                        + (43.42 - 3.11*np.log10(hBS)) * (np.log10(d3D) - 3) \
                        + 20*np.log10(fc) - (3.2 * (np.log10(11.75*hUT))**2 - 4.97)
            
            PL_RMa_NLOS = max(PL_RMa_LOS, PL_RMa_NLOS)
            SF_std = 8
            return [PL_RMa_NLOS, SF_std, Pr_LOS]
        else:
            #LOS
            return [PL_RMa_LOS, SF_std, Pr_LOS]

if __name__ == "__main__":
    nrPathlossRMa = NrPathlossRMa()
    freq_in_Hz = 2e9
    LOS = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossRMa.cal(freq_in_Hz, LOS)

    LOS = False
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossRMa.cal(freq_in_Hz, LOS)

    nrPathlossRMa.config["d2D"] = 3000
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossRMa.cal(freq_in_Hz, LOS)

    pass