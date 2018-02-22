#!/usr/bin/env python

import sys
sys.path.insert(0, '.')

from app.utils import find_buurt_and_wijk

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


def main():
    reader = UnicodeReader(sys.stdin, delimiter=';')
    for row in reader:
        print(row[0], row[1], find_buurt_and_wijk('GM0363', row[-2], row[-1]))
    return 0

if __name__ == '__main__':
    sys.exit(main())
