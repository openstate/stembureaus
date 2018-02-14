#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug.datastructures import MultiDict

from app.forms import EditForm
import app


class RecordValidator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, line_no, headers=[], record={}):
        """
        Validates a single record. Gets a line number and a list of headers as
        well as a dict. Returns a list of issues found, which can be empty.
        """
        old_val = app.app.config.get('WTF_CSRF_ENABLED', True)
        app.app.config['WTF_CSRF_ENABLED'] = False
        form = EditForm(MultiDict(record))
        result = form.validate()
        errors = form.errors
        app.app.config['WTF_CSRF_ENABLED'] = old_val
        return result, errors


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
            validated, errors = record_validator.validate(
                line_no, headers, record)
            if not validated:
                results += [errors]
        return (len(results) == 0), results