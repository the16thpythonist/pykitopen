import csv
from typing import List
from zipfile import ZipFile
from tempfile import TemporaryFile, TemporaryDirectory


def multi_isinstance(objects: list, types: list):
    for _object, _type in zip(objects, types):
        if not isinstance(_object, _type):
            return False
    return True


def unzip_bytes(content: bytes) -> TemporaryDirectory:
    temp_file = TemporaryFile()
    temp_file.write(content)

    temp_directory = TemporaryDirectory()
    with ZipFile(temp_file, mode='r') as zip_file:
        zip_file.extractall(temp_directory.name)

    return temp_directory


def csv_as_dict_list(path: str) -> List[dict]:
    with open(path, mode='r') as file:
        reader = csv.DictReader(file)

        result = []
        for row in reader:
            result.append(dict(row))

    return result
