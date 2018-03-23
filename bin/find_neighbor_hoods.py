#!/usr/bin/env python
import sys
import os
import re
from pprint import pprint
from copy import deepcopy

import fiona
import shapely
import shapely.geometry

import csv
import codecs
import io

import csv
import codecs
import io


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


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.writer = csv.writer(f, dialect=dialect, **kwds)

    def writerow(self, row):
        self.writer.writerow(row)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def get_shapes(shape_file):
    shapes = []
    with fiona.open(shape_file) as shape_records:
        shapes = [
            (shapely.geometry.asShape(s['geometry']), s['properties'],)
            for s in shape_records]
    return shapes


def main():
    if len(sys.argv) < 4:
        print("Usage: merge.py <shape_file> <lat_field> <lon_field>")
        return 1

    reader = UnicodeReader(sys.stdin, delimiter=';')
    writer = UnicodeWriter(sys.stdout)
    header = reader.__next__()
    shapes = get_shapes(sys.argv[1])
    shapes_by_muni = {}
    for s, p in shapes:
        gm_code = p[u'GM_CODE']
        try:
            shapes_by_muni[gm_code] += [(s, p,)]
        except Exception:
            shapes_by_muni[gm_code] = [(s, p,)]
    out_header = deepcopy(header)
    out_header += [
        'buurt_code', 'buurt_naam', 'wijk_code', 'gem_code',
        'gem_naam']
    writer.writerow(out_header)

    lat_field = sys.argv[3]
    lon_field = sys.argv[2]
    lat_fb_field = sys.argv[3]
    lon_fb_field = sys.argv[2]

    for row in reader:
        out_row = deepcopy(row)
        data = dict(zip(header, row))
        if (data[lon_field] != u'-') and (data[lat_field] != u''):
            lat = data[lat_field]
            lon = data[lon_field]
        else:
            lat = data[lat_fb_field]
            lon = data[lon_fb_field]
        if (lat != u'-') and (lon != u'-'):
            point = shapely.geometry.Point(float(lat), float(lon))
            gm_code = 'GM%s' % (data['object_id'][0:4])
            if gm_code in shapes_by_muni:
                gm_shapes = shapes_by_muni[gm_code]
            else:
                gm_shapes = []
            for shape, props in gm_shapes:
                if shape.contains(point):
                    for fld in [
                        u'BU_CODE', u'BU_NAAM', u'WK_CODE',
                        u'GM_CODE', u'GM_NAAM'
                    ]:
                        out_row.append(props[fld])
                    break
        if len(out_row) == len(row):  # if we did not find anything
            out_row += [u'-', u'-', u'-', u'-', u'-', u'-']
        writer.writerow(out_row)

    return 0

if __name__ == '__main__':
    sys.exit(main())
