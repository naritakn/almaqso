# almaqso

This repository is a folk of [astroysmr/almaqso](https://github.com/astroysmr/almaqso), which is no longer maintained.

```shell
$ echo 'export CASA_AU_PATH=/hoge/hoge/hoge/analysis_scripts' >> ~/.bash_profile
$ echo 'export CASA_FOR_UVFIT=/hoge/hoge/hoge/casa-pipeline-release-5.6.2-2.el7/bin/casa' >> ~/.bash_profile
$ source ~/.bash_profile
```

## For client

- I am now currently testing this repository with `CASA version 6.6.1-17-pipeline-2024.1.0.8`.
- I am using the latest version of `Python`. Maybe any version of `Python` newer than `3.8` is fine.
- You may need to modify the `analysisUtilities.py` provided by NRAO. Details are described [here](https://github.com/skrbcr/almaqso/issues/2).
- To follow other bugs or information, please refer the [issues](https://github.com/skrbcr/almaqso/issues).

## Test

First, make sure that you have CASA with alma pipeline installed e.g., the version that I am using.
Then please install pipenv.

```shell
$ pip install pipenv
```

Then, you can reproduce the environment by

```shell
$ pipenv install --dev
```

You can enter the environment by

```shell
$ pipenv shell
```

Then, you can run the downloading test by
```
$ python test/script_test_download.py
```

To test analysis after this downloading, you have to modify the `test/script_test_analysis.py` and `test/test_download_analysis.py`.
I am considering to make it more automatic, but for now, you have to modify the path to your CASA.

```python
# test/script_test_analysis.py
import os
import sys
from pathlib import Path
sys.path.append('../almaqso')
from almaqso.analysis import analysis

CURRENT_DIR = Path(__file__).parent
DATA_PATH = f'{CURRENT_DIR}/uid___A002_Xd68367_X9885'
TARFILE = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'

os.system(f'rm -rf {DATA_PATH}')
analysis(TARFILE, skipflag='', casacmd='/usr/local/casa/casa-6.6.1-17-pipeline-2024.1.0.8-py3.8.el8/bin/casa')  # Please modify the path to your CASA
assert os.path.exists(DATA_PATH)
```

```python
# test/test_download_analysis.py
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CASA_PATH = '/usr/local/casa/casa-6.6.1-17-pipeline-2024.1.0.8-py3.8.el8/bin/casa'  # Please modify the path to your CASA

# Ommitted...
```

Then, you can run the download and analysis test by

```
$ pytest
```
