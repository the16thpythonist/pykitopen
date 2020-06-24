from pprint import pprint

import pykitopen.search as search
import pykitopen.config as config
import pykitopen.mixins as mixins

options = {
    'author':           'KOPMANN, A*',
    'start':            '2019',
    'end':              '',
    'type':             ''
}
builder = search.SearchParametersBuilder()
builder.set_options(options)
parameters = builder.get_parameters()

pprint(parameters)

#%%

batch = search.SearchBatch(config.DEFAULT, options)
batch.execute()

for publication in batch:
    print(publication)
