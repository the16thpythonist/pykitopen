import logging
from typing import Any, Iterable, Tuple, Callable


from pykitopen.util import multi_isinstance


class DictTransformationMixin:

    # PROTECTED METHODS
    # -----------------

    def process(self, content: dict):
        result = {}
        for key_tuple, transformations in self.dict_transformation.items():
            key_original, key_transformed = key_tuple

            if isinstance(key_original, tuple):
                _method_name = '_process_many_to_one'

            elif isinstance(key_transformed, tuple):
                _method_name = '_process_one_to_many'

            else:
                _method_name = '_process_one_to_one'

            _method = getattr(self, _method_name)
            _update = _method(content, key_original, key_transformed, transformations)
            result.update(_update)

        return result

    # PROTECTED METHODS
    # -----------------

    def _process_one_to_one(self,
                            content: dict,
                            original_key: Any,
                            transformed_key: Any,
                            transformations: dict) -> dict:
        self._check_keys(content, [original_key])

        result = {}
        value = content[original_key]
        for t, method_name in transformations.items():
            if isinstance(value, t):
                method = getattr(self, method_name)
                result[transformed_key] = method(original_key, value)
                break
        else:
            self._type_error(original_key, value, transformations.keys())

        return result

    def _process_one_to_many(self,
                             content: dict,
                             original_key: Any,
                             transformed_keys: Tuple[Any],
                             transformations: dict) -> dict:
        self._check_keys(content, [original_key])

        result = {}
        value = content[original_key]
        for t, method_name in transformations.items():
            if isinstance(value, t):
                _method = self._get_object_method(self, method_name)
                _list = _method(original_key, value)
                assert len(_list) == len(transformed_keys), \
                    'The length of returned values has to be equal to given keys'

                for key, value in zip(transformed_keys, _list):
                    result[key] = value

                break
        else:
            self._type_error(original_key, value, transformations.keys())

        return result

    def _process_many_to_one(self,
                             content: dict,
                             original_keys: Tuple[Any],
                             transformed_key: Any,
                             transformations: dict) -> dict:
        self._check_keys(content, original_keys)

        result = {}
        values = [content[key] for key in original_keys]
        for ts, method_name in transformations.items():
            if multi_isinstance(values, ts):
                method = getattr(self, method_name)
                result[transformed_key] = method(original_keys, values)
                break
        else:
            self._type_error(original_keys, values, transformations.keys())

        return result

    @classmethod
    def _type_error(cls, keys, values, valid_types):
        message = 'The key(s) {} cannot have the value(s) {}! Supported types for a transformation are {}'.format(
            str(keys),
            str(values),
            str(valid_types)
        )
        raise TypeError(message)

    @staticmethod
    def _get_object_method(obj: object, method_name: str) -> Callable:
        assert hasattr(obj, method_name), f'The method "{method_name}" has to actually be implemented in {type(obj)}'
        return getattr(obj, method_name)

    @staticmethod
    def _check_keys(content: dict, keys: Iterable):
        for key in keys:
            if key not in content.keys():
                raise KeyError
