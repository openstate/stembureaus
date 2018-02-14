#!/usr/bin/env python
import sys
import json

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


def main(argv):
    if len(argv) < 2:
        print("Usage: shape-props-to-json.py <shape-file>")
        return 1

    shapes = get_shapes(argv[1])
    output = [p for s, p in shapes]
    print (json.dumps(output))

if __name__ == '__main__':
    sys.exit(main(sys.argv))
