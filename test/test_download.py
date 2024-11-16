import sys
sys.path.append('../almaqso')
from almaqso.search_archive import search_archive

if __name__ == '__main__':
    search_archive(4, 'catalog/test.json')
