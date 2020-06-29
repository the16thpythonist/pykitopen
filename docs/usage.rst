=====
Usage
=====

Basic Usage
-----------

The most simple use case is to perform a simple search. To do this simply create an instance
of a ``KitOpen`` wrapper object with the desired configuration and then call the ``search``
method on it with the proper parameters.

A simple search can be constructed by passing a string author argument and the start/end years
for the search also as strings.

The resulting ``SearchResult`` object can be iterated to get all the publication objects.

.. code:: python

    from pykitopen import KitOpen, Publication
    from pykitopen.config import DEFAULT

    kitopen = KitOpen(DEFAULT)
    results = kitopen.search({
        'author':           'MUSTERMANN, M*',
        'start':            '2012',
        'end'               '2016',
        'view'              Publication.VIEWS.FULL
    })

    for publication in results:
        print(publication.data)

Publication Views
-----------------

As you might have noticed, there is an additional parameter *'view'*, which can be passed to the search parameters.
This parameter is supposed to be an object of the type ``PublicationView``. This parameter influences, what kind of
data fields are requested for each publication in the search.

Some standard options are available as constant members of the ``Publication.VIEWS`` class. This included for example
the ``FULL`` view, which will request *all* of the fields and the ``BASIC`` view which will only contain the most basic
information such as ID, author, title etc. Choosing the appropriate view might help to reduce response times.

Custom Views
""""""""""""

The user is not limited to the predefined views though, it is also possible to define custom views with only the
required fields. First of all, a list of all the available fields can be displayed like this:

.. code:: python

    from pykitopen.publication import PublicationView

    print(PublicationView.FIELDS)

A custom view can be created, by simply creating a new instance of the ``PublicationView`` class. A string name and a
subset of the fields list have to be passed to the constructor. This object can then be used to be passed as a search
parameter or even set as a default in the configuration dict.

.. code:: python

    from pykitopen import KitOpen
    from pykitopen.config import DEFAULT
    from pykitopen.publication import PublicationView

    # Set it as a default
    custom_view = PublicationView('MyCustomView', ['author', 'title'])

    config = DEFAULT.copy()
    config['default_view'] = custom_view

    kitopen = KitOpen(config)

    # Or use it for a search request directly
    kitopen.search({
        'author':       'MUSTERMANN, M*,
        'view':         custom_view
    })

Request Batching
----------------

The problem
"""""""""""

So the problem is, that the used KITOpen interface at `KITOpen Auswertungen <https://publikationen.bibliothek.kit.edu/auswertungen/>`_
does not expose a REST API. The only way to export the more detailed information data is through the download of a ZIP
file, which then in turn contains a CSV file.

So the way *pykitopen* works in the background is: It downloads the zip file, unpacks it into a temporary folder and
parses the csv for the actual data.

This creates a practical complication: If the amount of requested data is high, the server takes a long time to create
corresponding csv and zip files, which then leads to a timeout for the request...

Batching Strategies
"""""""""""""""""""

To work around this problem, it is possible to get the desired data in batches, instead of everything at once. A single
request will be split into multiple different requests based on some criteria. This behaviour can be controlled with
the ``"batching_strategy"`` key the configuration dict, which is being passed to the ``KitOpen`` wrapper object. The
default behaviour being the ``NoBatching`` strategy, which will request all the data at once.

A good alternative would be the ``YearBatching`` strategy, which will request the data for every year
individually.

.. code:: python

    from pykitopen import KitOpen
    from pykitopen.search import YearBatching
    from pykitopen.config import DEFAULT

    # It is good practice to base a custom configuration on a copy of the default
    config = DEFAULT.copy()
    config['batching_strategy'] = YearBatching

    pykitopen = KitOpen(config)

Changing the batching strategy does not change anything on the behaviour of ``SearchResult``,
since the batching is implemented in the background. Each batch is executed, once the iterator reaches the
corresponding point.

