import sys
BASE_PATH = '/home/jonas/Nextcloud/Programmieren/PyCharm/pykitopen'
sys.path.append(BASE_PATH)

from pykitopen.search import SearchOptions, SearchBatch, SearchResult, YearBatching, Publication
from pykitopen.config import DEFAULT


print('\n\nSEARCH OPTIONS:')
search_options = SearchOptions.from_dict({})
print('from empty dict', search_options)


print('\n\nSEARCH BATCH:')
options = SearchOptions.from_dict({
    'author':       'KOPMANN, A*',
    'start':        '2019'
})
batch = SearchBatch(DEFAULT, options)
# batch.execute()


print('\n\nSEARCH RESULT:')
result = SearchResult(DEFAULT, {
    'author':       'KOPMANN, A*',
    'start':        '2019'
})

# for publication in result:
#     print(publication.data)

print('\n\nYEAR BATCHING:')
config = DEFAULT.copy()
config['batching_strategy'] = YearBatching
result = SearchResult(config, {
    'author':       'KOPMANN, A*',
    'start':        '2018',
})

for publication in result:
    print(publication.data)
