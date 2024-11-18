import os
import sys
from pathlib import Path
sys.path.append('../almaqso')
from almaqso.analysis import analysis

CURRENT_DIR = Path(__file__).parent
DATA_PATH = f'{CURRENT_DIR}/uid___A002_Xd68367_X9885'
TARFILE = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'

os.system(f'rm -rf {DATA_PATH}')
analysis(TARFILE, skipflag='', casacmd='/usr/local/casa/casa-6.6.1-17-pipeline-2024.1.0.8-py3.8.el8/bin/casa')
assert os.path.exists(DATA_PATH)
