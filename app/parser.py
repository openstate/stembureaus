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
    def _has_correct_sheet_count(self, wb):
        return (wb.nsheets == 3) or (wb.nsheets == 1)

    def _get_headers(self, sh):
        return [x.lower() for x in sh.col_values(0)[1:]]

    def parse(self, path):
        headers = []
        rows = []
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)

        # moet 1 of 3 sheets hebben anders is het niet goed
        if not self._has_correct_sheet_count(wb):
            return [], []

        # TODO: checken of alle tabs er in staan

        # als we 1 tab hebben dan de eerste, anders de tweede
        if wb.nsheets == 1:
            nsh = 0
        else:
            nsh = 1
        sh = wb.sheet_by_index(nsh)

        headers = self._get_headers(sh)

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
