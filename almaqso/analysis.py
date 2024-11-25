import os
import subprocess


def _run_casa_script(casa: str, cmd: str, cmd_name: str):
    try:
        result = subprocess.run(
            [casa, '--nologger', '--nogui', '-c', cmd],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"STDOUT for {cmd_name}:", result.stdout)
        print(f"STDERR for {cmd_name}:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {cmd}:")
        print(f"Return Code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise


def analysis(tardir: str, mode='calonly', casacmd='casa', skip=True):
    """
    Run the analysis of the QSO data.

    Args:
        tardir (str): Directory containing the `*.asdm.sdm.tar` files.
        mode (str): 'calonly': Step 1-4, 'aftercal': Step 5-8 of analysis, 'all': Step 1-8 of analysis. Default is 'calonly'.
        casacmd (str): CASA command. Default is 'casa'.
        skip (bool): Skip the analysis if the output directory exists. Default is True.
    """
    asdm_files = [file for file in os.listdir(f'{tardir}') if file.endswith('.asdm.sdm.tar')]

    for asdm_file in asdm_files:
        cmd = "sys.path.append('.');" + \
            "from almaqso._analysis import _analysis;" + \
            f"_analysis('{asdm_file}', skip={skip}," + \
            f"casacmd='{casacmd}', mode='{mode}')"
        _run_casa_script(casacmd, cmd, asdm_file)
