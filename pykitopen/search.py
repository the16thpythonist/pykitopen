import os
import csv
import json
import datetime

from collections import deque
from typing import Tuple, Type, List, Union, Any, Dict

import requests
from tempfile import TemporaryDirectory, TemporaryFile
from zipfile import ZipFile

from pykitopen.publication import Publication, PublicationView, publication_from_row
from pykitopen.util import csv_as_dict_list, unzip_bytes
from pykitopen.mixins import DictTransformationMixin

# INTERFACES AND ABSTRACT CLASSES
# ###############################


class BatchingStrategy:

    def __init__(self, config, options):
        self.options = options
        self.config = config

    def __call__(self):
        raise NotImplementedError()


class SearchOptions:

    _ARGS = ['author', 'start', 'end', 'view']

    _DEFAULT_CONFIG = {
        'default_view':         Publication.VIEWS.BASIC,
        'default_start':        '2000',
        'default_end':          '',
        'default_author':       'MUSTERMANN, M*'
    }

    def __init__(self,
                 author: Union[List[str], str],
                 start: str,
                 end: str,
                 view: PublicationView):
        self.author = author
        self.start = start
        self.end = end
        self.view = view

        self.parameters_builder = SearchParametersBuilder()
        self.parameters_builder.set_options(self.to_dict())

    # PUBLIC METHODS
    # --------------

    def to_parameters(self):
        return self.parameters_builder.get_parameters()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'author':       self.author,
            'start':        self.start,
            'end':          self.end,
            'view':         self.view
        }

    @classmethod
    def from_dict(cls, data: dict, config: dict = _DEFAULT_CONFIG):
        kwargs = {}
        for key in cls._ARGS:
            default_key = f'default_{key}'
            kwargs[key] = data[key] if key in data.keys() else config[default_key]
        return SearchOptions(**kwargs)

    # PROTECTED METHODS
    # -----------------

    # MAGIC METHODS
    # -------------

    def __dict__(self) -> dict:
        return self.to_dict()

    def __str__(self) -> str:
        return 'SearchOptions(author="{}", start="{}", end="{}", view={})'.format(
            self.author,
            self.start,
            self.end,
            self.view
        )


class SearchParametersBuilder(DictTransformationMixin):

    DEFAULT_PARAMETERS: dict = {
        'external_publications':                                'kit',
        'open_access_availability':                             'do_not_care',
        'full_text':                                            'do_not_care',
        'key_figures':                                          'number_of_publications',
        'year':                                                 '2015-',
        'consider_online_advance_publication_date':             'true',
        'consider_additional_pof_structures':                   'false',
        'row':                                                  'type',
        'column':                                               'year',
        'authors':                                              'MUSTERMANN',
        'table_fields':                                         'title',
        'format':                                               'csv',
        'publications':                                         'true'
    }

    dict_transformation: dict = {
        ('author',
         'authors'): {
            str:                        'process_author_str',
            list:                       'process_author_list',
            object:                     'raise_type_error'
        },
        (('start', 'end'),
         'year'): {
            (str, str):                 'process_year_str',
            (object, object):           'raise_type_error'
        },
        ('view', 'table_fields'): {
            PublicationView:            'process_view',
            object:                     'raise_type_error'
        }
        # ('type',
        #  'type'): {
        #     str:                        'process_type_str',
        #     object:                     'raise_type_error'
        # }
    }

    def __init__(self):
        self.options: Union[dict, None] = None
        self.parameters: Union[dict, None] = None

    # PUBLIC METHODS
    # --------------

    def set_options(self, options: dict):
        self.options = options

    def get_parameters(self):
        assert self.options is not None, 'options have to be supplied to build parameters!'

        parameters = self.DEFAULT_PARAMETERS.copy()
        update = self.process(self.options)
        parameters.update(update)

        return parameters

    def process_view(self, key: str, value: PublicationView) -> str:
        return ','.join(value.fields)

    def process_author_str(self, key: str, value: str) -> str:
        return value

    def process_author_list(self, key: str, value: List[str]) -> str:
        return self._join_author_list(value)

    def process_year_str(self, keys: Tuple[str, str], values: Tuple[int, int]) -> str:
        start, end = values

        return f'{start}-{end}'

    def process_type_str(self, key, value):
        return ''

    def raise_type_error(self, key: str, value: Any):
        raise TypeError(f'Key "{key}" is not supposed to be type "{type(value)}"')

    # PROTECTED_METHODS
    # -----------------

    @classmethod
    def _join_author_list(cls, authors: List[str]) -> str:
        return " or ".join(authors)


