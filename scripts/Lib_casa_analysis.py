# CASA script
# tested on CASA 6.2.1.7

# modules
import os
import sys
import numpy as np
import glob

sys.path.append(os.environ.get('CASA_AU_PATH'))
import analysisUtils as aU
import almaqa2csg as csg

class QSOanalysis():

    def __init__(self,tarfilename,casacmd='casa',casacmdforuvfit='casa',spacesave=False,workingDir=None):
        self.tarfilename = tarfilename
        self.workingDir = workingDir
        self.spacesave = spacesave
        self.casacmd = casacmd
        self.casacmdforuvfit = casacmdforuvfit

        self.projID = tarfilename.split('_uid___')[0]
        self.asdmname = 'uid___' + (tarfilename.split('_uid___')[1]).replace('.asdm.sdm.tar','')

    def writelog(self,content=''):
        os.system('mkdir -p log')
        os.system('touch ./log/'+self.asdmname+'.analysis.log')
        os.system('echo "'+content+'" >> '+'./log/'+self.asdmname+'.analysis.log')

    # step0: untar & make working dir
    def intial_proc(self):

        if self.workingDir!=None:
            os.chdir(self.workingDir)

        if os.path.exists(self.tarfilename):
            os.system('mkdir -p '+self.asdmname)
            os.system('mv '+self.tarfilename+' '+self.asdmname+'/')
            os.chdir(self.asdmname)
            os.system('tar -xvf '+self.tarfilename)

        elif os.path.exists(self.tarfilename+'.gz'):
            os.system('mkdir -p '+self.asdmname)
            os.system('mv '+self.tarfilename+'.gz '+self.asdmname+'/')
            os.chdir(self.asdmname)
            os.system('gzip -d '+self.tarfilename+'.gz')
            os.system('tar -xvf '+self.tarfilename)

        elif os.path.exists(self.asdmname):
            os.chdir(self.asdmname)

            if os.path.exists(self.tarfilename):
                os.system('tar -xvf '+self.tarfilename)

            elif os.path.exists(self.tarfilename+'.gz'):
                os.system('gzip -d '+self.tarfilename+'.gz')
                os.system('tar -xvf '+self.tarfilename)

        else:
            print('Error: You may need to download data.')
            sys.exit()

        self.writelog('step0:OK')

    # step1: importasdm
    def importasdm(self,dryrun=False):

        asdmfile = glob.glob('./' + self.projID + '/*/*/*/raw/*')[0]
        os.system('ln -sf '+asdmfile+' .')
        visname = (os.path.basename(asdmfile)).replace('.asdm.sdm','.ms')

        kw_importasdm = {
            'asdm':os.path.basename(asdmfile),
            'vis':visname,
            'asis':'Antenna Station Receiver Source CalAtmosphere CalWVR CorrelatorMode SBSummary',
            'bdfflags':True,
            'lazy':True,
            'flagbackup':False,
            }

        if not dryrun:

            from casatasks import importasdm
            importasdm(**kw_importasdm)

        try:
            self.spws = aU.getScienceSpws(vis=visname).split(",")
            os.system('mkdir -p tempfiles')
            np.save('tempfiles/spws.npy',np.array(self.spws))

        except:
            self.spws = np.load('tempfiles/spws.npy')

        self.asdmfile = asdmfile
        self.visname = visname

        self.writelog('step1:OK')

    # step2: generate calib script
    def gen_calib_script(self,dryrun=False):
        refant = aU.commonAntennas(self.visname)
        kw_generateReducScript = {
            'msNames':self.visname,
            'refant':refant[0],
            'corrAntPos':False,
            }

        if not dryrun:
            csg.generateReducScript(**kw_generateReducScript)

        self.refant = refant
        self.dish_diameter = aU.almaAntennaDiameter(refant[0])

        self.writelog('step2:OK')

    # step3: remove TARGET observations
    def remove_target(self,dryrun=False):

        listOfIntents_init = [
            'CALIBRATE_BANDPASS#ON_SOURCE',
            'CALIBRATE_FLUX#ON_SOURCE',
            'CALIBRATE_PHASE#ON_SOURCE',
            'CALIBRATE_WVR#AMBIENT',
            'CALIBRATE_WVR#HOT',
            'CALIBRATE_WVR#OFF_SOURCE',
            'CALIBRATE_WVR#ON_SOURCE',
            'CALIBRATE_ATMOSPHERE#OFF_SOURCE',
            'CALIBRATE_ATMOSPHERE#AMBIENT',
            'CALIBRATE_ATMOSPHERE#HOT',
            'CALIBRATE_POINTING#ON_SOURCE'
            ]

        if not dryrun:
            os.system('mv '+self.visname+' '+self.visname+'.org')
            kw_mstransform = {
                'vis':self.visname+'.org',
                'outputvis':self.visname,
                'datacolumn':'all',
                'intent':','.join(listOfIntents_init),
                'keepflags':True
                }

            from casatasks import mstransform
            mstransform(**kw_mstransform)

        self.writelog('step3:OK')

    # step4: do Calibration
    def doCalib(self,dryrun=False):

        if not dryrun:
            cmdfile = self.visname + '.scriptForCalibration.py'

            f = open(cmdfile.replace('.py','.part.py'),'w')
            f.write('mysteps = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]'+'\n')
            f.write('applyonly = True'+'\n')
            f.write('execfile('+'"'+cmdfile+'"'+',globals())'+'\n')
            f.close()

            cmd = '"' + 'execfile('+"'"+cmdfile.replace('.py','.part.py')+"'"+')' +'"'
            os.system(self.casacmd+' --nologger --nogui -c '+cmd)

        self.fields = np.unique(aU.getCalibrators(vis=self.visname+'.split'))

        self.beamsize = aU.estimateSynthesizedBeam(self.visname+'.split')
        from casatools import synthesisutils
        su = synthesisutils()
        self.imsize = su.getOptimumSize(int(100./self.beamsize*5))
        #self.imsize = optImsize(int(100./self.beamsize*5))
        self.cell = '{:.3f}'.format(self.beamsize/5) + 'arcsec'

        self.writelog('step4:OK')


    # step5-1: split calibrator observations
    def uvfit_splitQSO(self,spw,field,dryrun=False):

        self.spw = spw
        self.field = field

        kw_mstransform = {
            'vis':self.visname+'.split',
            'outputvis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw,
            'datacolumn':'corrected',
            'spw':spw,
            'field':field,
            'intent':'*ON_SOURCE*',
            'keepflags':True,
            'reindex':True,
            }

        if not dryrun:
            os.system('mkdir -p calibrated')
            os.system('rm -rf '+kw_mstransform['outputvis'])
            os.system('rm -rf '+kw_mstransform['outputvis']+'.listobs')

            from casatasks import mstransform,listobs
            mstransform(**kw_mstransform)
            listobs(vis=kw_mstransform['outputvis'],listfile=kw_mstransform['outputvis']+'.listobs')

    def uvfit_splitQSO_allspw(self,field,dryrun=False):

        self.spw = 'all'
        self.field = field

        kw_split = {
            'vis':self.visname+'.split',
            'outputvis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw+'.tmp',
            'datacolumn':'corrected',
            'spw':','.join(self.spws),
            #'combinespws':False,
            'width':10000,
            'field':field,
            'intent':'*ON_SOURCE*',
            'keepflags':True,
            #'reindex':True,
            }

        kw_mstransform = {
            'vis':kw_split['outputvis'],
            'outputvis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw,
            'datacolumn':'all',
            #'spw':','.join(self.spws),
            'combinespws':True,
            'regridms':True,
            'start':0,
            'nchan':1,
            'width':len(self.spws),
            'field':field,
            #'intent':'*ON_SOURCE*',
            'keepflags':True,
            'reindex':True,
            }

        if not dryrun:
            os.system('mkdir -p calibrated')
            os.system('rm -rf '+kw_split['outputvis'])
            os.system('rm -rf '+kw_split['outputvis']+'.listobs')
            os.system('rm -rf '+kw_mstransform['outputvis'])
            os.system('rm -rf '+kw_mstransform['outputvis']+'.listobs')

            from casatasks import split,listobs,mstransform
            split(**kw_split)
            listobs(vis=kw_split['outputvis'],listfile=kw_split['outputvis']+'.listobs')
            mstransform(**kw_mstransform)
            os.system('rm -rf '+kw_split['outputvis'])
            listobs(vis=kw_mstransform['outputvis'],listfile=kw_mstransform['outputvis']+'.listobs')


    # step5-2: create model column
    def uvfit_createcol(self,modelcol=True,dryrun=False):

        if not dryrun:
            kw_clearcal = {
                'vis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw,
                'addmodel':modelcol,
                }

            from casatasks import clearcal
            clearcal(**kw_clearcal)

    #step5-3: do uvmultifit
    def uvfit_uvmultifit(self,intent=None,write="",column='data',mfsfit=True,dryrun=False):

        if not dryrun:
            os.system('mkdir -p tempfiles')
            os.system('mkdir -p specdata')

            if intent == None:
                outfile = self.visname+'.split.'+self.field+'.spw_'+self.spw+'.dat'
            else:
                outfile = self.visname+'.split.'+self.field+'.spw_'+self.spw+'.'+intent+'.dat'

            f = open('./tempfiles/'+outfile.replace('.dat','.kw_uvfit.py'),'w')
            f.write('from NordicARC import uvmultifit as uvm'+'\n')
            f.write('\n')
            f.write('kw_uvfit = {'+'\n')
            f.write('   "vis":"'+'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw+'",'+'\n')
            f.write('   "spw":"0",'+'\n')
            f.write('   "column":"'+column+'",'+'\n')
            f.write('   "field":"0",'+'\n')
            f.write('   "stokes":"I",'+'\n')
            f.write('   "pbeam":True,'+'\n')
            f.write('   "dish_diameter":12.0,'+'\n')
            f.write('   "chanwidth":1,'+'\n')
            f.write('   "var":["0,0,p[0]"],'+'\n')
            f.write('   "p_ini":[1.0],'+'\n')
            f.write('   "model":["delta"],'+'\n')
            f.write('   "OneFitPerChannel":'+str(mfsfit)+','+'\n')
            f.write('   "write":"'+write+'",'+'\n')
            f.write('   "outfile":"./specdata/'+outfile+'",'+'\n')
            f.write('   }'+'\n')
            f.write('myfit = uvm.uvmultifit(**kw_uvfit)'+'\n')
            f.close()

            "'" + 'execfile("./tempfiles/'+outfile.replace('.dat','.kw_uvfit.py')+'")' + "'"
            cmd = self.casacmdforuvfit+' --nologger --nogui --nologfile -c '+ "'" + 'execfile("./tempfiles/'+outfile.replace('.dat','.kw_uvfit.py')+'")' + "'"
            os.system(cmd)


    # step5-4: gaincal
    def uvfit_gaincal(self,intent='phase',solint='int',solnorm=False,gaintype='G',calmode='p',gaintable='',dryrun=False):

        kw_gaincal = {
            'vis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw,
            'caltable':'./caltables/'+self.visname+'.split.'+self.field+'.spw_'+self.spw+'.'+intent,
            'field':'0',
            'solint':solint,
            'refant':self.refant[0],
            'gaintype':gaintype,
            'calmode':calmode,
            'minsnr':2.0,
            'gaintable':gaintable,
            'solnorm':solnorm,
            }

        if not dryrun:
            os.system('mkdir -p caltables')
            os.system('rm -rf '+kw_gaincal['caltable'])

            from casatasks import gaincal
            gaincal(**kw_gaincal)

        return kw_gaincal['caltable']

    # step5-5: applycal
    def uvfit_applycal(self,gaintable='',dryrun=False):

        if not dryrun:
            kw_applycal = {
                'vis':'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw,
                'interp':'linear',
                'flagbackup':False,
                'applymode':'calflag',
                'gaintable':gaintable,
                'calwt':False,
                }

            from casatasks import applycal
            applycal(**kw_applycal)

    # step5-6: gainplot
    def uvfit_gainplot(self,type='amp_phase',dryrun=False):

        if not dryrun:
            from casatools import table
            tb = table()
            import matplotlib.pyplot as plt

            for field in self.fields:
                for spw in self.spws:
                    caltablebase = self.asdmname+'.ms.split.'+field+'.spw_'+spw
                    caltable0 = './caltables/' + caltablebase + '.'+type+'_0'
                    caltable1 = './caltables/' + caltablebase + '.'+type+'_1'

                    tb.open(caltable0)
                    Time0  = tb.getcol('TIME').copy()
                    cgain0 = tb.getcol('CPARAM').copy()
                    ant0   = tb.getcol('ANTENNA1') .copy()
                    tb.close()

                    tb.open(caltable1)
                    Time1  = tb.getcol('TIME').copy()
                    cgain1 = tb.getcol('CPARAM').copy()
                    ant1   = tb.getcol('ANTENNA1') .copy()
                    tb.close()

                    if type == 'phase':
                        phase0_0 = np.angle(cgain0[0][0],deg=True)
                        phase0_1 = np.angle(cgain0[1][0],deg=True)
                        phase1   = np.angle(cgain1[0][0],deg=True)
                    elif type == 'amp_phase':
                        phase0_0 = np.abs(cgain0[0][0])
                        phase1   = np.abs(cgain1[0][0])


                    plt.close()
                    titlename = self.asdmname+' '+field+' spw:'+spw
                    plt.title(titlename)
                    plt.scatter((Time0-Time0[0])/60.,phase0_0,c='b',s=2)
                    if type == 'phase':
                        plt.scatter((Time0-Time0[0])/60.,phase0_1,c='b',s=2)
                    plt.scatter((Time1-Time1[0])/60.,phase1,c='r',s=1)
                    plt.xlabel('Time from the first integration [min]')
                    if type == 'phase':
                        plt.ylabel('Gain phase [deg]')
                    elif type == 'amp_phase':
                        plt.ylabel('Gain amplitude')
                    plt.savefig('./caltables/'+caltablebase+'.gainplot.'+type+'.png')
                    plt.savefig('./caltables/'+caltablebase+'.gainplot.'+type+'.pdf')
                    plt.close()

    # step5: uvmultifit & selfcal
    def uvfit_run(self,allrun=False,spw=None,field=None,dryrun=False,plot=True):

        if allrun:
            for _field in self.fields:
                for _spw in self.spws:

                    self.uvfit_splitQSO(spw=_spw,field=_field,dryrun=dryrun)
                    self.uvfit_createcol(dryrun=dryrun)
                    self.uvfit_uvmultifit(write='model',column='data',intent='noselfcal',dryrun=dryrun)
                    gaintable_p  = self.uvfit_gaincal(intent='phase_0',solint='int',gaintype='G',calmode='p',gaintable='',dryrun=dryrun)
                    gaintable_ap = self.uvfit_gaincal(intent='amp_phase_0',solint='int',solnorm=True,gaintype='T',calmode='ap',gaintable=[gaintable_p],dryrun=dryrun)
                    self.uvfit_applycal(gaintable=[gaintable_p,gaintable_ap],dryrun=dryrun)
                    self.uvfit_uvmultifit(write='model',column='corrected',dryrun=dryrun)
                    gaintable_p1  = self.uvfit_gaincal(intent='phase_1',solint='int',gaintype='T',calmode='p',gaintable=[gaintable_p,gaintable_ap],dryrun=dryrun)
                    gaintable_ap1 = self.uvfit_gaincal(intent='amp_phase_1',solint='int',solnorm=True,gaintype='T',calmode='ap',gaintable=[gaintable_p,gaintable_ap,gaintable_p1],dryrun=dryrun)
                    #self.uvfit_applycal(gaintable=[gaintable_p,gaintable_p1],dryrun=dryrun)
                    self.uvfit_uvmultifit(write='residuals',column='corrected',dryrun=dryrun)

            self.uvfit_gainplot(dryrun=(not plot),type='phase')
            self.uvfit_gainplot(dryrun=(not plot),type='amp_phase')

        else:
            if spw==None:
                print('Error: You need to specify spw.')

            elif field==None:
                print('Error: You need to specify field.')

            else:

                self.uvfit_splitQSO_allspw(field=field,dryrun=dryrun)
                self.uvfit_createcol(dryrun=dryrun)
                self.uvfit_uvmultifit(write='residuals',column='data',dryrun=dryrun,mfsfit=True)
                self.uvfit_gainplot(dryrun=(not plot))
                '''
                self.uvfit_splitQSO(spw=spw,field=field,dryrun=dryrun)
                self.uvfit_createcol(dryrun=dryrun)
                self.uvfit_uvmultifit(write='model',column='data',dryrun=dryrun)
                gaintable_p  = self.uvfit_gaincal(intent='phase_0',solint='int',gaintype='G',calmode='p',gaintable='',dryrun=dryrun)
                gaintable_ap = self.uvfit_gaincal(intent='amp_phase_0',solint='int',gaintype='T',solnorm=True,calmode='ap',gaintable=[gaintable_p],dryrun=dryrun)
                self.uvfit_applycal(gaintable=[gaintable_p,gaintable_ap],dryrun=dryrun)
                self.uvfit_uvmultifit(write='model',column='corrected',dryrun=dryrun)
                gaintable_p1  = self.uvfit_gaincal(intent='phase_1',solint='int',gaintype='T',calmode='p',gaintable=[gaintable_p,gaintable_ap],dryrun=dryrun)
                gaintable_ap1 = self.uvfit_gaincal(intent='amp_phase_1',solint='int',gaintype='T',solnorm=True,calmode='ap',gaintable=[gaintable_p,gaintable_ap,gaintable_p1],dryrun=dryrun)
                self.uvfit_applycal(gaintable=[gaintable_p,gaintable_ap,gaintable_p1,gaintable_ap1],dryrun=dryrun)
                self.uvfit_uvmultifit(write='residuals',column='corrected',dryrun=dryrun)
                '''

        self.writelog('step5:OK')

    # step6: continuum imaging
    def cont_imaging(self,field,dryrun=False):

        vis = list( set(glob.glob('./calibrated/*.'+field+'.*')) ^ set(glob.glob('./calibrated/*.'+field+'.*.listobs')))
        #vis = list( set(glob.glob('./calibrated/*'+field+'*all*')) ^ set(glob.glob('./calibrated/*'+field+'*all*listobs')))


        kw_tclean = {
            'vis':vis,
            'imagename':'./imsg/'+self.asdmname+'.'+field+'.residual.allspw.selfcal.mfs.briggs.robust_0.5.dirty',
            'datacolumn':'corrected',
            'imsize':self.imsize,
            'cell':self.cell,
            'weighting':'briggs',
            'robust':0.5,
            'deconvolver':'hogbom',
            'gridder':'standard',
            'specmode':'mfs',
            'threshold':'10mJy',
            'niter':0,
            'nterms':2,
            'interactive':False,
            'pbcor':True,
            'restoringbeam':'common',
            }

        if not dryrun:
            os.system('mkdir -p imsg')
            os.system('rm -rf '+kw_tclean['imagename']+'*')
            from casatasks import tclean, exportfits
            tclean(**kw_tclean)
            exportfits(kw_tclean['imagename']+'.image',kw_tclean['imagename']+'.image.fits')
            exportfits(kw_tclean['imagename']+'.image.pbcor',kw_tclean['imagename']+'.image.pbcor.fits')

            for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
                os.system('rm -rf '+kw_tclean['imagename']+ext)

        self.writelog('step6:OK')

    # step7: spacesaving
    def spacesaving(self,gzip=False,dryrun=False):

        if not dryrun:
            if self.spacesave:
                os.system('rm -rf *.last')
                os.system('rm -rf byspw')
                try:
                    os.system('mkfir -p log')
                    os.system('mv ./calibrated/*.listobs ./log/')
                except:
                    print('ERROR: copy listobs failed')

                os.system('rm -rf calibrated')
                os.system('rm -rf '+self.asdmname+'*')
                os.system('rm -rf '+self.projID)

                if gzip:
                    os.system('gzip -1 -v '+glob.glob('*.tar')[0])

        self.writelog('step7:OK')




###
