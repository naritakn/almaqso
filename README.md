# almaqso

This repository is a folk of [astroysmr/almaqso](https://github.com/astroysmr/almaqso), which is no longer maintained.

## For client

- I am now currently testing this repository with `CASA version 6.6.1-17-pipeline-2024.1.0.8`.
- I am using the latest version of `Python`. Maybe any version newer than `3.8` is fine.
- You may need to modify the `analysisUtilities.py` provided by NRAO. Details are described [here](https://github.com/skrbcr/almaqso/issues/2).
- To follow other bugs or information, please refer the [issues](https://github.com/skrbcr/almaqso/issues).

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

Or you examine run downloading and analysis test individually:

```shell
$ python test/script_test_download.py
$ python test/script_test_analysis.py
```
