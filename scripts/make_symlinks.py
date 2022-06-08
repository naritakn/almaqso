import glob
import os
import sys
import numpy as np
args = sys.argv

asdmList = glob.glob('./data/uid___*')
asdm12m = np.load(args[1])

for f in asdmList:
    imgs = glob.glob(f+'/specplot/*.png')
    fitsimgs = glob.glob(f+'/imsg/*.image.fits')
    asdm = f.replace('./data/','')

    telescope = None
    #print(asdm)
    if asdm in asdm12m:
        telescope = 'A12m'
    else:
        telescope = 'A7m'

    if len(imgs) >= 1:
        for img in imgs:
            try:
                field = 'J'+img.split('.J')[1].split('.spw')[0]
                os.system('mkdir -p figs')
                os.system('mkdir -p figs/'+telescope)
                os.system('mkdir -p figs/'+telescope+'/'+field)
                os.system('ln -sf '+os.path.abspath(img)+' '+'figs/'+telescope+'/'+field+'/')
            except:
                pass
    if len(fitsimgs) >= 1:
        for fitsimg in fitsimgs:
            try:
                field = 'J'+fitsimg.split('.J')[1].split('.residual.allspw.')[0]
                os.system('mkdir -p fits')
                os.system('mkdir -p fits/'+telescope)
                os.system('mkdir -p fits/'+telescope+'/'+field)
                os.system('ln -sf '+os.path.abspath(fitsimg)+' '+'fits/'+telescope+'/'+field+'/')
            except:
                pass
