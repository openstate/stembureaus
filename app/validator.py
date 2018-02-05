#!/usr/bin/env python
# -*- coding: utf-8 -*-


class RecordValidator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, line_no, headers=[], record={}):
        """
        Validates a single record. Gets a line number and a list of headers as
        well as a dict. Returns a list of issues found, which can be empty.
        """
        results = []
        return results


class Validator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, headers=[], records=[]):
        """
        Validates input, which consists of a list of headers with a series of
        records. Returns a tuple consisting of a bool and a list of issues.
        """
        results = []
        record_validator = RecordValidator()
        line_no = 0
        for record in records:
            line_no += 1
            results += record_validator.validate(line_no, headers, record)
        return (len(results) == 0), results
