=========
pykitopen
=========


.. image:: https://img.shields.io/pypi/v/pykitopen.svg
        :target: https://pypi.python.org/pypi/pykitopen

.. image:: https://readthedocs.org/projects/pykitopen/badge/?version=latest
        :target: https://pykitopen.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


A python wrapper for the *KITOpen* database!

* Free software: MIT license
* Documentation: https://pykitopen.readthedocs.io.

Getting Started
---------------

Installation
""""""""""""

The package is best installed using pip, as it will also install all the necessary dependencies

.. code:: console

    $ pip install pykitopen

Usage
-----

To query the KITOpen search function, simply create a ``KitOpen`` wrapper object with the desired
configuration and call the ``search`` function with the relevant parameters. The returned ``SearchResults``
object can be iterated for all the publications.

.. code:: python

    from pykitopen import KitOpen, Publication
    from pykitopen.config import DEFAULT

    kitopen = KitOpen(DEFAULT)
    results = kitopen.search({
        'author':       'MUSTERMANN, MAX',
        'start':        '2012',
        'stop':         '2016',
        'view':         Publication.VIEWS.FULL
    })

    for publication in results:
        print(publication.data)


Features
--------

The library is still under development, which is why this first version only provides some basic functionality.
At the moment only a publication search is supported:

* Searching by author and by year

* Customizable publication "views", which define the fields to be included.

Planned
-------

* Support more search parameters such as publication type, open access availability etc.

* Add support for the metrics generation feature of KITOpen.

* Add additional batching strategies

* Add export of the result to different formats such as CSV, JSON...

License
-------

Distributed under the MIT License. See ``LICENSE`` for more information

Contact
-------

Jonas Teufel - jonseb1998@gmail.com

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
