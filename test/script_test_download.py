import os
import sys
from pathlib import Path
sys.path.append('../almaqso')
from almaqso.search_archive import search_archive

CURRENT_DIR = Path(__file__).parent
TARFILE = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'

os.system(f'rm -rf {TARFILE}')
search_archive(4, 'catalog/test_2.json')
assert os.path.exists(TARFILE)
