import numpy as np
import glob
import os
from .QSOanalysis import QSOanalysis


def analysis(tarfilename: str, skipflag='skip', casacmd='casa'):
    obj = QSOanalysis(tarfilename, spacesave=True, casacmd=casacmd)
    
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
