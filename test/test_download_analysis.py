import os
import subprocess
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CASA_PATH = os.environ.get('ALMAQSO_CASA', 'casa')


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
    subprocess.run(
        [
            'python',
            f'{CURRENT_DIR}/script_test_download.py'
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    run_casa_script(f'{CURRENT_DIR}/script_test_analysis.py')
