#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser


class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.parser = BaseParser()

    def test_parse(self):
        with self.assertRaises(NotImplementedError):
            self.parser.parse('/dev/null')


class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.parser = ExcelParser()
        self.file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data/juinen.xlsx')

    def test_has_correct_num_sheets(self):
        wb = open_workbook(self.file_path)
        self.assertTrue(self.parser._has_correct_sheet_count(wb))

    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        self.assertListEqual(headers, [
            'nummer stembureau',
            'naam stembureau',
            'gebruikersdoel het gebouw',
            'website locatie',
            'bag referentie nummer',
            'extra adresaanduiding',
            'longitude',
            'latitude',
            'districtcode',
            'openingstijden',
            'mindervaliden toegankelijk',
            'invalidenparkeerplaatsen',
            'akoestiek',
            'mindervalide toilet aanwezig',
            'kieskring id',
            'hoofdstembureau',
            'contactgegevens',
            'beschikbaarheid'])
