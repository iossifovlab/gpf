#!/usr/bin/env python

from __future__ import absolute_import
import sys
import argparse
from pyliftover import LiftOver
from .utilities import *

def get_argument_parser():
    desc = """Program to annotate variants (substitutions & indels & cnvs)"""
    parser = argparse.ArgumentParser(version='%prog version 2.2 10/October/2013', description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-F', '--file', help='lift over description file path', required=True, action='store')
    parser.add_argument('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')
    parser.add_argument('--new-c', help='name for the generated chromosome column', default='chrLiftOver', action='store')
    parser.add_argument('--new-p', help='name for the generated position column', default='positionLiftOver', action='store')
    parser.add_argument('--new-x', help='name for the generated location (chr:pos) column', default='locationLiftOver', action='store')
    return parser


class LiftOverAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(LiftOverAnnotator, self).__init__(opts, header)

        if opts.x is not None:
            assert(opts.c is None)
            assert(opts.p is None)
            self.argCols = [assign_values(opts.x, header)]
            self._new_columns = ['new_x']
            labels = [opts.new_x]
        else:
            assert(opts.c is not None)
            assert(opts.p is not None)
            self.argCols = [assign_values(opts.c, header),
                assign_values(opts.p, header)]
            self._new_columns = ['new_c', 'new_p']
            labels = [opts.new_c, opts.new_p]

        self.header = self.header + labels
        self.lift_over = LiftOver(opts.file)

    @property
    def new_columns(self):
        return self._new_columns

    def line_annotations(self, line, new_columns):
        args = [line[col-1] for col in self.argCols]
        if len(args) == 1:
            args = args[0].split(':')
        chromosome, position = args
        positions = map(lambda p: int(p) - 1, position.split('-'))

        convert_result = [self.lift_over.convert_coordinate(chromosome, p)
                          for p in positions]

        result = []
        for positions in convert_result:
            if len(positions) == 0:
                return ['' for i in new_columns]
            else:
                if len(positions) > 1:
                    sys.stderr.write(
                        'Position {} has more than one corresponding'
                        ' position in target assembly.'.format(position))
                result.append(str(positions[0][1] + 1))

        new_c = convert_result[0][0][0]
        new_p = '-'.join(result)
        new_x = '{}:{}'.format(new_c, new_p)
        return [locals()[col] for col in new_columns]


if __name__ == "__main__":
    main(get_argument_parser(), LiftOverAnnotator)
