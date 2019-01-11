#!/usr/bin/env python
import os

import fiona
import shapely
import shapely.geometry
from pyproj import Proj, transform


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
            self.wijken_for_muni = {}
            for g, p in self.wijken:
                try:
                    self.wijken_for_muni[p['GM_CODE']].append((g, p,))
                except KeyError:
                    self.wijken_for_muni[p['GM_CODE']] = [(g, p,)]

        if os.path.exists('data/adressen/buurt_2017_recoded/buurt_2017.shp'):
            self.buurten = get_shapes(
                'data/adressen/buurt_2017_recoded/buurt_2017.shp')
            self.buurten_for_wijk = {}
            for g, p in self.buurten:
                try:
                    self.buurten_for_wijk[p['WK_CODE']].append((g, p,))
                except KeyError:
                    self.buurten_for_wijk[p['WK_CODE']] = [(g, p,)]

    def get_wijken_for(self, code):
        self._load()
        return self.wijken_for_muni[code]

    def get_buurten_for(self, code):
        return self.buurten_for_wijk[code]

_wijken_buurten = WijkenBuurtenData()


def find_shape(lat, lon, shapes):
    point = shapely.geometry.Point(float(lat), float(lon))
    for shape, props in shapes:
        if shape.contains(point):
            return props


def find_buurt_and_wijk(bag_nummer, muni_code, lon, lat):
    try:
        wijken = _wijken_buurten.get_wijken_for(muni_code)
    except KeyError:
        wijken = []

    if len(wijken) <= 0:
        wijken = _wijken_buurten.wijken

    try:
        wijk_props = find_shape(float(lon), float(lat), wijken)
        buurten = _wijken_buurten.get_buurten_for(wijk_props['WK_CODE'])
        buurt_props = find_shape(float(lon), float(lat), buurten)
    except TypeError:
            return ('', '', '', '',)
    return (
        wijk_props['WK_CODE'], wijk_props['WK_NAAM'], buurt_props['BU_CODE'],
        buurt_props['BU_NAAM'],)


# Converts rijksdriehoekstelsel to latitude and longitude, from
# https://publicwiki.deltares.nl/display/OET/Python+convert+coordinates
p1 = Proj("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs")
p2 = Proj(proj='latlong', datum='WGS84')


def convert_xy_to_latlong(x, y):
    longitude, latitude, _ = transform(p1, p2, x, y, 0.0)
    return (longitude, latitude)


def convert_latlong_to_xy(longitude, latitude):
    x, y, _ = transform(p2, p1, longitude, latitude, 0.0)
    return (x, y)
