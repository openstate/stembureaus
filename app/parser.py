#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re

from pyexcel_ods3 import get_data
from xlrd import open_workbook


class BaseParser(object):
    def __init__(self, *args, **kwargs):
        pass

    # Rename columnnames which use different spellings
    def _clean_headers(self, headers):
        for idx, header in enumerate(headers):
            if header == 'bag_referentie_nummer':
                headers[idx] = 'bag_referentienummer'

        return headers

    def _clean_records(self, records):
        # Convert variations of 'Y' and 'N' to 'Y' and 'N'
        for record in records:
            yes_no_empty_fields = [
                'mindervaliden_toegankelijk',
                'invalidenparkeerplaatsen',
                'akoestiek',
                'mindervalide_toilet_aanwezig'
            ]

            for yes_no_empty_field in yes_no_empty_fields:
                if re.match('^[YyJj]$', str(record[yes_no_empty_field])):
                    record[yes_no_empty_field] = 'Y'
                if re.match('^[Nn]$', str(record[yes_no_empty_field])):
                    record[yes_no_empty_field] = 'N'

        return records

    def parse(self, path):
        """
        Parses a file (Assumes). Returns a tuple of a list of headers and
        a list of records.
        """
        raise NotImplementedError


class ODSParser(BaseParser):
    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        return [x[0].lower().replace(' ', '_') for x in sh[1:] if x]

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, len(sh[0])):
            values = []
            for row in sh[1:]:
                if row:
                    try:
                        values.append(row[col_num])
                    except IndexError:
                        values.append('')
            records.append(dict(zip(clean_headers, values)))

        return records

    def parse(self, path):
        headers = []
        if not os.path.exists(path):
            return [], []

        wb = get_data(path)
        sh = wb['Attributen']

        headers = self._get_headers(sh)
        clean_headers = self._clean_headers(headers)

        records = self._get_records(sh, clean_headers)
        clean_records = self._clean_records(records)

        return clean_headers, clean_records


class ExcelParser(BaseParser):
    def _has_correct_sheet_count(self, wb):
        return (wb.nsheets == 3) or (wb.nsheets == 1)

    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        return [x.lower().replace(' ', '_') for x in sh.col_values(0)[1:]]

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, sh.ncols):
            records.append(dict(zip(clean_headers, sh.col_values(col_num)[1:])))

        return records

    def parse(self, path):
        headers = []
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
        clean_headers = self._clean_headers(headers)

        records = self._get_records(sh, clean_headers)
        clean_records = self._clean_records(records)

        return clean_headers, clean_records


class UploadFileParser(BaseParser):
    PARSERS = {
        '.ods': ODSParser,
        '.xlsx': ExcelParser,
        '.xls': ExcelParser
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
