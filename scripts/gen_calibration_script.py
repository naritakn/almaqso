import sys
import os
import glob

asdmname = glob.glob('*.asdm.sdm')[0]

sys.path.append(os.environ.get('CASA_AU_PATH'))

import analysisUtils as aU
import almaqa2csg as csg

visname = asdmname.replace('.asdm.sdm','.ms')

kw_importasdm = {
    'asdm':asdmname,
    'vis':visname,
    'asis':'Antenna Station Receiver Source CalAtmosphere CalWVR CorrelatorMode SBSummary',
    'bdfflags':True,
    'lazy':True,
    'flagbackup':False,
    #'process_caldevice':False,
    }

importasdm(**kw_importasdm)

refant = aU.commonAntennas(visname)
kw_generateReducScript = {
    'msNames':visname,
    'refant':refant[0],
    'corrAntPos':False,
    }

csg.generateReducScript(**kw_generateReducScript)
