import os
from .QSOanalysis import QSOanalysis


def _analysis(tarfilename: str, skip=True, casacmd='casa', mode='all'):
    obj = QSOanalysis(tarfilename, spacesave=True, casacmd=casacmd, casacmdforuvfit='casa')

    asdmname = 'uid___' + (tarfilename.split('_uid___')
                           [1]).replace('.asdm.sdm.tar', '')

    if os.path.exists(asdmname) and skip:
        print(asdmname+': analysis already done and skip')

    else:
        if os.path.exists(asdmname):
            print(asdmname+': analysis already done but reanalyzed')

        if mode == 'aftercal':
            dryrun = True
        else:
            dryrun = False

        print('step:0')
        obj.intial_proc(dryrun=dryrun)
        print('step:1')
        obj.importasdm(dryrun=dryrun)
        print('step:2')
        obj.gen_calib_script(dryrun=dryrun)
        print('step:3')
        obj.remove_target(dryrun=dryrun)
        print('step:4')
        obj.doCalib(dryrun=dryrun)
        # obj.init_spacesave()

        if mode != 'calonly':
            print('step:5')
            obj.uvfit_run(plot=True)
            print('step:6')
            obj.cont_imaging()
            print('step:7')
            obj.spacesaving(gzip=True)

            print('step:8')
            obj.specplot()
