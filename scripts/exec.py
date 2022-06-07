import os
import sys
import numpy as np
import time

args = sys.argv

dryrun = False
nworker = int(args[2])

from concurrent.futures import ThreadPoolExecutor
from logging import StreamHandler, Formatter, INFO, getLogger

flist = np.load(args[1])
try:
    skipflag = args[3]
except:
    skipflag = 'do'

def init_logger():
    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(Formatter("[%(asctime)s] [%(threadName)s] %(message)s"))
    logger = getLogger()
    logger.addHandler(handler)
    logger.setLevel(INFO)

def casa_f(num):
    getLogger().info("%s start", num)

    if not dryrun:
        tarfilename = flist[num]
        cmdfile = 'exec_analysis.py'

        os.system('mkdir -p python_scripts')
        os.system('mkdir -p log')

        f = open('./python_scripts/'+cmdfile.replace('.py','.'+tarfilename+'.py'),'w')
        f.write('tarfilename = "'+tarfilename+'"'+'\n')
        f.write('skipflag = "'+str(skipflag)+'"'+'\n')
        f.write('execfile('+'"'+cmdfile+'"'+',globals())'+'\n')
        f.close()

        cmd = '"' + 'execfile('+"'"+'./python_scripts/'+cmdfile.replace('.py','.'+tarfilename+'.py')+"'"+')' +'"'
        print('running: '+tarfilename)

        os.system('touch ./log/'+tarfilename+'.term.log')
        os.system('casa --nologger --nogui --logfile ./log/'+tarfilename+'.casa.log -c '+cmd+' >> '+'./log/'+tarfilename+'.term.log')
    else:
        print('dryrun: '+tarfilename)

    getLogger().info("%s end", num)


def pipe_run():
    nFiles = flist.shape[0]

    init_logger()
    getLogger().info("main start")
    with ThreadPoolExecutor(max_workers=min(nFiles,nworker), thread_name_prefix="thread") as executor:
        for i in range(nFiles):
            executor.submit(casa_f, i)
        getLogger().info("submit end")
    getLogger().info("main end")

if __name__ == '__main__':
    pipe_run()
