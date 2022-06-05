import importlib
import sys
import os
import numpy as np
import json

sys.path.append('.')
import Lib_python_analysis as Lib
importlib.reload(Lib)
args = sys.argv

band = str(args[1])
os.system('mkdir -p urls')
dryrun = False

jfilename = args[2]
f = open(jfilename,'r')
jdict = json.load(f)
f.close()

for i in range(len(jdict)):
    sname = jdict[i]['names'][0]['name']

    if os.path.exists('./urls/'+sname+'.B'+band+'.npy'):
        print(sname+' -> skipped')

    else:
        if dryrun:
            pass
            print(sname+' -> dydrun')
        else:
            try:
                print(sname+' -> start!')
                obj = Lib.QSOquery(sname,band=band,almaurl='https://almascience.eso.org',download_d='./',replaceNAOJ=True,only12m=True,onlyFDM=True)
                obj.get_data_urls(almaquery=False)
                np.save('./urls/'+sname+'.B'+band+'.npy',obj.url_list)
                print('Totla size('+sname+' B'+band+'): '+str(obj.total_size)+' GB')
            except:
                print('ERROR: '+sname+' -> failed and skipped')
