import os
import sys
from pathlib import Path
sys.path.append('../almaqso')  # isort:skip
from almaqso.analysis import analysis

CURRENT_DIR = Path(__file__).parent
CASA_PATH = os.environ.get('ALMAQSO_CASA', 'casa')
DATA_PATH = './uid___A002_Xd68367_X9885'
TARFILE = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'

os.system(f'rm -rf {DATA_PATH}')
analysis(
    TARFILE,
    skipflag='',
    casacmd=CASA_PATH
)
assert os.path.exists(DATA_PATH)
