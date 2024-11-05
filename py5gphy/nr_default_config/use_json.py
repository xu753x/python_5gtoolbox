# -*- coding:utf-8 -*-

import json
import os

curpath = "py5gphy/nr_default_config/"
filename = "default_DL_waveform_config.json"
def usejson():
    with open(curpath + filename, 'r') as f:
        data = json.load(f)
    print(data)
    return data

if __name__ == "__main__":
    jsondata = usejson()
    pass