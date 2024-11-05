# -*- coding:utf-8 -*-

from zipfile import ZipFile 
import os

from tests import testvectors_path

testvectors_path = testvectors_path.read_testvectors_path()


print("start remove all testvectos matfiles")

for path in testvectors_path:
    for f in os.listdir(path):
        if f.endswith(".mat"):
            file = os.path.join(path, f)
            os.remove(file)

    
print("finished unzip testvectos")