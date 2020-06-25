import sys
BASE_PATH = '/home/jonas/Nextcloud/Programmieren/PyCharm/pykitopen'
sys.path.append(BASE_PATH)

from pykitopen.publication import PublicationView, Publication


print('\n\nONLY AUTHOR VIEW:')
author_view = PublicationView('only_author', ['author'])
print(author_view)
print(author_view.fields)


print('\n\nEXTENDING A VIEW')
extended_view = author_view.extend(['title', 'year'])
extended_view.name = 'extended_author_view'
print(extended_view.fields)
print(author_view == extended_view)


print('\n\nPREDEFINED VIEW')
full_view = Publication.VIEWS.FULL
print(full_view)
print(full_view.fields)
