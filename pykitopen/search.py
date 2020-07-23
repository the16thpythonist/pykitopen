"""
The module, which contains all the classes which are directly concerned with the search action.

This includes the classes SearchResult, SearchBatch, SearchOptions and the batching strategies
"""
import os
import csv
import json
import datetime

from collections import deque
from typing import Tuple, Type, List, Union, Any, Dict

import requests
from tempfile import TemporaryDirectory, TemporaryFile
from zipfile import ZipFile

from pykitopen.publication import Publication, PublicationView
from pykitopen.util import csv_as_dict_list, unzip_bytes
from pykitopen.mixins import DictTransformationMixin

# INTERFACES AND ABSTRACT CLASSES
# ###############################


class BatchingStrategy:
    """
    This is the interface for request batching strategy. A BatchingStrategy object acts as a function, by having to
    implement the __call__ method. This call method has to return a list of SearchBatch objects. A batching strategy
    is constructed by passing the config dict of the overall configuration for the KitOpen wrapper as well as the
    options dict, which defines the parameters for a single search action.

    Background
    ----------
    So what is a batching strategy even doing in the broader context of the whole package and why is it important?
    For the requests to the KITOpen database it is important, that there is a functionality, which breaks down request
    for large amounts of data into smaller individual request, because for large requests there is the chance that the
    server will take way to long thus running the request into a timeout.

    So the search batching strategies are classes, which essentially represent different methods of dividing a big
    request into smaller requests.
    """

    def __init__(self, config, options):
        self.options = options
        self.config = config

    def __call__(self):
        """
        Returns a list of SearchBatch objects, which have been created according to the described strategy from the
        basic "options" dict passed to this object

        :return: List[SearchBatch]
        """
        raise NotImplementedError()


