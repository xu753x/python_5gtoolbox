# -*- coding:utf-8 -*-
import numpy as np

class NrPathlossUMi():
    """ UMi-street Canyon:	Urban Micro refer to Table 7.4.1-1: Pathloss models
    """
    def __init__(self, hUT=1.5, d2D=20, hE=1, optional=False):
        self.config = {}
        self.config["hBS"] = 10 #BS antenna height in meter
        self.config["hUT"] = hUT #UE height in meter
        self.config["d2D"] = d2D
        self.config["hE"] = hE #effective environment height
        self.config["optional"] = optional # used for NLOS optional path loss

        self.hE_pro_list = self.get_hE_distribution() #get supported [hE, probability] list

        #validate
        assert (hUT>=1.5) and (hUT<=22.5)
        assert (d2D >=10) and (d2D <= 5*1000)

    def get_config(self):
        return self.config
    
    def get_hE_distribution(self):
        """ return all possible hE values and probability list
        refer to Table 7.4.1-1 note 1
        """
        d2D = self.config["d2D"]
        hUT = self.config["hUT"]
        if hUT < 13:
            #C(d2D,hUT) = 0, only support [hE=1 and probability = 1]
            return [[1,1]] 
        
        #cal g(d2D)
        if d2D <= 18:
            g_d2D = 0
        else:
            g_d2D = 5/4* (d2D/100)**3 * np.exp(-d2D/150)
        
        #cal C(d2D,hUT)
        C_d2D_hUT = ((hUT-13)/10)**1.5*g_d2D
        if C_d2D_hUT == 0:
            #only support [hE=1 and probability = 1]
            return [[1,1]] 
        
        #get hE=1 probability
        P1 = 1/(1+C_d2D_hUT)

        #get discrete uniform distribution uniform(12,15,…,(hUT-1.5)) hE list
        hE_list = list(np.arange(12, hUT-1.5, 3))
        hE_list.append(hUT-1.5)
        P2 = (1-P1)/len(hE_list) #probability of each hE value
        
        #generate [hE, probability] list
        hE_pro_list = [[1, P1]] #hE =1 and probability
        for hE in hE_list:
            hE_pro_list.append([hE,P2])
        return hE_pro_list

    def cal_dBP(self, freq_in_Hz):
        """ calculate breakpoint, refer to Table 7.4.1-1: Pathloss models note 1"""
        hBS = self.config["hBS"]
        hUT = self.config["hUT"]
        hE = self.config["hE"]

        hBSp = hBS - hE
        hUTp = hUT - hE

        dBP = 4 * hBSp * hUTp * freq_in_Hz / (3e8)
        return dBP
    
    def cal(self, freq_in_Hz, LOS):
        """ return :
                pathloss without shadow fading,  
                shadow fading std(standard deviation)
                LOS probability
        """
        hBS = self.config["hBS"]
        hUT = self.config["hUT"]
        d2D = self.config["d2D"]
        optional = self.config["optional"]

        fc = freq_in_Hz/1e9 #get freq_in_Hz in GHz

        #LOD probability, Table 7.4.2-1 LOS probability
        if d2D <= 18:
            Pr_LOS = 1
        else:
            Pr_LOS = 18/d2D + np.exp(-d2D/36)*(1 - 18/d2D)

        d3D = np.sqrt(d2D**2 + (hBS-hUT)**2)
        dBP = self.cal_dBP(freq_in_Hz)

        SF_std = 4
        if d2D <= dBP:
            #PL1
            PL_UMi_LOS = 32.4 + 21*np.log10(d3D) + 20*np.log10(fc)
        else:
            #PL2
            PL_UMi_LOS = 32.4 + 40*np.log10(d3D) + 20*np.log10(fc) \
                        - 9.5*np.log10(dBP**2 + (hBS-hUT)**2)
                    
        if LOS == False:
            #NLOS
            if optional == False:
                PL_UMi_NLOS = 35.3*np.log10(d3D) + 22.4 + 21.3*np.log10(fc) - 0.3*(hUT-1.5)
                PL_UMi_NLOS = max(PL_UMi_LOS, PL_UMi_NLOS)
                SF_std = 7.82
            else:
                PL_UMi_NLOS = 32.4 + 20*np.log10(fc) + 31.9*np.log10(d3D)
                SF_std = 8.2
            return [PL_UMi_NLOS, SF_std, Pr_LOS]
        else:
            #LOS
            return [PL_UMi_LOS, SF_std, Pr_LOS]

if __name__ == "__main__":
    nrPathlossUMi = NrPathlossUMi()

    print(nrPathlossUMi.get_config())
    default_hUT = nrPathlossUMi.config["hUT"]
    default_d2D = nrPathlossUMi.config["d2D"]

    print(nrPathlossUMi.get_hE_distribution())
    nrPathlossUMi.config["hUT"] = 20
    nrPathlossUMi.config["d2D"] = 18
    print(nrPathlossUMi.get_hE_distribution())
    nrPathlossUMi.config["d2D"] = 3000
    print(nrPathlossUMi.get_hE_distribution())

    nrPathlossUMi.config["hUT"] = default_hUT
    nrPathlossUMi.config["d2D"] = default_d2D

    freq_in_Hz = 2e9
    LOS = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossUMi.cal(freq_in_Hz, LOS)

    LOS = False
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossUMi.cal(freq_in_Hz, LOS)

    nrPathlossUMi.config["d2D"] = 3000
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossUMi.cal(freq_in_Hz, LOS)

    nrPathlossUMi.config["optional"] = True
    [PL_no_shadow, SF_std, Pr_LOS] = nrPathlossUMi.cal(freq_in_Hz, LOS)

    pass