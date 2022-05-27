from astroquery.alma import Alma
import numpy as np
import pyvo
import pandas as pd
import os

from concurrent.futures import ThreadPoolExecutor
from logging import StreamHandler, Formatter, INFO, getLogger

def init_logger():
    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(Formatter("[%(asctime)s] [%(threadName)s] %(message)s"))
    logger = getLogger()
    logger.addHandler(handler)
    logger.setLevel(INFO)

class QSOquery:
    def __init__(self,sname,band='4',almaurl='https://almascience.nao.ac.jp',download_d='./',replaceNAOJ=False):
        self.sname = sname
        self.band = band
        self.almaurl = almaurl
        self.myAlma = Alma()
        self.myAlma.archive_url = almaurl
        self.download_d = download_d
        self.replaceNAOJ=False

    def queryALMA(self,almaquery=True):
        service = pyvo.dal.TAPService(self.almaurl+"/tap")
        query = f"""
                SELECT *
                FROM ivoa.obscore
                WHERE target_name = '{self.sname}'  AND band_list = '{self.band}' AND data_rights = 'Public' """

        if almaquery:
            return self.myAlma.query_tap(query).to_table().to_pandas()
        else:
            return service.search(query).to_table().to_pandas()

    def get_data_urls(self,almaquery=True):
        rlist = self.queryALMA(almaquery=almaquery)
        mous_list = np.unique(rlist['member_ous_uid'])

        total_size = 0.
        url_list = np.zeros([1,2]).astype(dtype='<U120')
        for (id,mous) in zip(range(len(mous_list)),mous_list):
            uid_url_table = self.myAlma.get_data_info(mous)

            url_size = [[url,size] for (url,size) in zip(uid_url_table['access_url'],uid_url_table['content_length']) if '.asdm.sdm.tar' in url]

            asdm_size = (np.array(url_size)[:,1].astype('float')).sum()/1.e9

            url_list = np.vstack([url_list,np.array(url_size)])
            print('['+str(id+1)+'/'+str(len(mous_list))+'] '+str(asdm_size))
            total_size = total_size + asdm_size

        url_list = url_list[1:]

        self.rlist = rlist
        self.total_size = total_size
        self.url_list = url_list

    def wget_f(self,num):
        getLogger().info("%s start", num)
        if self.replaceNAOJ:
            download_url = (self.url_list[num][0]).replace(self.almaurl,"https://almascience.nao.ac.jp")
        else:
            download_url = self.url_list[num][0]
        os.system('wget -q -P '+self.download_d+' '+download_url)
        getLogger().info("%s end", num)

    def download(self):
        nFiles = self.url_list.shape[0]
        init_logger()
        getLogger().info("main start")
        with ThreadPoolExecutor(max_workers=min(nFiles,5), thread_name_prefix="thread") as executor:
            for i in range(nFiles):
                executor.submit(self.wget_f, i)
            getLogger().info("submit end")
        getLogger().info("main end")
