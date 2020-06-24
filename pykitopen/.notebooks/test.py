import os
import sys
from pprint import pprint

from pykitopen.search import SearchResult
from pykitopen.config import DEFAULT
from pykitopen.mixins import DictTransformationMixin


class TransformTest(DictTransformationMixin):
    dict_transformation = {
        ('int', 'str'): {
            int: 'get_str',
            object: 'raise_error'
        },
        (('add1', 'add2'), 'sum'): {
            (int, int): 'add',
            object: 'raise_error'
        },
        ('full_name', ('first_name', 'last_name')): {
            str: 'split_name',
            object: 'raise_error'
        }
    }

    def __init__(self):
        self.content = {
            'int': 10,
            'add1': 10,
            'add2': 5,
            'full_name': 'Jonas Teufel'
        }

    def get(self):
        return self.process(self.content)

    def get_str(self, key: str, value: int):
        return str(value)

    def split_name(self, key, value):
        return value.split(' ')

    def add(self, keys, values):
        return sum(values)

    def raise_error(self, *args):
        raise TypeError


transform_test = TransformTest()
pprint(transform_test.get())

pprint(isinstance(None, object))
