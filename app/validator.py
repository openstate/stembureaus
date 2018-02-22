#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug.datastructures import MultiDict

from app.forms import EditForm
import app


class RecordValidator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, headers=[], record={}):
        """
        Validates a single record. Gets a line number and a list of headers as
        well as a dict. Returns a list of issues found, which can be empty.
        """
        form = EditForm(MultiDict(record), csrf_enabled=False)
        result = form.validate()
        errors = form.errors
        return result, errors, form


class Validator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, headers=[], records=[]):
        """
        Validates input, which consists of a list of headers with a series of
        records. Returns a tuple consisting of a bool and a list of issues.
        """
        results = {}
        record_validator = RecordValidator()
        line_no = 5
        no_errors = True
        for record in records:
            line_no += 1
            validated, errors, form = record_validator.validate(headers, record)
            if not validated:
                no_errors = False
            results[line_no] = {
                'errors': errors,
                'form': form
            }
        return no_errors, results
