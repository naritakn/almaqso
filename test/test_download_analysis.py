import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CASA_PATH = '/usr/local/casa/casa-6.6.1-17-pipeline-2024.1.0.8-py3.8.el8/bin/casa'

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

def test_download_analysis():
    run_casa_script(f'{CURRENT_DIR}/script_test_download.py')
    run_casa_script(f'{CURRENT_DIR}/script_test_analysis.py')
