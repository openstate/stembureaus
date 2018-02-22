#!/usr/bin/env python
import os

import fiona
import shapely
import shapely.geometry


def get_shapes(shape_file):
    shapes = []
    with fiona.open(shape_file) as shape_records:
        shapes = [
            (shapely.geometry.asShape(s['geometry']), s['properties'],)
            for s in shape_records]
    return shapes


class WijkenBuurtenData:
    def __init__(self, *arg, **kwargs):
        self.wijken = None
        self.buurten = None
        self._load()

    def _load(self):
        if self.wijken is not None and self.buurten is not None:
            return

        if os.path.exists('data/adressen/wijk_2017_recoded/wijk_2017.shp'):
            self.wijken = get_shapes(
                'data/adressen/wijk_2017_recoded/wijk_2017.shp')
        if os.path.exists('data/adressen/buurt_2017_recoded/buurt_2017.shp'):
            self.buurten = get_shapes(
                'data/adressen/buurt_2017_recoded/buurt_2017.shp')

    def get_wijken_for(self, code):
        self._load()
        return [(w, p,) for w, p in self.wijken if p['GM_CODE'] == code]

    def get_buurten_for(self, code):
        self._load()
        return [(w, p,) for w, p in self.buurten if p['WK_CODE'] == code]

_wijken_buurten = WijkenBuurtenData()


def find_shape(lat, lon, shapes):
    point = shapely.geometry.Point(float(lat), float(lon))
    for shape, props in shapes:
        if shape.contains(point):
            return props


def find_buurt_and_wijk(muni_code, lat, lon):
    wijken = _wijken_buurten.get_wijken_for(muni_code)
    wijk_props = find_shape(lat, lon, wijken)
    buurten = _wijken_buurten.get_buurten_for(wijk_props['WK_CODE'])
    buurt_props = find_shape(lat, lon, buurten)
    return (
        wijk_props['WK_CODE'], wijk_props['WK_NAAM'], buurt_props['BU_CODE'],
        buurt_props['BU_NAAM'],)
