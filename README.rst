=========
pykitopen
=========


.. image:: https://img.shields.io/pypi/v/pykitopen.svg
        :target: https://pypi.python.org/pypi/pykitopen

.. image:: https://img.shields.io/travis/the16thpythonist/pykitopen.svg
        :target: https://travis-ci.com/the16thpythonist/pykitopen

.. image:: https://readthedocs.org/projects/pykitopen/badge/?version=latest
        :target: https://pykitopen.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


A python wrapper for the *KITOpen* database!

* Free software: MIT license
* Documentation: https://pykitopen.readthedocs.io.

Usage
-----

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

* Searching publications

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
