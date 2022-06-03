import numpy as np
import importlib
import glob
import os

import sys
sys.path.append('.')
import Lib_casa_analysis as Lib
importlib.reload(Lib)

casacmdforuvfit = sys.path.append(os.environ.get('CASA_FOR_UVFIT'))
args = sys.argv

tarfilename = args[1]
if args[1] == None:
    tarfilename = '2018.1.00850.S_uid___A002_Xd845af_X3ce8.asdm.sdm.tar'

obj = Lib.QSOanalysis(tarfilename,casacmdforuvfit=casacmdforuvfit,spacesave=True)

print('step:0')
obj.intial_proc()
print('step:1')
obj.importasdm()
print('step:2')
obj.gen_calib_script()
print('step:3')
obj.remove_target()
print('step:4')
obj.doCalib()
print('step:5')
obj.uvfit_run(allrun=True,plot=True)
print('step:6')
for field in obj.fields:
    obj.cont_imaging(field)

print('step:7')
obj.spacesaving(gzip=True,dryrun=False)
