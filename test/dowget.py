import os
import sys
import numpy as np

args = sys.argv

replaceNAOJ = True
dryrun = False
download_d = args[2]
nworker = 10

from concurrent.futures import ThreadPoolExecutor
from logging import StreamHandler, Formatter, INFO, getLogger

flist = np.unique(np.load(args[1])[:,0])

def init_logger():
    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(Formatter("[%(asctime)s] [%(threadName)s] %(message)s"))
    logger = getLogger()
    logger.addHandler(handler)
    logger.setLevel(INFO)

def wget_f(num):
    getLogger().info("%s start", num)
    if replaceNAOJ:
        download_url = (flist[num]).replace("https://almascience.eso.org","https://almascience.nao.ac.jp")
    else:
        download_url = flist[num]
    print('wget -q --no-check-certificate -P '+download_d+' '+download_url)

    if not dryrun:
        os.system('wget -q --no-check-certificate -P '+download_d+' '+download_url)
    getLogger().info("%s end", num)


def download():
    nFiles = flist.shape[0]

    init_logger()
    getLogger().info("main start")
    with ThreadPoolExecutor(max_workers=min(nFiles,nworker), thread_name_prefix="thread") as executor:
        for i in range(nFiles):
            executor.submit(wget_f, i)
        getLogger().info("submit end")
    getLogger().info("main end")

if __name__ == '__main__':
    download()

###
