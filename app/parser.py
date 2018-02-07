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
        headers = []
        rows = []
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)
        # altijd de tweede tab
        # TODO: checken of alle tabs er in staan
        sh = wb.sheet_by_index(1)

        headers = sh.col_values(0)[1:]

        rows = []
        for col_num in range(5, sh.ncols):
            rows.append(dict(zip(headers, sh.col_values(col_num)[1:])))

        return headers, [
            r for r in rows if ''.join([
                str(x).replace('0', '') for x in r.values()
            ]).strip() != '']


class CSVParser(BaseParser):
    pass


class UploadFileParser(BaseParser):
    PARSERS = {
        '.json': JSONParser,
        '.xlsx': ExcelParser
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
