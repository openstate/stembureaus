#!/usr/bin/env python

import sys
sys.path.insert(0, '.')

from app.utils import find_buurt_and_wijk
from app.models import BAG

import csv, codecs, io


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def __next__(self):
        row = next(self.reader)
        return row

    def __iter__(self):
        return self


def find_bag_record(data):
    return BAG.query.filter_by(
        openbareruimte=data['Straat'],
        huisnummer=data['Huisnummer'],
        huisnummertoevoeging=data['Toevoeging'],
        woonplaats=data['Plaats']
    ).first()


def main():
    reader = UnicodeReader(sys.stdin, delimiter=',')
    header = reader.__next__()
    for row in reader:
        data = dict(zip(header, row))
        print(data)
        bag = find_bag_record(data)
        print(bag)
    return 0

if __name__ == '__main__':
    sys.exit(main())
