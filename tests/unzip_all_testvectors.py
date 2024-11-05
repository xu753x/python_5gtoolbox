# -*- coding:utf-8 -*-

from zipfile import ZipFile 
import os

from tests import testvectors_path

testvectors_path = testvectors_path.read_testvectors_path()


print("start unzip testvectos")

for path in testvectors_path:
    zipfile_lists = []
    for f in os.listdir(path):
        if f.endswith(".zip"):
            zipfile_lists.append(path + '/' + f)

    for zipfile in zipfile_lists:
        zObject = ZipFile(zipfile, 'r')
        zObject.extractall(path)

print("finished unzip testvectos")