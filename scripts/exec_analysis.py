import numpy as np
import importlib
import glob
import os

import sys
sys.path.append('.')
import Lib_casa_analysis as Lib
importlib.reload(Lib)

casacmdforuvfit = os.environ.get('CASA_FOR_UVFIT')
args = sys.argv

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
obj.init_spacesave()
print('step:5')
obj.uvfit_run(allrun=True,plot=True)
print('step:6')
for field in obj.fields:
    obj.cont_imaging(field,statwtflag=False)

print('step:7')
obj.spacesaving(gzip=True,dryrun=False)
