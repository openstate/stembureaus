#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re

from flask import current_app

import pyexcel


valid_headers = [
    'Nummer stembureau',
    'Naam stembureau',
    'Type stembureau',
    'Website locatie',
    'BAG Nummeraanduiding ID',
    'Extra adresaanduiding',
    'Latitude',
    'Longitude',
    'X',
    'Y',
    'Openingstijd',
    'Sluitingstijd',
    'Toegankelijk voor mensen met een lichamelijke beperking',
    'Toegankelijke ov-halte',
    'Toilet',
    'Host',
    'Geleidelijnen',
    'Stemmal met audio-ondersteuning',
    'Kandidatenlijst in braille',
    'Kandidatenlijst met grote letters',
    'Gebarentolk (NGT)',
    'Gebarentalig stembureaulid (NGT)',
    'Akoestiek geschikt voor slechthorenden',
    'Prikkelarm',
    'Prokkelduo',
    'Extra toegankelijkheidsinformatie',
    'Overige informatie',
    'Tellocatie',
    'Contactgegevens gemeente',
    'Verkiezingswebsite gemeente'
]

# If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
# to valid_headers
if [x for x in current_app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
    valid_headers += ['Verkiezingen']

parse_as_integer = [
    'nummer_stembureau'
]

# Fields that have options (fixed input; so no free text). Most fields just
# have ja/nee/'' as options, some fields have other options
option_fields = [
    'type_stembureau', # contains other options than just ja/nee/''
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking',
    'toegankelijke_ov_halte',
    'toilet', # contains other options than just ja/nee/''
    'host',
    'geleidelijnen', # contains other options than just ja/nee/''
    'stemmal_met_audio_ondersteuning',
    'kandidatenlijst_in_braille',
    'kandidatenlijst_met_grote_letters',
    'gebarentolk_ngt', # contains other options than just ja/nee/''
    'gebarentalig_stembureaulid_ngt',
    'akoestiek_geschikt_voor_slechthorenden',
    'prikkelarm',
    'prokkelduo',
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

    def _clean_records(self, records):
        for record in records:
            # For each option field, lowercase the value and convert
            # variations of 'ja' and 'nee' to exactly 'ja' and 'nee'
            for option_field in option_fields:
                if option_field in record:
                    lowercased_record = str(record[option_field]).lower()
                    if re.match('^[yj]a?$', lowercased_record):
                        record[option_field] = 'ja'
                    elif re.match('^[n]e?e?$', lowercased_record):
                        record[option_field] = 'nee'
                    else:
                        record[option_field] = lowercased_record

            # Split the Verkiezingen string into a list in order to validate
            # the content. Afterwards in create_record the list will be
            # changed back to a string again to save in CKAN.
            if record.get('verkiezingen'):
                record['verkiezingen'] = [
                    x.strip() for x in record['verkiezingen'].split(';')
                ]

        return records

    def _clean_bag_nummeraanduiding_id(self, record):
        # Left pad this field with max 3 zeroes
        if len(record['bag_nummeraanduiding_id']) == 15:
            record['bag_nummeraanduiding_id'] = '0' + record[
                'bag_nummeraanduiding_id'
            ]
        if len(record['bag_nummeraanduiding_id']) == 14:
            record['bag_nummeraanduiding_id'] = '00' + record[
                'bag_nummeraanduiding_id'
            ]
        if len(record['bag_nummeraanduiding_id']) == 13:
            record['bag_nummeraanduiding_id'] = '000' + record[
                'bag_nummeraanduiding_id'
            ]

        return record

    def parse(self, path):
        """
        Parses a file (Assumes). Returns a tuple of a list of headers and
        a list of records.
        """
        raise NotImplementedError


# There used to be a separate ODSParser and ExcelParser. After upgrading from xlrd to pyexcel all
# files can be parsed using ExcelParser.
class ExcelParser(BaseParser):
    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        headers = []
        all_headers_check = []
        found_valid_headers = False
        for header in sh[1:]:
            name = header[0]
            if self._header_valid(name):
                found_valid_headers = True
                all_headers_check.append(name)
                # 'Slugify' the field name
                headers.append(
                    re.sub(
                        '_+',
                        '_',
                        re.sub(
                            r'[/: .,()\-]', '_', str(name).lower()
                        )
                    ).rstrip('_').replace('\n', '')
                )
        if not found_valid_headers:
            current_app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        if sorted(valid_headers) != sorted(all_headers_check):
            current_app.logger.warning(f'Spreadsheet bevat niet alle veldnamen; dit zijn de afwijkende veldnamen: {set(valid_headers) - set(all_headers_check)}')
            raise ValueError()
        return headers

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, len(sh[0])):
            record = {}
            for idx, row in enumerate(sh[1:len(clean_headers)+1]):
                try:
                    value = row[col_num]
                    # Convert all to str except for bag_nummeraanduiding_id
                    # as this field is interpreted as float by Excel so
                    # first cast it to int and then to str
                    if clean_headers[idx] == 'bag_nummeraanduiding_id':
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
                except IndexError:
                    record[clean_headers[idx]] = ''

            if 'bag_nummeraanduiding_id' in record:
                record = self._clean_bag_nummeraanduiding_id(record)
            records.append(record)

        return records

    def parse(self, path):
        headers = []
        if not os.path.exists(path):
            return [], []

        wb = pyexcel.get_book(file_name=path)
        n_sheets = wb.number_of_sheets()

        # als we 1 tab hebben dan de eerste, anders de tweede
        if n_sheets == 1:
            sheet_index = 0
        else:
            sheet_index = 1
        sh = wb.sheet_by_index(sheet_index).array

        headers = self._get_headers(sh)

        records = self._get_records(sh, headers)
        clean_records = self._clean_records(records)

        return clean_records


class UploadFileParser(BaseParser):
    PARSERS = {
        '.ods': ExcelParser,
        '.xlsx': ExcelParser,
        '.xls': ExcelParser
    }

    def parse(self, path):
        self._set_parser(path)
        if not self.parser:
            return

        return self.parser.parse(path)

    def _set_parser(self, path):
        self.parser = None

        if not os.path.exists(path):
            return
        
        _, extension = os.path.splitext(path)
        if extension in self.PARSERS.keys():
            klass = self.PARSERS[extension]
            self.parser = klass()
