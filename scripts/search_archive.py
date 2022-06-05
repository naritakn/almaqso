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

cals = []
for i in range(len(jdict)):
     cals.append(jdict[i]['names'][0]['name'])

cals = np.unique(cals)
print(cals.shape)

for i in range(cals.shape[0]):
    #sname = jdict[i]['names'][0]['name']
    sname = cals[i]

    if os.path.exists('./urls/'+sname+'.B'+band+'.npy'):
        print('['+str(i+1)+'/'+str(cals.shape[0])+'] '+sname+' -> skipped')

    else:
        if dryrun:
            pass
            print('['+str(i+1)+'/'+str(cals.shape[0])+'] '+sname+' -> dydrun')
        else:
            try:
                print('['+str(i+1)+'/'+str(cals.shape[0])+'] '+sname+' -> start!')
                obj = Lib.QSOquery(sname,band=band,almaurl='https://almascience.eso.org',download_d='./',replaceNAOJ=True,only12m=True,onlyFDM=True)
                obj.get_data_urls(almaquery=False)
                np.save('./urls/'+sname+'.B'+band+'.npy',obj.url_list)
                print('Totla size('+sname+' B'+band+'): '+str(obj.total_size)+' GB')
            except:
                print('ERROR: '+sname+' -> failed (maybe no matched data) and skipped')
