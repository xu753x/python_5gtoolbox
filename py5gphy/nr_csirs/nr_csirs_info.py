# -*- coding:utf-8 -*-
import numpy as np

def validate_config(csirs_config,carrier_prbsize):
    """ check if CSIRS config correct or not
    """
    #read input
    row = csirs_config["frequencyDomainAllocation"]["row"]
    bitstring = csirs_config["frequencyDomainAllocation"]["bitstring"]
    nrofPorts = csirs_config["nrofPorts"]
    firstOFDMSymbolInTimeDomain = csirs_config["firstOFDMSymbolInTimeDomain"]
    cdm_type = csirs_config["cdm_type"]
    density = csirs_config["density"]
    startingRB = csirs_config["startingRB"]
    nrofRBs = csirs_config["nrofRBs"]
    periodicity = csirs_config["periodicity"]
    slotoffset = csirs_config["slotoffset"]

    assert row in [1,2,3,4,5]
    if row ==1:
        assert nrofPorts == 1
        assert density == "three"
        assert cdm_type == "noCDM"
        assert (len(bitstring) >= 4) and ('1' in bitstring[-4:])
        
    elif row == 2:
        assert nrofPorts == 1
        assert density in ["dot5evenPRBs", "dot5oddPRBs", "one"]
        assert cdm_type == "noCDM"
        assert (len(bitstring) >= 12) and ('1' in bitstring[-12:])
    elif row == 3:
        assert nrofPorts == 2
        assert density in ["dot5evenPRBs", "dot5oddPRBs", "one"]
        assert cdm_type == "fd-CDM2"
        assert (len(bitstring) >= 6) and ('1' in bitstring[-6:])
    elif row == 4:
        assert nrofPorts == 4
        assert density == "one"
        assert cdm_type == "fd-CDM2"
        assert (len(bitstring) >= 3) and ('1' in bitstring[-3:])
    elif row == 5:
        assert nrofPorts == 4
        assert density == "one"
        assert cdm_type == "fd-CDM2"
        assert (len(bitstring) >= 6) and ('1' in bitstring[-6:])
    

    assert (firstOFDMSymbolInTimeDomain >= 0) and (firstOFDMSymbolInTimeDomain <= 13)
    assert startingRB < carrier_prbsize
    assert (nrofRBs >= 24) and (nrofRBs <= carrier_prbsize+1) and (nrofRBs % 4 == 0)
    assert periodicity in [4,5,8,10,16,20,32,40,64,80,160,320,640]
    assert slotoffset < periodicity

    return True
    



