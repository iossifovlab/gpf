from __future__ import unicode_literals
import common.config
from tools.utilities import *


def get_arguments():
    return {
        '-c': {
            'help': 'chromosome column number/name'
        },
        '-p': {
            'help': 'position column number/name'
        },
        '-x': {
            'help': 'location (chr:position) column number/name'
        }
    }


class LocationPreannotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        self._new_columns = ['LOCATION:chr', 'LOCATION:position', 'LOCATION:location']
        if opts.x == None and opts.c == None:
            opts.x = "location"
        self.argColumnNs = [assign_values(col, header)
                            for col in [opts.c, opts.p, opts.x]]

    @property
    def new_columns(self):
        return self._new_columns

    def _location_columns(self, chromosome=None, position=None, location=None):
        if chromosome is not None and position is not None:
            location = '{}:{}'.format(chromosome, position)
        elif location is not None:
            chromosome, position = location.split(':')
        return {
            'LOCATION:chr': chromosome,
            'LOCATION:position': position,
            'LOCATION:location': location
        }

    def line_annotations(self, line, new_columns):
        if len(new_columns) == 0:
            return []
        params = [line[i-1] if i!=None else None for i in self.argColumnNs]
        location_columns = self._location_columns(*params)
        return [location_columns[col] for col in new_columns]
