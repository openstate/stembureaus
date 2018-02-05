#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
    pass


class CSVParser(BaseParser):
    pass
