import sys
sys.path.append('../almaqso')
from almaqso import analysis

tarfilename = './2018.1.01575.S_uid___A002_Xd68367_X9885.asdm.sdm.tar'
analysis(tarfilename, skipflag='', casacmd='$HOME/.local/casa/casa-6.6.1-17-pipeline-2024.1.0.8-py3.8.el8/bin/casa')