class SearchBatch:

    PUBLICATIONS_FILE_NAME = 'Publikationen.csv'
    ANALYSIS_FILE_NAME = 'Analyse.csv'

    def __init__(self, config: dict, options: SearchOptions):
        self.config = config
        self.options = options

        self.response = None
        self.success = False

        self.publications: List[Publication] = []
        self.length = 0
        self.index = 0

    # PUBLIC METHODS
    # --------------

    def execute(self):
        self.response = self.send_request()

        if self.response.status_code == 200:
            temp_dir: TemporaryDirectory = unzip_bytes(self.response.content)
            publications_file_path = os.path.join(temp_dir.name, self.PUBLICATIONS_FILE_NAME)
            publications_rows = csv_as_dict_list(publications_file_path)

            self.publications = self._get_publications_from_rows(publications_rows, self.options.view)
            self.length = len(self.publications)
            self.success = True
        else:
            raise ConnectionError()

    def send_request(self) -> requests.Response:
        url = self.config['search_url']
        parameters = self.options.to_parameters()

        return requests.get(
            url=url,
            params=parameters
        )

    # PROTECTED METHODS
    # -----------------

    @classmethod
    def _get_publications_from_rows(cls,
                                    rows: List[Dict[str, Any]],
                                    publication_view: PublicationView) -> List[Publication]:
        publications = []

        for row in rows:
            _publication = Publication(row, publication_view)
            publications.append(_publication)

        return publications

    # MAGIC METHODS
    # -------------

    def __bool__(self):
        return self.success

    def __len__(self) -> int:
        return self.length

    def __iter__(self):
        return self

    def __next__(self) -> Publication:
        publication = self.publications[self.index]
        self.index += 1

        if self.index >= self.length:
            raise StopIteration

        return publication


class SearchResult:

    def __init__(self, config: dict, options: dict):
        self.config = config
        self._options_dict = options
        self.options = SearchOptions.from_dict(options)

        self.batches = self.create_batches()
        self.length = len(self.batches)
        self.index = 0

    # PUBLIC METHODS
    # --------------

    def create_batches(self):
        return self._create_batches(
            self.config,
            self.options
        )

    # PROTECTED METHODS
    # -----------------

    @classmethod
    def _create_batches(cls,
                        config: dict,
                        options: SearchOptions) -> List[SearchBatch]:
        strategy_class = config['batching_strategy']
        strategy = strategy_class(config, options)
        return strategy()

    # MAGIC METHODS
    # -------------

    def __iter__(self):
        return self

    def __next__(self) -> Publication:
        try:
            batch = self.batches[self.index]
            if not bool(batch): batch.execute()
            publication = next(batch)
        except StopIteration:
            self.index += 1

            if self.index >= self.length:
                raise StopIteration

            batch = self.batches[self.index]
            if not bool(batch): batch.execute()
            publication = next(batch)

        return publication


class NoBatching(BatchingStrategy):

    def __init__(self, config: dict, options: SearchOptions):
        super(NoBatching, self).__init__(config, options)

    def __call__(self) -> List[SearchBatch]:
        return [SearchBatch(self.config, self.options)]


class YearBatching(BatchingStrategy):

    def __init__(self, config: dict, options: SearchOptions):
        super(YearBatching, self).__init__(config, options)

        self.now = datetime.datetime.now()
        self.start = int(self.options.start)
        self.end = self.now.year if self.options.end == '' else int(self.options.end)

    def __call__(self) -> List[SearchBatch]:
        batches = []
        for start, end in self.get_year_tuples():
            _dict = self.options.to_dict()
            _dict.update({'start': str(start), 'end': str(end)})
            print(_dict)
            options = SearchOptions.from_dict(_dict)
            batches.append(SearchBatch(self.config, options))

        return batches

    def get_year_tuples(self):
        result = []
        current = range(self.start, self.end)
        following = range(self.start + 1, self.end + 1)

        for start, end in  zip(current, following):
            result.append((start, end))

        return result
