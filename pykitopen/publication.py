from typing import List, Iterable


class PublicationView:

    VALID_FIELDS = {
        'doi',
        'publication_type',
        'year',
        'date_online',
        'isbn',
        'issn',
        'title',
        'author',
        'collaborations',
        'volume',
        'issue',
        'pages',
        'source',
        'series',
        'series_number',
        'publisher',
        'edition',
        'thesis_type',
        'advisor',
        'event',
        'bibliographic_data',
        'id',
        'cn_id',
        'wos_id',
        'scopus_id',
        'pof_structure',
        'additional_pof_structures',
        'in_wos',
        'in_scopus',
        'in_wos_or_scopus',
        'in_doaj',
        'is_referenced',
        'is_otherwise_referenced',
        'remarks_review_process',
        'is_open_access',
        'with_full_text',
        'is_invited',
        'verification_tasks',
        'languages',
        'organization_names',
        'organization_acronyms',
        'institute_specification',
        'psp_elements_gfb',
        'psp_elements_ub',
        'project_acronym',
        'project_funder',
        'project_funding_id',
        'project_framework_program',
        'remarks_publication',
        'kit_tagging',
        'full_text_type',
        'full_text_state',
        'doi_kitopen',
        'license',
        'embargo',
        'citations',
        'citations_wos',
        'citations_scopus',
        'impact_factor',
        'downloads',
        'page_views',
        'ddc',
        'insert_date',
    }

    def __init__(self, name: str, fields: List[str]):
        self.name = name
        self.fields = fields

        self.length = len(self.fields)

        # Check if all the fields are valid fields
        self._validate_fields(self.fields)

    # PUBLIC METHODS
    # --------------

    def to_string(self):
        return self.name

    def extend(self, fields: List[str]):
        return self.__class__(self.name, self.fields + fields)

    # PROTECTED METHODS
    # -----------------

    @classmethod
    def _validate_field(cls, field: str):
        assert field in cls.VALID_FIELDS, f'field {field} not supported for PublicationView'

    # TODO: This could be more efficient. With a set difference for example
    @classmethod
    def _validate_fields(cls, fields: Iterable[str]):
        for field in fields:
            cls._validate_field(field)

    # MAGIC METHODS
    # -------------

    def __len__(self):
        return self.length

    def __str__(self):
        return 'PublicationView(name={}, #fields={})'.format(
            self.name,
            self.length
        )


class Publication:

    # INTERNAL CLASSES
    # ----------------
    # These are mainly being used as an additional namespace for class constants

    class VIEWS:

        FULL = PublicationView('full',
                               list(PublicationView.VALID_FIELDS))
        BASIC = PublicationView('basic', [
            'doi',
            'id',
            'title',
            'author',
            'year',
            'pof_structure',
            'impact_factor',
            'insert_date',
        ])

    def __init__(self, data: dict, view: PublicationView):
        self.data = dict(zip(view.fields, data.values()))
        self.view = view

    # PUBLIC METHODS
    # --------------

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def get_authors(self):
        assert 'author' in self.keys(), '"author" has to be included in the view to get the list of authors!'

        author_string = self['author']
        indexed_names = author_string.split('\n')
        authors = []
        for indexed_name in indexed_names:
            last, first = indexed_name.split(', ')
            author = {'first': first, 'last': last}
            authors.append(author)

        return authors

    # MAGIC METHODS
    # -------------

    def __iter__(self):
        return self.data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __str__(self):
        return 'Publication(view={}, data={})'.format(
            self.view,
            self.data
        )