class SearchOptions:
    """
    This class represents the parameters which are passed to the `search` action of the `KitOpen` wrapper.

    The `search` method itself expects a dict to be passed to it to define the options for the search, but this dict
    is then converted internally to a `SearchOptions` object, as it wraps some important functionality to be executed
    on these options.
    """

    # CLASS CONSTANTS
    # ---------------

    _ARGS = ['author', 'start', 'end', 'view']
    """A list of the string keys, which are possible to pass as options"""

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
        """
        The constructor.

        Design Choice
        -------------
        I have made the design choice to make the constructor of this object expect every possible search option as a
        positional argument explicitly, instead of having the constructor accept the dict. The primary way to create
        this object will still be using the "from_dict" class method, which does exactly as it sounds, but by defining
        the arguments explicitly, it is more concise and obvious right away what the search options actually includes.

        :param author:
        :param start:
        :param end:
        :param view:
        """
        self.author = author
        self.start = start
        self.end = end
        self.view = view

        # The SearchParametersBuilder is the object which manages the construction of the dict, which will then be
        # used as the GET parameters for the actual network request from the simplified options passed to the search
        # method of the wrapper.
        self.parameters_builder = SearchParametersBuilder()
        self.parameters_builder.set_options(self.to_dict())

    # PUBLIC METHODS
    # --------------

    def to_parameters(self) -> Dict[str, Any]:
        """
        Returns the dict, which is used as the GET parameters for the actual network request to the database

        :return:
        """
        return self.parameters_builder.get_parameters()

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns the search options as a dict

        :return:
        """
        return {
            'author':       self.author,
            'start':        self.start,
            'end':          self.end,
            'view':         self.view
        }

    @classmethod
    def from_dict(cls, data: dict, config: dict = _DEFAULT_CONFIG):
        """
        Creates a new `SearchOptions` object from the given data dict and an optional config.

        The config is also part of creating the dict, because it has to be possible to also supply an options dict to
        the `search` method which only contains a subset of all possible options. All the missing options are then
        substituted by their default values. And those default values can be customized within the config...

        :param data:
        :param config:
        :return:
        """
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
    """
    The SearchBatch class represents one of the parts of a search request to the KITOpen database. The SearchBatch
    objects are the actual lowest layer of abstraction, which actually execute the network request to the database and
    handle the processing of the response.

    Processing the response
    -----------------------

    The response, which is returned by the KITOpen database is a little bit different than the usual REST API. KITOpen
    has chosen to only export the detailed publication data in the form of a ZIP file, which in turn contains a CSV,
    which actually contains the data. Thus the reponse has to be processed by first unpacking the downloaded ZIP file
    into a temp folder and then parsing the CSV for the data.

    Iterator
    --------
    The SearchBatch class implements the magic methods to act as an iterator, which will simply return all the
    `Publication` objects, which have been processed from the response of the request

    .. code:: python

        batch = SearchBatch(config, options)
        batch.execute()
        for publication in batch:
            print(publication)

    """

    # CLASS CONSTANTS
    # ---------------

    # These constants define the names of the files, which are contained within the zip file, which is returned as a
    # response of the KITOpen server. These file names are always the same and have to be known to read the files for
    # the data they contain

    PUBLICATIONS_FILE_NAME = 'Publikationen.csv'
    ANALYSIS_FILE_NAME = 'Analyse.csv'

    def __init__(self, config: dict, options: SearchOptions):
        self.config = config
        self.options = options

        self.response = None
        self.success = False

        # Setting up the helper variables for the iterator functionality. A list, which will actually hold all the
        # publications, the total length of that list and the current index of the iteration.
        self.publications: List[Publication] = []
        self.length = 0
        self.index = 0

    # PUBLIC METHODS
    # --------------

    def execute(self):
        """
        Actually executes the search batch, by sending the request to the server and processing the response

        :raises ConnectionError: In case anything with the request went wrong

        :return:
        """
        self.response = self.send_request()

        if self.response.status_code == 200:
            # The 'unzip_bytes' function takes the binary string, which represents a ZIP file unzips the content of
            # this file into a TemporaryDictionary and then returns the object, which describes this temp folder
            temp_dir: TemporaryDirectory = unzip_bytes(self.response.content)

            # The function "csv_as_dict_list" does exactly how it sounds it takes the path of a csv file and returns
            # a list of dicts, where each dict represents a single row in the csv file, the keys being the headers
            # of the scv rows.
            publications_file_path = os.path.join(temp_dir.name, self.PUBLICATIONS_FILE_NAME)
            publications_rows = csv_as_dict_list(publications_file_path)

            self.publications = self._get_publications_from_rows(publications_rows, self.options.view)

            self.length = len(self.publications)
            self.success = True
        else:
            raise ConnectionError()

    def send_request(self) -> requests.Response:
        """
        This method actually sends the request to the KITOpen server and returns the response.

        :return: requests.Response
        """
        # The url of the KITOpen server is defined as part of the overall config dict
        url = self.config['search_url']

        # The parameters for the GET request to the server are directly derived from the options dict passed to the
        # search action. The ".to_parameter" method performs this conversion.
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
        """
        Given a list of dicts, where each dict describes a publication and the PublicationView object, which was used
        to retrieve these publications, this method will return a list of Publication objects, which contain the data
        from the dicts and the keys according to the given view.

        :param rows:
        :param publication_view:
        :return:
        """
        publications = []

        for row in rows:
            _publication = Publication(row, publication_view)
            publications.append(_publication)

        return publications

    # MAGIC METHODS
    # -------------

    def __bool__(self):
        """
        The boolean state of this object evaluates to whether or not the request was successful

        :return:
        """
        return self.success

    def __len__(self) -> int:
        return self.length

    def __iter__(self):
        return self

    def __next__(self) -> Publication:
        """
        This method implements the functionality of being able to iterate a SearchBatch object.

        For each call to the next function this will simply go through the internal list of publications.

        :raises AssertionError: If the request to the server was not successful

        :return:
        """
        assert self.response is not None, "The batch has to be executed first, before it can be iterated"
        assert self.success, "The search request has to be successful to be iterated"

        publication = self.publications[self.index]
        self.index += 1

        if self.index >= self.length:
            raise StopIteration

        return publication


class SearchResult:
    """
    This class represents the result of a search action. A `SearchResult` object is in fact returned for every call to
    the `search` method of the `KitOpen` wrapper.

    Iterator
    --------
    The `SearchResult` class implements the necessary methods to act as an iterator, which returns all the publications
    that have been returned by the class.

    .. code:: python

        from pykitopen import KitOpen
        from pykitopen.config import DEFAULT

        pykitopen = KitOpen(DEFAULT)
        results: SearchResult = pykitopen.search()

        for publication in results:
            print(publication)
    """
    def __init__(self, config: dict, options: dict):
        self.config = config

        # The options are passed to the search function in the form of a dict, but for further processing down the
        # search pipeline it is converted to a SearchOptions object, which wraps some important functionality to be
        # performed on these options
        self._options_dict = options
        self.options = SearchOptions.from_dict(options)

        # The batch objects are the actual instances, which ultimately perform the network request to the server and
        # also the processing of the response
        self.batches: List[SearchBatch] = self.create_batches()
        self.length = len(self.batches)
        self.index = 0

    # PUBLIC METHODS
    # --------------

    def create_batches(self) -> List[SearchBatch]:
        """
        Returns a list of SearchBatch objects, which have been created according to the config.

        :return:
        """
        # The '_create_batches' is a class method which creates the list of SearchBatch objects according to the
        # BatchingStrategy defined in the config.
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
        """
        Returns a list of SearchBatch objects, which have been created from the passed search options and the
        BatchingStrategy defined in the config dict.

        :return:
        """
        # The 'batching_strategy' field of the config is supposed to contain a class(!) which implements the
        # BatchingStrategy interface. Objects of this type accept the config and the options as contruction arguments
        # and can be called directly. This call will return a list of SearchBatch objects, which have been created
        # from the overall options according to some criterion.
        strategy_class = config['batching_strategy']
        strategy = strategy_class(config, options)
        return strategy()

    # MAGIC METHODS
    # -------------

    def __iter__(self):
        return self

    def __next__(self) -> Publication:
        """
        Returns the next `Publication` object in the list of results from the request, when calling the next() function
        on the object

        Implementation
        --------------
        So the `SearchResult` class is actually not concerned with the actual network request to the database server.
        It does not contain the list of publications itself. The actual requests are managed by the `SearchBatch`
        objects. This class only manages a list of all these search batches.

        So the implementation of the iterator works by executing the next search batch at the time, at which it is
        needed and then for each next() call to the `SearchResult` object itself a next call to the current search
        batch will return the actual publication, which is then also returned by this method. If the current batch
        runs out of publications the next one is executed and then set as the current one etc...

        :return:
        """
        try:
            batch = self.batches[self.index]
            if not bool(batch):
                batch.execute()
            publication = next(batch)
        except StopIteration:
            self.index += 1

            if self.index >= self.length:
                raise StopIteration

            batch = self.batches[self.index]
            if not bool(batch):
                batch.execute()
            publication = next(batch)

        return publication


# DIFFERENT BATCHING STRATEGIES
# #############################


class NoBatching(BatchingStrategy):
    """
    Implements the `BatchingStrategy` interface.

    This class defines the most simple batching strategy, which is no batching at all. This strategy will not divide
    the request at all, it will simply take the search options and create a single SearchBatch object from it.
    """
    def __init__(self, config: dict, options: SearchOptions):
        super(NoBatching, self).__init__(config, options)

    def __call__(self) -> List[SearchBatch]:
        """
        Will return a list with a single SearchBatch element, which represents the entire search request.

        :return:
        """
        return [SearchBatch(self.config, self.options)]


class YearBatching(BatchingStrategy):
    """
    Implements the `BatchingStrategy` Interface

    This class defines a batching strategy, which will divide the search options by the individual years, which are
    included in the search. A SearchBatch will be created for each year within the given time span.
    """
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
