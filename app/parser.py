#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re

from app import app
from pyexcel_ods3 import get_data
from xlrd import open_workbook


valid_headers = [
    'Stembureau of Afgiftepunt',
    'Nummer stembureau of afgiftepunt',
    'Naam stembureau of afgiftepunt',
    'Website locatie',
    'BAG referentie nummer',
    'Extra adresaanduiding',
    'Longitude',
    'Latitude',
    'X',
    'Y',
    'Openingstijden 10-03-2021',
    'Openingstijden 11-03-2021',
    'Openingstijden 12-03-2021',
    'Openingstijden 13-03-2021',
    'Openingstijden 14-03-2021',
    'Openingstijden 15-03-2021',
    'Openingstijden 16-03-2021',
    'Openingstijden 17-03-2021',
    'Mindervaliden toegankelijk',
    'Akoestiek',
    'Auditieve hulpmiddelen',
    'Visuele hulpmiddelen',
    'Mindervalide toilet aanwezig',
    'Tellocatie',
    'Contactgegevens',
    'Beschikbaarheid'
    #'Verkiezingen'
]

parse_as_integer = [
    'nummer_stembureau_of_afgiftepunt'
]

yes_no_empty_fields = [
    'mindervaliden_toegankelijk',
    'akoestiek',
    'mindervalide_toilet_aanwezig',
    'tellocatie'
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
            for yes_no_empty_field in yes_no_empty_fields:
                if yes_no_empty_field in record:
                    if re.match('^[YyJj]$', str(record[yes_no_empty_field])):
                        record[yes_no_empty_field] = 'Y'
                    elif re.match('^[Nn]$', str(record[yes_no_empty_field])):
                        record[yes_no_empty_field] = 'N'

            # Split the Verkiezingen string into a list in order to validate
            # the content. Afterwards in _create_record the list will be
            # changed back to a string again to save in CKAN.
            if record.get('verkiezingen'):
                record['verkiezingen'] = [
                    x.strip() for x in record['verkiezingen'].split(';')
                ]

        return records

    def _clean_bag_referentienummer(self, record):
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

        return record

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
            record = {}
            for idx, row in enumerate(sh[1:len(clean_headers)+1]):
                if row:
                    # No values left
                    if len(row) - 1 < col_num or len(row) <= 5:
                        continue
                    value = row[col_num]
                    try:
                        # Convert all to str except for bag_referentienummer
                        # as this field is interpreted as float by Excel so
                        # first cast it to int and then to str
                        if clean_headers[idx] == 'bag_referentienummer':
                            if type(value) == float or type(value) == int:
                                record[clean_headers[idx]] = str(
                                    int(value)
                                ).strip()
                            else:
                                record[clean_headers[idx]] = value.strip()
                        elif clean_headers[idx] == 'nummer_stembureau_of_afgiftepunt':
                            record[clean_headers[idx]] = value
                        else:
                            record[clean_headers[idx]] = str(value).strip()
                    except IndexError:
                        record[clean_headers[idx]] = ''

            if 'bag_referentienummer' in record:
                record = self._clean_bag_referentienummer(record)
            records.append(record)

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

        return clean_records


class ExcelParser(BaseParser):
    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        headers = []
        all_headers_check = []
        found_valid_headers = False
        for header in sh.col_values(0)[1:]:
            if self._header_valid(header):
                found_valid_headers = True
                all_headers_check.append(header)
            # The mindervaliden checklist field names start with a
            # number, so we prepend those names with a 'v' (from
            # 'veld')
            if re.match('\d', str(header)):
                header = 'v' + str(header)
            # 'Slugify' the field name
            headers.append(
                re.sub(
                    '_+',
                    '_',
                    re.sub(
                        '[/: .,()\-]', '_', str(header).lower()
                    )
                ).rstrip('_').replace('\n', '')
            )
        if not found_valid_headers:
            app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        if sorted(valid_headers) != sorted(all_headers_check):
            app.logger.warning('Spreadsheet bevat niet alle veldnamen')
            raise ValueError()
        return headers

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, sh.ncols):
            record = {}
            for idx, value in enumerate(
                    sh.col_values(col_num)[1:len(clean_headers)+1]):
                # Convert all to str except for bag_referentienummer
                # as this field is interpreted as float by Excel so
                # first cast it to int and then to str
                if clean_headers[idx] == 'bag_referentienummer':
                    if type(value) == float or type(value) == int:
                        record[clean_headers[idx]] = str(
                            int(value)
                        ).strip()
                    else:
                        record[clean_headers[idx]] = value.strip()
                elif clean_headers[idx] in parse_as_integer:
                    record[clean_headers[idx]] = value
                else:
                    record[clean_headers[idx]] = str(value).strip()

            record = self._clean_bag_referentienummer(record)
            records.append(record)

        return records

    def parse(self, path):
        headers = []
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)

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

        return clean_records


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
            records = parser.parse(path)
        return records
