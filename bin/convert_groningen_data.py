#!/usr/bin/env python

import os
import sys
import csv

from openpyxl import load_workbook
from pyexcel_ods3 import get_data, save_data

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

    for muni, points in points_per_muni.items():
        # first Excel
        path = "data/%s-2018-03-21.xlsx" % (muni,)
        os.system("cp waarismijnstemlokaal.nl_invulformulier.xlsx \"%s\"" % (
            path,))
        workbook = load_workbook(path)
        worksheet = workbook['Attributen']
        col = 5
        for point in points:
            worksheet.cell(row=2, column=col, value=point['Naam stembureau'])
            if 'BAG referentienummer' in point:
                worksheet.cell(row=6, column=col, value=point['BAG referentienummer'])
            if 'Longitude' in point:
                worksheet.cell(row=8, column=col, value=point['Longitude'])
            if 'Latitude' in point:
                worksheet.cell(row=9, column=col, value=point['Latitude'])
            worksheet.cell(row=11, column=col, value=point['Openingstijden'])
            col += 1
        workbook.save(path)

        # now openoffice
        path = "data/%s-2018-03-21.ods" % (muni,)
        os.system("cp waarismijnstemlokaal.nl_invulformulier.ods \"%s\"" % (
            path,))
        data = get_data(path)
        for point in points:
            data['Attributen'][2].append(point['Naam stembureau'])
            if 'BAG referentienummer' in point:
                data['Attributen'][5].append(point['BAG referentienummer'])
            if 'Longitude' in point:
                data['Attributen'][7].append(point['Longitude'])
            if 'Latitude' in point:
                data['Attributen'][8].append(point['Latitude'])
            data['Attributen'][10].append(point['Openingstijden'])
            save_data(path, data)
    return 0

if __name__ == '__main__':
    sys.exit(main())
