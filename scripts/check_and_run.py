import os
import glob
import numpy as np
import sys
import datetime

args = sys.argv

tarlist = glob.glob('*.tar')
urllist = np.load(args[1])

try:
    rmflag = str(args[2])
except:
    rmflag = 'save'

exec_tarlist = []

for f in tarlist:
    dd = urllist[urllist[:,0]=='https://almascience.eso.org/dataPortal/'+f][:,1].astype('int') - os.path.getsize(f)
    if dd > 0:
        print(f+' '+str(dd/1024/1024/1024))
        if rmflag == 'rm':
            os.system('rm -rf '+f)
    else:
        exec_tarlist.append(f)

dt_now = datetime.datetime.now()
ver = dt_now.isoformat().replace(':','-')
np.save('exec_tarlist.v'+ver+'.npy',np.array(exec_tarlist))
