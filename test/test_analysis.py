import sys
sys.path.append('../almaqso')
from almaqso.search_archive import search_archive

def test_analysis():
    os.system('casa --nologger --nogui -c script_test_analysis.py')
