#!/usr/bin/env python

import os
import sys
import csv

sys.path.insert(0, '.')

from app.utils import find_buurt_and_wijk
from app.models import BAG


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
        openbareruimte=data['Straat'].strip(),
        huisnummer=data['Huisnummer'].strip(),
        huisnummertoevoeging=data['Toevoeging'].strip(),
        woonplaats=data['Plaats'].strip()
    ).first()


def find_bag_record_by_huisletter(data):
    return BAG.query.filter_by(
        openbareruimte=data['Straat'].strip(),
        huisnummer=data['Huisnummer'].strip(),
        huisletter=data['Toevoeging'].strip(),
        woonplaats=data['Plaats'].strip()
    ).first()


def main():
    reader = UnicodeReader(sys.stdin, delimiter=',')
    header = reader.__next__()
    points_per_muni = {}
    for row in reader:
        data = dict(zip(header, row))
        tijd_open, tijd_sluit = data['Openingsti'].split(' - ', 1)
        bag = find_bag_record(data)
        if bag is None:
            bag = find_bag_record_by_huisletter(data)
        if bag is None:
            record = {
                'Naam stembureau': data['Naam'],
                'Openingstijden': '2018-03-21T%s:00 tot 2018-03-21T%s:00' % (
                    tijd_open, tijd_sluit)
            }
        else:
            record = {
                'BAG referentienummer': bag.nummeraanduiding,
                'Naam stembureau': data['Naam'],
                'Openingstijden': '2018-03-21T%s:00 tot 2018-03-21T%s:00' % (
                    tijd_open, tijd_sluit),
                'Longitude': float(bag.lon),
                'Latitude': float(bag.lat)
            }
        try:
            points_per_muni[data['Gemeente']].append(record)
        except KeyError:
            points_per_muni[data['Gemeente']] = [record]
    print(points_per_muni)

    for muni, points in points_per_muni.items():
        path = "data/%s-2018-03-21.xlsx" % (muni,)
        os.system("cp waarismijnstemlokaal.nl_invulformulier.xlsx \"%s\"" % (
            path,))
    return 0

if __name__ == '__main__':
    sys.exit(main())
