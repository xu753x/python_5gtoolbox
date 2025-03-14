# -*- coding:utf-8 -*-
import numpy as np

class NrPathlossInH():
    """ InH Office: Indoor Hotspot refer to Table 7.4.1-1: Pathloss models
    """
    def __init__(self, d3D=20, hBS=3, hUT=1,optional=False, office_type = 'Mixed'):
        self.config = {}
        self.config["d3D"] = d3D #distance from BS antenna to UT antenna
        #refer Table 7.2-2: Evaluation parameters for indoor-office scenarios
        #default hBS = 3and hUT = 1
        self.config["hBS"] = hBS #BS antenna height in meter
        self.config["hUT"] = hUT #UE height in meter
        self.config["optional"] = optional # used for NLOS optional path loss
        self.config["office_type"] = office_type

        #validate
        assert (d3D >=1) and (d3D <= 150)
        assert office_type in ['Mixed', 'Open']

    def get_config(self):
        return self.config
    
    def cal(self, freq_in_Hz, LOS):
        """ return :
                pathloss without shadow fading,  
                shadow fading std(standard deviation)
                LOS probability
        """
        d3D = self.config["d3D"]
        hBS = self.config["hBS"]
        hUT = self.config["hUT"]
        optional = self.config["optional"]
        office_type = self.config["office_type"]

        fc = freq_in_Hz/1e9 #get freq_in_Hz in GHz

        #LOD probability, Table 7.4.2-1 LOS probability
        d2D = np.sqrt(d3D**2 - (hBS-hUT)**2)
        if office_type == 'Mixed':
            #Mixed Office
            if d2D <= 1.2:
                Pr_LOS = 1
            elif d2D < 6.5:
                Pr_LOS = np.exp(-(d2D-1.2)/4.7)
            else:
                Pr_LOS = np.exp(-(d2D-6.5)/32.6)*0.32
        else:
            #Open office
            if d2D <= 5:
                Pr_LOS = 1
            elif d2D <= 49:
                Pr_LOS = np.exp(-(d2D-5)/70.8)
            else:
                Pr_LOS = np.exp(-(d2D-49)/211.7)*0.54

        #LOS
        SF_std = 3
        PL_InH_LOS = 32.4 + 17.3*np.log10(d3D) + 20*np.log10(fc)
                            
        if LOS == False:
            #NLOS
            if optional == False:
                PL_InH_NLOS = 38.3*np.log10(d3D) + 17.3 + 24.9*np.log10(fc)
                PL_InH_NLOS = max(PL_InH_LOS, PL_InH_NLOS)
                SF_std = 8.03
            else:
                PL_InH_NLOS = 32.4 + 20*np.log10(fc) + 31.9*np.log10(d3D)
                SF_std = 8.29
            return [PL_InH_NLOS, SF_std, Pr_LOS]
        else:
            #LOS
            return [PL_InH_LOS, SF_std, Pr_LOS]

if __name__ == "__main__":
    nrPathlossInH = NrPathlossInH()

    print(nrPathlossInH.get_config())
    
    freq_in_Hz = 2e9
    LOS = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInH.cal(freq_in_Hz, LOS)

    LOS = False
    nrPathlossInH.config["office_type"] = 'Open'
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInH.cal(freq_in_Hz, LOS)

    nrPathlossInH.config["optional"] = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossInH.cal(freq_in_Hz, LOS)

    pass