import almaqa2csg as csg
import analysisUtils as aU
import os
import sys
import numpy as np
import glob
import subprocess


def _run_casa_cmd(casa, cmd):
    try:
        result = subprocess.run(
            [casa, '--nologger', '--nogui', '-c', f'"{cmd}"'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"STDOUT for {cmd}:", result.stdout)
        print(f"STDERR for {cmd}:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {cmd}:")
        print(f"Return Code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise


class QSOanalysis():
    def __init__(self, tarfilename, casacmd='casa', casacmdforuvfit='casa',
                 spacesave=False, workingDir=None):
        self.tarfilename = tarfilename
        self.workingDir = workingDir
        self.spacesave = spacesave
        self.casacmd = casacmd
        self.casacmdforuvfit = casacmdforuvfit

        self.projID = tarfilename.split('_uid___')[0]
        self.asdmname = 'uid___' + \
            (tarfilename.split('_uid___')[1]).replace('.asdm.sdm.tar', '')

        try:
            print(f'analysisUtils of {aU.version()} will be used.')
        except Exception:
            raise Exception('analysisUtils is not found')

    def writelog(self, content=''):
        os.system('mkdir -p log')
        os.system('touch ./log/'+self.asdmname+'.analysis.v2.log')
        os.system('echo "'+content+'" >> '+'./log/' +
                  self.asdmname+'.analysis.v2.log')

    # step0: untar & make working dir
    def intial_proc(self, forcerun=False, dryrun=False):
        if dryrun:
            os.chdir(self.asdmname)

        else:
            if self.workingDir is not None:
                os.chdir(self.workingDir)

            if os.path.exists(self.tarfilename):
                os.makedirs(self.asdmname)
                os.system('cp '+self.tarfilename+' '+self.asdmname+'/')
                os.chdir(self.asdmname)
                os.system('tar -xf '+self.tarfilename)

            elif os.path.exists(self.tarfilename+'.gz'):
                os.makedirs(self.asdmname)
                os.system('cp '+self.tarfilename+'.gz '+self.asdmname+'/')
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
                # print('Error: You may need to download data.')
                raise Exception('You may need to download data.')

        self.writelog('step0:OK')

    # step1: importasdm
    def importasdm(self, dryrun=False):
        asdmfile = glob.glob(
            f'{os.getcwd()}/{os.path.basename(self.projID)}/*/*/*/raw/*')[0]
        visname = (os.path.basename(asdmfile)).replace('.asdm.sdm', '.ms')
        # try:
        #     asdmfile = glob.glob('./' + self.projID + '/*/*/*/raw/*')[0]
        #     os.system('ln -sf '+asdmfile+' .')
        #     visname = (os.path.basename(asdmfile)).replace('.asdm.sdm','.ms')
        # except:
        #     asdmfile = 'uid___' + self.tarfilename.split('_uid___')[1].replace('.tar','')
        #     visname = asdmfile.replace('.asdm.sdm','.ms')

        kw_importasdm = {
            # 'asdm': os.path.basename(asdmfile),
            'asdm': asdmfile,
            'vis': visname,
            'asis': 'Antenna Station Receiver Source CalAtmosphere CalWVR CorrelatorMode SBSummary',
            'bdfflags': True,
            'lazy': True,
            'flagbackup': False,
        }

        if not dryrun:
            from casatasks import importasdm
            os.system('rm -rf '+kw_importasdm['vis'])
            importasdm(**kw_importasdm)

            try:
                self.spws = aU.getScienceSpws(vis=visname).split(",")
                os.system('mkdir -p tempfiles')
                np.save('tempfiles/spws.npy', np.array(self.spws))

            except Exception:
                self.spws = np.load('tempfiles/spws.npy')
        else:
            try:
                self.spws = np.load('tempfiles/spws.npy')
            except Exception:
                self.spws = aU.getScienceSpws(vis=visname).split(",")
                os.system('mkdir -p tempfiles')
                np.save('tempfiles/spws.npy', np.array(self.spws))

        self.asdmfile = asdmfile
        self.visname = visname

        self.writelog('step1:OK')

    # step2: generate calib script
    def gen_calib_script(self, dryrun=False):
        try:
            refant = aU.commonAntennas(self.visname)
            vis = self.visname
        except Exception:
            refant = aU.commonAntennas(self.visname + '.split')
            vis = self.visname + '.split'

        if not dryrun:
            if os.path.exists(
                    f'./log/{self.visname}.scriptForCalibration.py'
                ):
                print('Calibration script already exists.')
                os.system(f'cp ./log/{self.visname}.scriptForCalibration.py ./')
            else:
                print('Calibration script will be generated.')
                csg.generateReducScript(
                        msNames = vis,
                        refant = refant[0],
                        corrAntPos = False,
                        useCalibratorService = False,
                        useLocalAlmaHelper = False
                )
                os.makedirs('./log', exist_ok=True)
                os.system(f'cp {self.visname}.scriptForCalibration.py ./log/')

        self.refant = refant
        self.dish_diameter = aU.almaAntennaDiameter(refant[0])

        self.writelog('step2:OK')

    # step3: remove TARGET observations
    def remove_target(self, dryrun=False):
        if not dryrun:
            IntentListASDM = aU.getIntentsFromASDM(self.asdmfile)

            IntentList = []
            for intfield in list(IntentListASDM):
                IntentList = IntentList + IntentListASDM[intfield]

            listOfIntents_init = (np.unique(IntentList)[
                                  np.unique(IntentList) != 'OBSERVE_TARGET'])

            os.system('rm -rf '+self.visname+'.org')
            os.system('mv '+self.visname+' '+self.visname+'.org')
            kw_mstransform = {
                'vis': self.visname+'.org',
                'outputvis': self.visname,
                'datacolumn': 'all',
                'intent': '*,'.join(listOfIntents_init)+'*',
                'keepflags': True
            }

            from casatasks import mstransform
            os.system('rm -rf '+kw_mstransform['outputvis'])
            os.system('rm -rf '+kw_mstransform['outputvis']+'.flagversions')
            mstransform(**kw_mstransform)

        self.writelog('step3:OK')

    # step4: do Calibration
    def doCalib(self, dryrun=False):
        if not dryrun:
            cmdfile = self.visname + '.scriptForCalibration.py'

            checksteps = open(cmdfile, 'r')
            syscalcheck = checksteps.readlines().copy()[21]
            checksteps.close()

            f = open(cmdfile.replace('.py', '.part.py'), 'w')
            if syscalcheck.split(':')[1].split("'")[1] == \
                    'Application of the bandpass and gain cal tables':
                f.write(
                    'mysteps = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]'+'\n')
            else:
                f.write(
                    'mysteps = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]'+'\n')
            f.write('applyonly = True'+'\n')
            f.write('execfile('+'"'+cmdfile+'"'+',globals())'+'\n')
            f.close()

            cmd = '"' + \
                'execfile('+"'"+cmdfile.replace('.py',
                                                '.part.py')+"'"+')' + '"'
            os.system(self.casacmd+' --nologger --nogui -c '+cmd)

        vis = self.visname + '.split'
        # if vis not in glob.glob('./*'):
        #     vis = self.visname

        fields = np.unique(aU.getCalibrators(vis=vis))
        self.fields = []

        for field in fields:
            if field[0] == 'J':
                self.fields.append(field)

        self.beamsize = aU.estimateSynthesizedBeam(vis)
        from casatools import synthesisutils
        su = synthesisutils()

        if self.dish_diameter > 10.:
            # 12m
            self.imsize = su.getOptimumSize(int(120./self.beamsize*5))
        else:
            # 7m
            self.imsize = su.getOptimumSize(int(180./self.beamsize*5))

        self.cell = '{:.3f}'.format(self.beamsize/5) + 'arcsec'

        self.writelog('step4:OK')

    def init_spacesave(self, dryrun=False):
        if not dryrun:
            os.makedirs('./caltables', exist_ok=True)
            os.system('mv '+self.visname+'.split.bandpass ./caltables/')
            if self.spacesave:
                os.system('rm -rf '+self.visname)
                os.system('rm -rf '+self.visname+'.org')
                os.system('rm -rf '+self.visname+'.flagversions')
                os.system('rm -rf '+self.visname+'.tsys')
                os.system('rm -rf '+self.visname+'.wvr*')
                os.system('rm -rf '+self.visname+'.*.png')
                os.system('rm -rf '+self.visname+'.split.*')
                os.system('rm -rf *.asdm.sdm')
                os.system('rm -rf '+self.projID)

    # step5-1: split calibrator observations
    def uvfit_splitQSO(self, spw, field, dryrun=False):
        self.spw = spw
        self.field = field

        vis = self.visname + '.split'

        kw_split = {
            'vis': vis,
            'outputvis': f'calibrated/{vis}.{field}.spw_{spw}',
            'datacolumn': 'corrected',
            'spw': spw,
            'field': field,
            'intent': '*ON_SOURCE*',
            'keepflags': False,
        }

        # kw_mstransform = {
        #     'vis': vis,
        #     'outputvis': f'calibrated/{vis}.{self.field}.spw_{self.spw}',
        #     'datacolumn': 'corrected',
        #     'spw': spw,
        #     'field': field,
        #     'intent': '*ON_SOURCE*',
        #     'keepflags': False,
        #     'reindex': True,
        #     'regridms': True,
        #     'mode': 'channel',
        #     'outframe': 'LSRK',
        # }

        if not dryrun:
            os.system('mkdir -p calibrated')
            os.system('rm -rf '+kw_split['outputvis'])
            os.system('rm -rf '+kw_split['outputvis']+'.listobs')

            from casatasks import mstransform, listobs, delmod, split
            split(**kw_split)
            # mstransform(**kw_mstransform)
            delmod(vis=kw_split['outputvis'], otf=True, scr=False)
            listobs(vis=kw_split['outputvis'],
                    listfile=kw_split['outputvis']+'.listobs')

    def avgspws(self, inputvis, dryrun=False):
        tb.open(inputvis)
        sigma = tb.getcol('SIGMA')
        data = tb.getcol('DATA')
        ID = tb.getcol('DATA_DESC_ID')
        spwIDs = np.unique(ID)
        flag = tb.getcol('FLAG')
        flag_new = np.zeros_like(flag[:, :, ID == 0], dtype='bool')

        # new flag
        for i in range(flag[0][0][ID1 == 0].shape[0]):
            for ii in range(2):
                tmp = False
                for spwID in spwIDs:
                    tmp = bool(tmp + (~flag)[ii][0][ID == spwID][i])
                flag_new[ii][0][i] = not tmp

        # average
        data_new = np.zeros_like(flag_new, dtype='float')
        weight = np.zeros_like(flag_new, dtype='float')
        for spwID in spwIDs:
            data_new[:, 0, :] = data_new[:, 0, :] + \
                data[:, 0, ID == spwID]/sigma[:, ID == spwID]**2
            weight[:, 0, :] = weight[:, 0, :] + 1./sigma[:, ID == spwID]**2

        data_new = data_new/weight

    def uvfit_splitQSO_avg(self, spw, field, dryrun=False):
        self.spw = spw+'.avg'
        self.field = field

        if not dryrun:
            from casatasks import split, listobs, delmod
            os.system('mkdir -p ./calibrated')
            # Nchans = [aU.getNChanFromCaltable(self.visname+'.split')[int(spw)] for spw in self.spws]
            vis = self.visname + '.split'

            width = aU.getNChanFromCaltable(vis)
            if not isinstance(width, int):
                width = width[int(spw)]

            kw_split = {
                'vis': vis,
                'outputvis': f'calibrated/{vis}.{field}.spw_{spw}.avg',
                'datacolumn': 'corrected',
                'spw': spw,
                'width': width,
                'field': field,
                'intent': '*ON_SOURCE*',
                'keepflags': False,
            }

            # kw_mstransform = {
            #     'vis': kw_split['outputvis'],
            #     'outputvis': f'calibrated/{vis}.{field}.spw_{spw}.avg',
            #     'datacolumn': 'all',
            #     'keepflags': False,
            # }

            os.system('rm -rf '+kw_split['outputvis'])
            os.system('rm -rf '+kw_split['outputvis'])
            os.system('rm -rf '+kw_split['outputvis']+'.listobs')
            split(**kw_split)
            delmod(vis=kw_split['outputvis'], otf=True, scr=False)
            listobs(vis=kw_split['outputvis'],
                    listfile=kw_split['outputvis']+'.listobs')
            # mstransform(**kw_mstransform)
            # listobs(vis=kw_mstransform['outputvis'],listfile=kw_mstransform['outputvis']+'.listobs')
            # os.system('rm -rf '+kw_split['outputvis'])

    # step5-2: create model column
    def uvfit_createcol(self, modelcol=True, dryrun=False):
        if not dryrun:
            kw_clearcal = {
                'vis': f'calibrated/{self.visname}.split.{self.field}.spw_{self.spw}',
                'addmodel': modelcol,
            }

            from casatasks import clearcal
            clearcal(**kw_clearcal)

    # step5-3: do uvmultifit
    def uvfit_uvmultifit(self, intent=None, write="", column='data',
                         spwid='0', mfsfit=True, dryrun=False):

        if not dryrun:
            os.system('mkdir -p tempfiles')
            os.system('mkdir -p specdata')

            vis = self.visname + '.split'

            if intent is None:
                outfile = f'{vis}.{self.field}.spw_{self.spw}.dat'
            else:
                outfile = f'{vis}.{self.field}.spw_{self.spw}.{intent}.dat'

            from NordicARC import uvmultifit as uvm
            myfit = uvm.uvmultifit(
                    vis=f'calibrated/{vis}.{self.field}.spw_{self.spw}',
                    spw='0',
                    column=column,
                    field=0,
                    stokes='I',
                    NCPU=8,
                    pbeam=True,
                    dish_diameter=self.dish_diameter,
                    chanwidth=1,
                    var=['0,0,p[0]'],
                    p_ini=[10.0],
                    model=['delta'],
                    OneFitPerChannel=(not mfsfit),
                    write=write,
                    method='simplex',
                    bounds=[[0, None]],
                    outfile=f'./specdata/{outfile}',
                    )

    # step5-4: gaincal
    def uvfit_gaincal(self, intent='phase', solint='int', solnorm=False,
                      gaintype='G', calmode='p', gaintable='', dryrun=False):
        vis = self.visname + '.split'
        # if vis not in glob.glob('./*'):
        #     vis = self.visname

        kw_gaincal = {
            'vis': 'calibrated/'+vis+'.'+self.field+'.spw_'+self.spw,
            'caltable': f'./caltables/{vis}.{self.field}.spw_{self.spw}\
                    .{intent}',
            'field': '0',
            'solint': solint,
            'refant': self.refant[0],
            'gaintype': gaintype,
            'calmode': calmode,
            'minsnr': 2.0,
            'gaintable': gaintable,
            'solnorm': solnorm,
        }

        if not dryrun:
            os.system('mkdir -p caltables')
            os.system('rm -rf '+kw_gaincal['caltable'])

            from casatasks import gaincal
            gaincal(**kw_gaincal)

        return kw_gaincal['caltable']

    # step5-5: applycal
    def uvfit_applycal(self, gaintable='', dryrun=False, removeflag=False):
        if not dryrun:
            vis = self.visname + '.split'
            # if vis not in glob.glob('./*'):
            #     vis = self.visname

            kw_applycal = {
                'vis': 'calibrated/'+vis+'.'+self.field+'.spw_'+self.spw,
                'interp': 'linear',
                'flagbackup': False,
                'applymode': 'calflag',
                'gaintable': gaintable,
                'calwt': False,
            }

            from casatasks import applycal
            applycal(**kw_applycal)

            if removeflag:
                kw_mstransform = {
                    'vis': 'calibrated/'+vis+'.'+self.field+'.spw_'+self.spw+'.tmp',
                    'outputvis': 'calibrated/'+vis+'.'+self.field+'.spw_'+self.spw,
                    'datacolumn': 'all',
                    'keepflags': False,
                }

                from casatasks import mstransform, listobs
                os.system('mv '+kw_applycal['vis']+' '+kw_mstransform['vis'])
                os.system('rm -rf '+kw_mstransform['outputvis']+'.listobs')
                mstransform(**kw_mstransform)
                os.system('rm -rf '+kw_mstransform['vis'])
                listobs(vis=kw_mstransform['outputvis'],
                        listfile=kw_mstransform['outputvis']+'.listobs')

    # step5-6: gainplot
    def uvfit_gainplot(self, type='amp_phase', dryrun=False, allspws=False):

        if not dryrun:
            from casatools import table
            tb = table()
            import matplotlib.pyplot as plt

            if allspws:
                for field in self.fields:
                    for spw in self.spws:
                        # spw = 'all'
                        caltablebase = self.asdmname+'.ms.split.'+field+'.spw_'+spw+'.avg'
                        caltable0 = './caltables/' + caltablebase + '.'+type+'_0'
                        caltable1 = './caltables/' + caltablebase + '.'+type+'_1'

                        tb.open(caltable0)
                        Time0 = tb.getcol('TIME').copy()
                        cgain0 = tb.getcol('CPARAM').copy()
                        ant0 = tb.getcol('ANTENNA1') .copy()
                        tb.close()

                        tb.open(caltable1)
                        Time1 = tb.getcol('TIME').copy()
                        cgain1 = tb.getcol('CPARAM').copy()
                        ant1 = tb.getcol('ANTENNA1') .copy()
                        tb.close()

                        if type == 'phase':
                            phase0_0 = np.angle(cgain0[0][0], deg=True)
                            phase0_1 = np.angle(cgain0[1][0], deg=True)
                            phase1 = np.angle(cgain1[0][0], deg=True)
                        elif type == 'amp_phase':
                            phase0_0 = np.abs(cgain0[0][0])
                            phase1 = np.abs(cgain1[0][0])

                        plt.close()
                        titlename = self.asdmname+' '+field+' spw:'+spw
                        plt.title(titlename)
                        plt.scatter((Time0-Time0[0])/60., phase0_0, c='b', s=2)
                        if type == 'phase':
                            plt.scatter(
                                (Time0-Time0[0])/60., phase0_1, c='b', s=2)
                        plt.scatter((Time1-Time1[0])/60., phase1, c='r', s=1)
                        plt.xlabel('Time from the first integration [min]')
                        if type == 'phase':
                            plt.ylabel('Gain phase [deg]')
                        elif type == 'amp_phase':
                            plt.ylabel('Gain amplitude')
                        plt.savefig('./caltables/'+caltablebase +
                                    '.gainplot.'+type+'.png')
                        plt.savefig('./caltables/'+caltablebase +
                                    '.gainplot.'+type+'.pdf')
                        plt.close()

            else:

                for field in self.fields:
                    for spw in self.spws:
                        caltablebase = self.asdmname+'.ms.split.'+field+'.spw_'+spw
                        caltable0 = './caltables/' + caltablebase + '.'+type+'_0'
                        caltable1 = './caltables/' + caltablebase + '.'+type+'_1'

                        tb.open(caltable0)
                        Time0 = tb.getcol('TIME').copy()
                        cgain0 = tb.getcol('CPARAM').copy()
                        ant0 = tb.getcol('ANTENNA1') .copy()
                        tb.close()

                        tb.open(caltable1)
                        Time1 = tb.getcol('TIME').copy()
                        cgain1 = tb.getcol('CPARAM').copy()
                        ant1 = tb.getcol('ANTENNA1') .copy()
                        tb.close()

                        if type == 'phase':
                            phase0_0 = np.angle(cgain0[0][0], deg=True)
                            phase0_1 = np.angle(cgain0[1][0], deg=True)
                            phase1 = np.angle(cgain1[0][0], deg=True)
                        elif type == 'amp_phase':
                            phase0_0 = np.abs(cgain0[0][0])
                            phase1 = np.abs(cgain1[0][0])

                        plt.close()
                        titlename = self.asdmname+' '+field+' spw:'+spw
                        plt.title(titlename)
                        plt.scatter((Time0-Time0[0])/60., phase0_0, c='b', s=2)
                        if type == 'phase':
                            plt.scatter(
                                (Time0-Time0[0])/60., phase0_1, c='b', s=2)
                        plt.scatter((Time1-Time1[0])/60., phase1, c='r', s=1)
                        plt.xlabel('Time from the first integration [min]')
                        if type == 'phase':
                            plt.ylabel('Gain phase [deg]')
                        elif type == 'amp_phase':
                            plt.ylabel('Gain amplitude')
                        plt.savefig('./caltables/'+caltablebase +
                                    '.gainplot.'+type+'.png')
                        plt.savefig('./caltables/'+caltablebase +
                                    '.gainplot.'+type+'.pdf')
                        plt.close()

    # step5-7: uvfitting
    def uvfit_man(self, datacolumn='data', intent=None, write_residuals=False, savemodel=False, dryrun=False, meansub=False, oldmode=True):

        if not dryrun:
            if not oldmode:
                from casatools import table
                from scipy.optimize import least_squares
                tb = table()
                tb.open('calibrated/'+self.visname +
                        '.split.'+self.field+'.spw_'+self.spw)
                if datacolumn == 'data':
                    data = tb.getcol('DATA').copy()
                elif datacolumn == 'corrected':
                    data = tb.getcol('CORRECTED_DATA').copy()
                flag = tb.getcol('FLAG').copy()
                weight = tb.getcol('WEIGHT').copy().reshape(
                    [2, 1, flag.shape[2]])
                tb.close()

                def res_func(param, x, y):
                    res = (y - (param[0] + 0.*1j))**2*weight
                    return np.abs(res)[~flag]

                res = least_squares(res_func, [1.0], args=(
                    np.zeros_like(data), data))
                print('### fit ###')
                print(res.x[0])

                model = np.zeros_like(data, dtype='complex')
                spec = np.zeros(1) + res.x[0]

                for i in range(data.shape[2]):
                    model[0, :, i] = model[0, :, i] + spec.astype('complex')
                    model[1, :, i] = model[1, :, i] + spec.astype('complex')

                tb.open('calibrated/'+self.visname+'.split.' +
                        self.field+'.spw_'+self.spw, nomodify=False)
                if savemodel:
                    tb.putcol('MODEL_DATA', model.copy())

                if write_residuals:
                    new_corr = (data.copy() - model.copy())
                    tb.putcol('CORRECTED_DATA', new_corr)

                tb.flush()
                tb.close()

            else:
                from casatools import table
                from scipy.optimize import least_squares
                tb = table()

                if intent is None:
                    infile = './specdata/'+self.visname + \
                        '.split.'+self.field+'.spw_'+self.spw+'.dat'
                else:
                    infile = './specdata/'+self.visname+'.split.' + \
                        self.field+'.spw_'+self.spw+'.'+intent+'.dat'

                # spec
                tb.open('calibrated/'+self.visname +
                        '.split.'+self.field+'.spw_'+self.spw)
                data = tb.getcol('DATA')
                model = np.zeros_like(data, dtype='complex')
                modeldata = np.loadtxt(infile)
                spec = np.zeros(1) + modeldata[1]

                for i in range(data.shape[2]):
                    model[0, :, i] = model[0, :, i] + spec.astype('complex')
                    model[1, :, i] = model[1, :, i] + spec.astype('complex')

                tb.close()
                tb.open('calibrated/'+self.visname+'.split.' +
                        self.field+'.spw_'+self.spw, nomodify=False)
                if savemodel:
                    tb.putcol('MODEL_DATA', model.copy())

                if write_residuals:
                    if datacolumn == 'data':
                        res = data.copy() - model.copy()
                    elif datacolumn == 'corrected':
                        corr_data = tb.getcol('CORRECTED_DATA')
                        res = corr_data.copy() - model.copy()
                    tb.putcol('CORRECTED_DATA', res)

                tb.flush()
                tb.close()

    # manural flagging
    def uvfit_flag_man(self, intent=None, nsigma=10., dryrun=False):

        if not dryrun:
            from casatools import table
            tb = table()

            if intent is None:
                infile = './specdata/'+self.visname+'.split.'+self.field+'.spw_'+self.spw+'.dat'
            else:
                infile = './specdata/'+self.visname+'.split.' + \
                    self.field+'.spw_'+self.spw+'.'+intent+'.dat'

            vis = 'calibrated/'+self.visname+'.split.'+self.field+'.spw_'+self.spw

            tb.open(vis)
            corr_data = tb.getcol('CORRECTED_DATA')
            Time = tb.getcol('TIME')
            flag = tb.getcol('FLAG')
            ndata = corr_data.shape[0]*corr_data.shape[2]
            fitdata = np.loadtxt(infile)
            threshold = nsigma * fitdata[2] * (ndata)**0.5
            flagsigma = (np.abs(corr_data) > threshold)
            flag_new = flag + flagsigma
            tb.close()

            Time_flag = Time[(flag_new[0][0] + flag_new[1][0])]
            flag_res = np.zeros_like(flag_new, dtype='bool')
            for i in range(Time.shape[0]):
                if Time[i] in Time_flag:
                    flag_res[0][0][i] = True
                    flag_res[1][0][i] = True
                else:
                    flag_res[0][0][i] = False
                    flag_res[1][0][i] = False

            tb.open(vis, nomodify=False)
            tb.putcol('FLAG', flag_res)
            tb.flush()
            tb.close()

    # step5: uvmultifit & selfcal
    def uvfit_run(self, dryrun=False, plot=True):
        for _field in self.fields:
            for _spw in self.spws:
                # selfcal by avaraged MS
                print(f'### field: {_field}, spw: {_spw} ###')
                print('step5-1')
                self.uvfit_splitQSO_avg(spw=_spw, field=_field, dryrun=dryrun)
                print('step5-2 (1)')
                self.uvfit_createcol(dryrun=dryrun)
                print('step5-3 (1)')
                self.uvfit_uvmultifit(
                    write='', column='data', dryrun=dryrun, mfsfit=True, intent='noselfcal')
                print('step5-7 (1)')
                self.uvfit_man(datacolumn='data', write_residuals=False,
                               savemodel=True, intent='noselfcal', dryrun=dryrun, meansub=False)

                print('step5-4 (1)')
                gaintable_p = self.uvfit_gaincal(
                    intent='phase_0', solint='int', gaintype='G', calmode='p', gaintable='', dryrun=dryrun)
                print('step5-4 (2)')
                gaintable_ap = self.uvfit_gaincal(
                    intent='amp_phase_0', solint='int', solnorm=True, gaintype='T', calmode='ap', gaintable=[gaintable_p], dryrun=dryrun)
                print('step5-5 (1)')
                self.uvfit_applycal(
                    gaintable=[gaintable_p, gaintable_ap], dryrun=dryrun, removeflag=False)

                print('step5-3 (2)')
                self.uvfit_uvmultifit(
                    write='', column='corrected', intent='selfcal', dryrun=dryrun, mfsfit=True)
                print('step5-7 (2)')
                self.uvfit_man(datacolumn='corrected', write_residuals=True,
                               savemodel=True, intent='selfcal', dryrun=dryrun, meansub=False)

                print('step5-4 (3)')
                gaintable_p1 = self.uvfit_gaincal(intent='phase_1', solint='int', gaintype='T', calmode='p', gaintable=[
                                                  gaintable_p, gaintable_ap], dryrun=dryrun)
                print('step5-4 (4)')
                gaintable_ap1 = self.uvfit_gaincal(intent='amp_phase_1', solint='int', solnorm=True, gaintype='T', calmode='ap', gaintable=[
                                                   gaintable_p, gaintable_ap, gaintable_p1], dryrun=dryrun)
                
                # selfcal by no-avaraged MS
                print('step5-1\'')
                self.uvfit_splitQSO(spw=_spw, field=_field, dryrun=dryrun)
                print('step5-2 (2)')
                self.uvfit_createcol(dryrun=dryrun)
                print('step5-3 (3)')
                self.uvfit_uvmultifit(
                    write='', column='data', intent='noselfcal', dryrun=dryrun, mfsfit=False)
                print('step5-5 (2)')
                self.uvfit_applycal(
                    gaintable=[gaintable_p, gaintable_ap, gaintable_p1, gaintable_ap1], dryrun=dryrun)
                print('step5-3 (4)')
                self.uvfit_uvmultifit(
                    write='', column='corrected', intent='selfcal', dryrun=dryrun, mfsfit=False)
                if self.spacesave:
                    os.system('rm -rf calibrated/'+self.visname +
                              '.split.'+self.field+'.spw_'+self.spw)
                    os.system('rm -rf calibrated/'+self.visname +
                              '.split.'+self.field+'.spw_'+self.spw+'.listobs')

        self.uvfit_gainplot(dryrun=(not plot), allspws=True, type='phase')
        self.uvfit_gainplot(dryrun=(not plot), allspws=True, type='amp_phase')

        self.writelog('step5:OK')

    # step6: continuum imaging
    def cont_imaging(self, clean=False, dryrun=False):

        if not dryrun:

            for field in self.fields:
                os.system('rm -rf '+'./calibrated/concat.'+field+'.ms')
                visForimsg = glob.glob(
                    './calibrated/'+self.visname+'.split.'+field+'.spw_*.avg')

                kw_tclean = {
                    'vis': visForimsg,
                    'imagename': './imsg/'+self.asdmname+'.'+field+'.residual.allspw.selfcal.mfs.briggs.robust_0.5.dirty',
                    'datacolumn': 'corrected',
                    'imsize': self.imsize,
                    'cell': self.cell,
                    'weighting': 'briggs',
                    'robust': 0.5,
                    'deconvolver': 'hogbom',
                    'gridder': 'standard',
                    'specmode': 'mfs',
                    'threshold': '0mJy',
                    'niter': 0,
                    'nterms': 2,
                    'interactive': False,
                    'pbcor': True,
                    'restoringbeam': 'common',
                }

                os.system('mkdir -p imsg')
                os.system('rm -rf '+kw_tclean['imagename']+'*')
                from casatasks import tclean, exportfits
                tclean(**kw_tclean)
                exportfits(kw_tclean['imagename']+'.image',
                           kw_tclean['imagename']+'.image.fits')
                exportfits(kw_tclean['imagename']+'.image.pbcor',
                           kw_tclean['imagename']+'.image.pbcor.fits')
                exportfits(kw_tclean['imagename']+'.psf',
                           kw_tclean['imagename']+'.psf.fits')

                for ext in ['.image', '.mask', '.model', '.image.pbcor', '.residual', '.psf', '.pb', '.sumwt']:
                    os.system('rm -rf '+kw_tclean['imagename']+ext)

                if clean:
                    from casatasks import imstat
                    imgstat = imstat(
                        kw_tclean['imagename']+'.image.fits', algorithm='biweight')
                    threshold = '{:.2f}'.format(imgstat['sigma'][0]*1000)+'mJy'
                    kw_tclean = {
                        'vis': visForimsg,
                        'imagename': './imsg/'+self.asdmname+'.'+field+'.residual.allspw.selfcal.mfs.briggs.robust_0.5.3sigma.clean',
                        'datacolumn': 'corrected',
                        'imsize': self.imsize,
                        'cell': self.cell,
                        'weighting': 'briggs',
                        'robust': 0.5,
                        'deconvolver': 'hogbom',
                        'gridder': 'standard',
                        'specmode': 'mfs',
                        'threshold': threshold,
                        'niter': 1000000,
                        'nterms': 2,
                        'interactive': False,
                        'pbcor': True,
                        'restoringbeam': 'common',
                    }

                    os.system('mkdir -p imsg')
                    os.system('rm -rf '+kw_tclean['imagename']+'*')
                    from casatasks import tclean, exportfits
                    tclean(**kw_tclean)
                    exportfits(kw_tclean['imagename']+'.image',
                               kw_tclean['imagename']+'.image.fits')
                    exportfits(kw_tclean['imagename']+'.image.pbcor',
                               kw_tclean['imagename']+'.image.pbcor.fits')
                    exportfits(kw_tclean['imagename']+'.psf',
                               kw_tclean['imagename']+'.psf.fits')

                    for ext in ['.image', '.mask', '.model', '.image.pbcor', '.psf', '.residual', '.pb', '.sumwt']:
                        os.system('rm -rf '+kw_tclean['imagename']+ext)

        self.writelog('step6:OK')

    # step7: spacesaving
    def spacesaving(self, gzip=False, dryrun=False):

        if not dryrun:
            if self.spacesave:
                from casatasks import mstransform, listobs
                for field in self.fields:
                    for spw in self.spws:
                        kw_mstransform = {
                            'vis': 'calibrated/'+self.visname+'.split.'+field+'.spw_'+spw+'.avg',
                            'outputvis': 'calibrated/'+self.visname+'.split.'+field+'.spw_'+spw+'.avg'+'.selfcal.residual',
                            'datacolumn': 'corrected',
                            'keepflags': True
                        }

                        os.system('rm -rf '+kw_mstransform['outputvis'])
                        mstransform(**kw_mstransform)
                        listobs(
                            vis=kw_mstransform['outputvis'], listfile=kw_mstransform['outputvis']+'.listobs')
                        os.system('rm -rf '+kw_mstransform['vis'])
                        os.system('rm -rf '+kw_mstransform['vis']+'.listobs')

                try:
                    os.system('mkdir -p log')
                    os.system('mv ./casa-*.log ./log/')
                    os.system('cp ./calibrated/*.listobs ./log/')
                except Exception:
                    print('ERRPR: copy casalog failed')

                try:
                    os.system('mv ../log/'+self.tarfilename+'*.log ./log/')
                except Exception:
                    pass

                try:
                    os.system('mv ./*.py ./log/')
                except Exception:
                    pass

                os.system('rm -rf *.last')
                os.system('rm -rf byspw')
                os.system('rm -rf tempfiles')
                os.system('rm -rf '+self.asdmname+'*')
                os.system('rm -rf '+self.projID)

                if gzip:
                    os.system('gzip -1 -v '+glob.glob('*.tar')[0])
                    os.system('rm -rf '+'calibrated.tar.gz')
                    os.system('tar -zcvf calibrated.tar.gz calibrated')
                    os.system('rm -rf ./calibrated')

        self.writelog('step7:OK')

    # step8: spectrum plot
    def specplot(self, dryrun=False):

        failflag = False

        if not dryrun:
            from astropy import stats
            import matplotlib.pyplot as plt

            for field in self.fields:
                if field[0] == 'J':
                    for spw in self.spws:
                        for selfcal in ['noselfcal', 'selfcal']:
                            try:
                                specfile = './specdata/'+self.visname + \
                                    '.split.'+field+'.spw_'+spw+'.'+selfcal+'.dat'
                                data = np.loadtxt(specfile)
                                freq = data[:, 0]/1.0e9  # GHz
                                spec = data[:, 1]  # Jy
                                spec_ma = stats.sigma_clip(spec, sigma=3.)

                                pp = np.ma.polyfit(freq, spec_ma, deg=1)
                                # cont = np.ma.median(spec_ma)
                                cont = pp[0]*freq+pp[1]
                                rms = np.ma.std(spec_ma/cont)
                                detect = np.ma.array(np.full_like(freq, np.ma.max(
                                    spec_ma/cont)+2.5*rms), mask=~spec_ma.mask)

                                ymax = np.max(spec/cont) + 5*rms
                                ymin = np.min(spec/cont) - 5*rms

                                plt.close()
                                plt.rcParams['font.family'] = 'Times New Roman'
                                plt.rcParams['mathtext.fontset'] = 'stix'
                                plt.rcParams["figure.dpi"] = 200
                                plt.rcParams["font.size"] = 20

                                plt.figure(figsize=[10, 8])
                                # plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))

                                plt.step(freq, spec/cont,
                                         where='mid', c='b', lw=1)
                                plt.plot(freq, detect, 'r-', lw=5)
                                plt.xlabel('frequency [GHz]')
                                plt.ylabel('line/continuum')
                                titlename = self.asdmname + ': ' + field + ' spw' + spw
                                plt.title(titlename)
                                os.system('mkdir -p specplot')
                                os.system('mkdir -p specplot/'+selfcal)
                                plt.ylim(ymin, ymax)
                                plt.savefig(
                                    './specplot/'+selfcal+'/'+self.asdmname + '.' + field + '.spw' + spw + '.pdf')
                                plt.savefig(
                                    './specplot/'+selfcal+'/'+self.asdmname + '.' + field + '.spw' + spw + '.png')
                                plt.close()

                            except Exception:
                                failflag = True

        if failflag:
            self.writelog('step8:Partially failed')
        else:
            self.writelog('step8:OK')
