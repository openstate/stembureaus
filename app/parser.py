#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re

from app import app
from pyexcel_ods3 import get_data
from xlrd import open_workbook


valid_headers = [
    'Nummer stembureau',
    'Naam stembureau',
    'Website locatie',
    'BAG referentie nummer',
    'Extra adresaanduiding',
    'Longitude',
    'Latitude',
    'Districtcode',
    'Openingstijden',
    'Mindervaliden toegankelijk',
    'Invalidenparkeerplaatsen',
    'Akoestiek',
    'Mindervalide toilet aanwezig',
    'Contactgegevens',
    'Beschikbaarheid'
]


class BaseParser(object):
    def __init__(self, *args, **kwargs):
        pass

    def _header_valid(self, header):
        if isinstance(header, str):
            if header in valid_headers:
                return True
            else:
                return False
        else:
            return False

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
        headers = []
        found_valid_headers = False
        for header in sh[1:]:
            if header:
                if self._header_valid(header[0]):
                    found_valid_headers = True
                headers.append(str(header[0]).lower().replace(' ', '_'))
        if not found_valid_headers:
            app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        return headers

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
        headers = []
        found_valid_headers = False
        for header in sh.col_values(0)[1:]:
            if self._header_valid(header):
                found_valid_headers = True
            headers.append(str(header).lower().replace(' ', '_'))
        if not found_valid_headers:
            app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        return headers

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, sh.ncols):
            record = dict(zip(clean_headers, sh.col_values(col_num)[1:]))

            # Some spreadsheets fill in this field as float, so convert
            #it via int back to str
            if type(record['bag_referentienummer']) == float:
                record['bag_referentienummer'] = str(
                    int(record['bag_referentienummer'])
                )

            # Left pad this field with max 3 zeroes
            if len(record['bag_referentienummer']) == 15:
                record['bag_referentienummer'] = '0' + record[
                    'bag_referentienummer'
                ]
            if len(record['bag_referentienummer']) == 14:
                record['bag_referentienummer'] = '00' + record[
                    'bag_referentienummer'
                ]
            if len(record['bag_referentienummer']) == 13:
                record['bag_referentienummer'] = '000' + record[
                    'bag_referentienummer'
                ]

            records.append(record)

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
