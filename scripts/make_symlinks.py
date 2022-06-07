import glob
import os
import sys
import numpy as np
args = sys.argv

asdmList = glob.glob('./data/uid___*')
asdm12m = np.load(args[1])

for f in asdmList:
    imgs = glob.glob(f+'/specplot/*.png')
    asdm = f.replace('./data/','')

    telescope = None
    if asdm in asdm12m:
        telescope = 'A12m'
    else:
        telescope = 'A7m'

    if len(imgs) >= 1:
        for img in imgs:
            field = 'J'+img.split('.J')[1].split('.spw_')[0]
            os.system('mkdir -p figs')
            os.system('mkdir -p figs/'+telescope)
            os.system('mkdir -p figs/'+telescope+'/'+field)
            os.system('ln -sf '+os.path.abspath(img)+' '+'mkdir -p figs/'+telescope+'/'+field+'/')
