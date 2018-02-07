#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from xlrd import open_workbook


class BaseParser(object):
    def __init__(self, *args, **kwargs):
        pass

    def parse(self, path):
        """
        Parses a file (Assumes). Returns a tuple of a list of headers and
        a list of records.
        """
        raise NotImplementedError


class JSONParser(BaseParser):
    def parse(self, path):
        headers = []
        records = []
        if not os.path.exists(path):
            return [], []

        with open(path) as in_file:
            records = json.load(in_file)

        return headers, records


class ExcelParser(BaseParser):
    def parse(self, path):
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)

        return [], []


class CSVParser(BaseParser):
    pass


class UploadFileParser(BaseParser):
    PARSERS = {
        '.json': JSONParser
    }

    def parse(self, path):
        headers = []
        records = []
        if not os.path.exists(path):
            return [], []
        _, extension = os.path.splitext(path)
        if extension in self.PARSERS.keys():
            klass = self.PARSERS[extension]
            parser = klass()
            headers, records = parser.parse(path)
        return headers, records
