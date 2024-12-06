import zipfile
import os

""" the file is to zip testvectos before git push to remote
there are around 100K small testvector files, it is better to zip them before git push to remote,
github has file limit of 100MB, this module is to zip testvector in the folder to multiple zip files to avoid file size limitation
"""

def zip_files(path, name_pre, splitsize):
    
    path_lists = []
    name_lists = []
    for f in os.listdir(path):
        if f.endswith(".mat"):
            path_lists.append(path + '/' + f)
            name_lists.append(f)
    
    compression = zipfile.ZIP_DEFLATED

    zip_idx = 0
    zip_count = 0
    zipfilename = "zip_{0}_{1}.zip".format(name_pre, zip_idx)
    zf = zipfile.ZipFile(path+'/'+zipfilename, mode="w")
    for m in range(len(name_lists)):
        zf.write(path_lists[m], name_lists[m], compress_type=compression)
        zip_count += 1
        if zip_count >= splitsize:
            #done one zip file
            zf.close()
            zip_count = 0
            zip_idx += 1
            zipfilename = "zip_{0}_{1}.zip".format(name_pre, zip_idx)
            zf = zipfile.ZipFile(path+'/'+zipfilename, mode="w")

    zf.close()
    
if __name__ == "__main__":
    #path = "tests/nr_pusch/testvectors_ulsch_without_uci"
    #zip_files(path, "testvectors_ulsch_without_uci", 200)

    #path = "tests/nr_pusch/testvectors_ulsch_with_uci"
    #zip_files(path, "testvectors_ulsch_with_uci", 200)

    #path = "tests/nr_pusch/testvectors_pusch"
    #zip_files(path, "testvectors_pusch", 50)

    #path = "tests/nr_pucch/testvectors_format0"
    #zip_files(path, "testvectors_pucch_format0", 2000)

    #path = "tests/nr_pucch/testvectors_format1"
    #zip_files(path, "testvectors_pucch_format1", 2000)

    #path = "tests/nr_pucch/testvectors_format2"
    #zip_files(path, "testvectors_pucch_format2", 2000)

    #path = "tests/nr_pucch/testvectors_format3"
    #zip_files(path, "testvectors_pucch_format3", 100)

    #path = "tests/nr_pucch/testvectors_format4"
    #zip_files(path, "testvectors_format4", 2000)

    #path = "tests/nr_srs/testvectors"
    #zip_files(path, "testvectors_srs", 200)

    #path = "tests/nr_prach/testvectors_prach_seq"
    #zip_files(path, "testvectors_prach_seq", 2000)

    #path = "tests/nr_prach/testvectors_prach"
    #zip_files(path, "testvectors_prach", 100)

    #path = "tests/nr_csirs/testvectors"
    #zip_files(path, "testvectors_csirs", 2000)

    #path = "tests/common/testvectors_lowPAPR"
    #zip_files(path, "testvectors_lowPAPR", 800)

    #path = "tests/common/testvectors_modulation"
    #zip_files(path, "testvectors_modulation", 3000)
    
    #path = "tests/ldpc/testvectors"
    #zip_files(path, "testvectors_ldpc", 3000)

    #path = "tests/polar/testvectors"
    #zip_files(path, "testvectors_polar", 3000)

    #path = "tests/smallblock/testvectors"
    #zip_files(path, "testvectors_smallblock", 3000)

    #path = "tests/nr_pdsch/testvectors_dlsch"
    #zip_files(path, "testvectors_dlsch", 500)

    #path = "tests/nr_pdsch/testvectors"
    #zip_files(path, "testvectors_pdsch", 10)

    #path = "tests/nr_pdsch/testvectors_short_pdsch"
    #zip_files(path, "testvectors_nrPDSCH_mixed_testvec", 100)
    
    #path = "tests/nr_lowphy/testvectors"
    #zip_files(path, "testvectors_nr_lowphy", 6)

    #path = "tests/nr_pdcch/testvectors"
    #zip_files(path, "testvectors_nr_pdcch", 200)

    #path = "tests/nr_ssb/testvectors"
    #zip_files(path, "testvectors_nr_ssb", 5)

    #path = "tests/nr_ssb/testvectors_highphy"
    #zip_files(path, "testvectors_ssb_highphy", 10)

    #path = "tests/nr_waveform/testvectors"
    #zip_files(path, "testvectors_nrPDSCH_mixed_testvec", 1)
    
    #path = "tests/nr_testmodel/testvectors"
    #zip_files(path, "nr_testmodel_testvec", 20)

    path = "tests/demodulation/testvectors"
    zip_files(path, "nr_demodulation_testvec", 20)

    aaaa=1


