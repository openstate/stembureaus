#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

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


class ExcelParser(BaseParser):
    def parse(self, path):
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)

        return [], []


class CSVParser(BaseParser):
    pass
