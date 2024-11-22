# almaqso

This repository is a folk of [astroysmr/almaqso](https://github.com/astroysmr/almaqso), which is no longer maintained.
So many bugs are still there, and I am trying to fix them.

**PLEASE REFER TO THE [ISSUE](https://github.com/skrbcr/almaqso/issues) SECTION SINCE IT CONTAINS THE BUGS AND INFORMATION.**

## Pre-requisites

### CASA

- Please use CASA with ALMA pipeline. I am using `CASA version 6.6.1-17-pipeline-2024.1.0.8`.

### CASA Modules

- analysisUtilities
- UVMultiFit  If you use CASA 6, you should switch the branch to `develop` to build properly.

Details (e.g., how to install and modify) are described in [Pre-requisites](PreRequisites.md).

## Test

### CASA to use

First, make sure that you have CASA with alma pipeline installed e.g., the version that I am using.
To set environment variables shown below, you can tell this program which CASA to use:

**`bash` and `zsh`**

Write above line in your `.bashrc` or `.zshrc`.

```shell
export ALMAQSO_CASA=/path/to/your/casa
```

**`fish`**

Write above line in your `config.fish`.

```shell
set -gx ALMAQSO_CASA /path/to/your/casa
```

### Prepare the environment

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

### Test run

Edit `test/test_download_analysis.py`:

```python
# test/test_download_analysis.py
# Edit the following constants.
DOWNLOAD = False  # True: Download the tar file, False: Use the existing tar file
MODE = 'aftercal'  # 'all': All Steps, 'calonly': Step 1-4, 'aftercal': Step 5-8 of analysis
```

Then you can run the test by

```
$ pytest
```
