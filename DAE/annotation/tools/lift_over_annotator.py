#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import gzip

import sys
import os
from pyliftover import LiftOver
from annotation.tools.annotator_base import VariantAnnotatorBase
from annotation.tools.schema import Schema


class LiftOverAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(LiftOverAnnotator, self).__init__(config)

        self.chrom = self.config.options.c
        self.pos = self.config.options.p
        if not self.config.options.vcf:
            self.location = self.config.options.x
        else:
            self.location = None
            assert self.chrom is not None
            assert self.pos is not None

        self.columns_config = self.config.columns_config
        assert 'new_x' in self.columns_config or \
            ('new_c' in self.columns_config and 'new_p' in self.columns_config)

        self.lift_over = self.build_lift_over(self.config.options.chain_file)

    def collect_annotator_schema(self, schema):
        super(LiftOverAnnotator, self).collect_annotator_schema(schema)
        for key, value in self.columns_config.items():
            if key == 'new_x' or key == 'new_c':
                schema.columns[value] = \
                    Schema.produce_type('str')
            elif key == 'new_p':
                schema.columns[value] = \
                    Schema.produce_type('str')

    @staticmethod
    def build_lift_over(chain_filename):
        assert chain_filename is not None
        assert os.path.exists(chain_filename)

        chain_file = gzip.open(chain_filename, "r")
        return LiftOver(chain_file)

    def do_annotate(self, aline, variant):
        if self.location and self.location in aline:
            location = aline[self.location]
            chrom, pos = location.split(":")
            pos = int(pos)
        else:
            chrom = aline[self.chrom]
            pos = int(aline[self.pos])

        # positions = [int(p) - 1 for p in position.split('-')]
        liftover_pos = pos - 1
        converted_coordinates = self.lift_over.convert_coordinate(
            chrom, liftover_pos)
        if len(converted_coordinates) == 0:
            print("position: chrom=", chrom, "; pos=", pos,
                  "(0-pos=", liftover_pos, ")",
                  "can not be converted into target reference genome",
                  file=sys.stderr)
            new_c = None
            new_p = None
            new_x = None
        else:
            if len(converted_coordinates) > 1:
                print(
                    "position: chrom=", chrom, "; pos=", pos,
                    "has more than one corresponding position "
                    "into target reference genome", converted_coordinates,
                    file=sys.stderr)

            new_c = converted_coordinates[0][0]
            new_p = converted_coordinates[0][1] + 1
            new_x = '{}:{}'.format(new_c, new_p)

        if 'new_x' in self.columns_config:
            aline[self.columns_config['new_x']] = new_x
        if 'new_c' in self.columns_config:
            aline[self.columns_config['new_c']] = new_c
        if 'new_p' in self.columns_config:
            aline[self.columns_config['new_p']] = new_p


# def get_argument_parser():
#     """
#     LiftOverAnnotator options::

#         usage: lift_over_variants.py [-h] [-v] [-c C] [-p P]
#                             [-x X] -F FILE [-H]
#                             [--new-c NEW_C] [--new-p NEW_P] [--new-x NEW_X]
#                             [infile] [outfile]

#         Program to annotate variants (substitutions & indels & cnvs)

#         positional arguments:
#           infile                path to input file; defaults to stdin
#           outfile               path to output file; defaults to stdout

#         optional arguments:
#           -h, --help            show this help message and exit
#           -v, --version         show program's version number and exit
#           -c C                  chromosome column number/name
#           -p P                  position column number/name
#           -x X                  location (chr:pos) column number/name
#           -F FILE, --file FILE  lift over description file path
#           -H                    no header in the input file
#           --new-c NEW_C         name for the generated chromosome column
#           --new-p NEW_P         name for the generated position column
#           --new-x NEW_X         name for the generated location (chr:pos)
#                                 column
#     """
#     desc = """Program to annotate variants (substitutions & indels & cnvs)"""
#     parser = argparse.ArgumentParser(
#         version='%prog version 2.2 10/October/2013', description=desc)
#     parser.add_argument(
#         '-c', help='chromosome column number/name', action='store')
#     parser.add_argument(
#         '-p', help='position column number/name', action='store')
#     parser.add_argument(
#         '-x', help='location (chr:pos) column number/name', action='store')
#     parser.add_argument(
#         '-F', '--file', help='lift over description file path',
#         required=True, action='store')
#     parser.add_argument(
#         '-H', help='no header in the input file', default=False,
#         action='store_true', dest='no_header')
#     parser.add_argument(
#         '--new-c', help='name for the generated chromosome column',
#         default='chrLiftOver', action='store')
#     parser.add_argument(
#         '--new-p', help='name for the generated position column',
#         default='positionLiftOver', action='store')
#     parser.add_argument(
#         '--new-x', help='name for the generated location (chr:pos) column',
#         default='locationLiftOver', action='store')
#     return parser


# if __name__ == "__main__":
#     main(get_argument_parser(), LiftOverAnnotator)
