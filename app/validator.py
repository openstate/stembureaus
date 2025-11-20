#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug.datastructures import MultiDict

from app.forms import EditForm

import uuid


# Use the validators that are also used in the EditForm
class RecordValidator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, record={}):
        """
        Validates a single record.
        Returns a list of issues found, which can be empty.
        """
        form = EditForm(MultiDict(record), meta={'csrf': False})
        result = form.validate()
        errors = form.errors
        return result, errors, form


class Validator(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, records=[]):
        """
        Validates input, which consists of a of a list of records.
        Returns a tuple consisting of a bool and a list of issues.
        """
        results = {}
        record_validator = RecordValidator()
        column_number = 5
        no_errors = True
        found_any_record_with_values = False
        for record in records:
            column_number += 1

            # Only validate records which have at least one field with a
            # value
            record_values = [str(x).replace('0', '') for x in record.values()]
            if ''.join(record_values).strip() != '':
                validated, errors, form = record_validator.validate(record)
                found_any_record_with_values = True
                if not validated:
                    no_errors = False
            # Keep track of empty columns as well in order to provide
            # the correct columns numbers in the user facing error
            # messages when some columns are left empty in between
            # filled columns
            else:
                errors = ''
                form = ''

            results[column_number] = {
                'errors': errors,
                'form': form,
                'uuid': uuid.uuid4().hex
            }
        return {
            'no_errors': no_errors,
            'found_any_record_with_values': found_any_record_with_values,
            'results': results
        }
