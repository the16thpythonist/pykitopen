import os
import csv
import json
from typing import Tuple, Type, List, Union, Any

import requests
from tempfile import TemporaryDirectory, TemporaryFile
from zipfile import ZipFile

from pykitopen.publication import Publication, publication_from_row
from pykitopen.util import csv_as_dict_list, unzip_bytes
from pykitopen.mixins import DictTransformationMixin

# INTERFACES AND ABSTRACT CLASSES
# ###############################
HELLO = 3

class BatchingStrategy:

    def __init__(self, options: dict):
        self.options = options

    def __call__(self, options: dict):
        raise NotImplementedError()


"""
contents of options dict:
author:                 list, str
start:                  int, None
end:                    int, None
type:                   str
"""


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
        'table_fields':                                         'author',
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

    @classmethod
    def _assert_valid_year(cls, year: Any):
        assert (isinstance(year, str)), "year value must be int!"
        assert (1800 <= year <= 2020), "year value must be a valid int between 1800 and 2020"


class SearchBatch:

    PUBLICATIONS_FILE_NAME = 'Publikationen.csv'
    ANALYSIS_FILE_NAME = 'Analyse.csv'

    def __init__(self, config: dict, options: dict):
        self.config = config
        self.options = options

        self.response = None
        self.parameter_builder = SearchParametersBuilder()

        self.publications: List[Publication] = []
        self.length = 0
        self.index = 0

    # PUBLIC METHODS
    # --------------

    def execute(self):
        self.response = self.send_request()
        if self.response.status_code == 200:
            temp_dir: TemporaryDirectory = unzip_bytes(self.response.content)
            publications_file_path: str = os.path.join(temp_dir.name, self.PUBLICATIONS_FILE_NAME)
            publications_rows = csv_as_dict_list(publications_file_path)

            self.publications = self._get_publications_from_rows(publications_rows)#
            self.length = len(self.publications)
        else:
            raise ConnectionError()

    def send_request(self) -> requests.Response:
        url = self.config['search_url']
        parameters = self.get_request_parameters()

        return requests.get(
            url=url,
            params=parameters
        )

    def get_request_parameters(self):
        self.parameter_builder.set_options(self.options)
        return self.parameter_builder.get_parameters()

    # PROTECTED METHODS
    # -----------------

    @classmethod
    def _get_publications_from_rows(cls, rows: List[dict]) -> List[Publication]:
        publications = []

        for row in rows:
            _publication = publication_from_row(row)
            publications.append(_publication)

        return publications

    # MAGIC METHODS
    # -------------

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
        self.options = options

        self.batches = self.create_batches()
        self.length = len(self.batches)
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self) -> Publication:
        try:
            batch = self.batches[self.index]
            publication = next(batch)
        except StopIteration:
            self.index += 1

            if self.index >= self.length:
                raise StopIteration

            batch = self.batches[self.index]
            publication = next(batch)

        return publication

    def create_batches(self):
        return self._create_batches(
            self.config['batching_strategy'],
            self.options
        )

    # CLASS METHODS
    # -------------

    @classmethod
    def _create_batches(cls,
                        strategy_class: Type[BatchingStrategy],
                        options: dict) -> List[SearchBatch]:
        strategy = strategy_class({})
        return strategy(options)


class NoBatching(BatchingStrategy):

    def __init__(self, options: dict):
        super(NoBatching, self).__init__(options)

    def __call__(self, options: dict):
        return SearchBatch(options)
