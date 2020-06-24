import os

from pykitopen.search import (BatchingStrategy,
                              NoBatching)

# CONSTANTS
# ---------

KITOPEN_BASE_URL = 'https://publikationen.bibliothek.kit.edu'
KITOPEN_EVALUATION_URL = os.path.join(KITOPEN_BASE_URL, 'auswertungen')
KITOPEN_SEARCH_URL = os.path.join(KITOPEN_EVALUATION_URL, 'report.php')


# DEFAULT CONFIG DICT
# -------------------

DEFAULT = {
    'batching_strategy':                NoBatching,
    'url':                              KITOPEN_BASE_URL,
    'search_url':                       KITOPEN_SEARCH_URL
}
