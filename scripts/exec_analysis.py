import numpy as np
import importlib
import glob
import os

import sys
sys.path.append('.')
import Lib_casa_analysis as Lib
importlib.reload(Lib)

casacmdforuvfit = os.environ.get('CASA_FOR_UVFIT')

obj = Lib.QSOanalysis(tarfilename,casacmdforuvfit=casacmdforuvfit,spacesave=True)

asdmname = 'uid___' + (tarfilename.split('_uid___')[1]).replace('.asdm.sdm.tar','')

if os.path.exists(asdmname) and skipflag == 'skip':
    print(asdmname+': analysis already done and skip')

else:
    if os.path.exists(asdmname):
        print(asdmname+': analysis already done but reanalyzed')
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
    obj.uvfit_run(plot=True)
    print('step:6')
    obj.cont_imaging()
    print('step:7')
    obj.spacesaving(gzip=True)

    print('step:8')
    obj.specplot()
