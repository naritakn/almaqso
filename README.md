# almaqso

This repository is a folk of [astroysmr/almaqso](https://github.com/astroysmr/almaqso), which is no longer maintained.
So many bugs are still there, and I am trying to fix them.

**PLEASE REFER TO THE [ISSUE](https://github.com/skrbcr/almaqso/issues) SECTION SINCE IT CONTAINS THE BUGS AND INFORMATION.**

## Pre-requisites

### CASA

- Please use CASA with ALMA pipeline. I am using `CASA version 6.6.1-17-pipeline-2024.1.0.8`.

### CASA Modules

- analysisUtilities
- [UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit): The installation is guided [here](https://github.com/onsala-space-observatory/UVMultiFit/blob/master/INSTALL.md). If you use CASA version 6, you may be supposed to switch the branch to `casa6` (I am not sure though).

**Modification required**

Some types use in modules shown above is deprecated.
Please modify like below:

`analysisUtils.py` of analysisUtilities:

- `np.int32`, `np.int64` and `np.long` -> `int`
- `np.float`, `np.float32`, `np.float64`, `float32` and `float64` -> `float`

`uvmultifit.py` of UVMultiFit:

- `np.int32`, `np.int64` -> `int`
- `np.float32`, `np.float64` -> `float`
- `np.bool` -> `bool`

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

Then, you can run the test by

```
$ pytest
```

Or you can examine downloading and analysis tests individually:

```shell
$ python test/script_test_download.py
$ python test/script_test_analysis.py
```
