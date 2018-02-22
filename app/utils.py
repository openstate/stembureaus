#!/usr/bin/env python
import sys

import fiona
import shapely
import shapely.geometry


def get_shapes_for(shape_file, code, prop_field='GM_CODE'):
    shapes = []
    with fiona.open(shape_file) as shape_records:
        shapes = [
            (shapely.geometry.asShape(s['geometry']), s['properties'],)
            for s in shape_records if s['properties'][prop_field] == code]
    return shapes


def find_shape(lat, lon, shapes):
    point = shapely.geometry.Point(float(lat), float(lon))
    for shape, props in shapes:
        if shape.contains(point):
            return props


def find_buurt_and_wijk(muni_code, lat, lon):
    wijken = get_shapes_for(
        'data/adressen/wijk_2017_recoded/wijk_2017.shp', muni_code)
    wijk_props = find_shape(lat, lon, wijken)
    buurten = get_shapes_for(
        'data/adressen/buurt_2017_recoded/buurt_2017.shp',
        wijk_props['WK_CODE'], 'WK_CODE')
    buurt_props = find_shape(lat, lon, buurten)
    return (
        wijk_props['WK_CODE'], wijk_props['WK_NAAM'], buurt_props['BU_CODE'],
        buurt_props['BU_NAAM'],)
