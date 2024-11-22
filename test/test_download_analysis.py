import os
import sys
import subprocess
from pathlib import Path
sys.path.append('../almaqso')  # isort:skip
from almaqso.download_archive import download_archive

CURRENT_DIR = Path(__file__).parent
CASA_PATH = os.environ.get('ALMAQSO_CASA', 'casa')
DATA_PATH = './uid___A002_Xd68367_X9885'
TARFILE = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'

# Edit the following constants.
DOWNLOAD = False  # True: Download the tar file, False: Use the existing tar file
MODE = 'aftercal'  # 'all': All Steps, 'calonly': Step 1-4, 'aftercal': Step 5-8 of analysis


def run_casa_script(script_name):
    try:
        result = subprocess.run(
            [CASA_PATH, '--nologger', '--nogui', '-c', script_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"STDOUT for {script_name}:", result.stdout)
        print(f"STDERR for {script_name}:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {script_name}:")
        print(f"Return Code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise


def test_download():
    if DOWNLOAD:
        os.system(f'rm -rf {TARFILE}')
        download_archive(4, 'catalog/test_2.json')
        assert os.path.exists(TARFILE)
    os.system(f'rm -rf {DATA_PATH}')


def test_analysis():
    if MODE == 'aftercal':
        os.system(f'cp -r {DATA_PATH}_backup {DATA_PATH}')

    cmd = "sys.path.append('../almaqso');" + \
        "from almaqso.analysis import analysis;" + \
        f"analysis('{TARFILE}', skipflag=''," + \
        f"casacmd='{CASA_PATH}', mode='{MODE}')"
    run_casa_script(cmd)

    if MODE == 'calonly':
        os.system(f'cp -r {DATA_PATH} {DATA_PATH}_backup')
