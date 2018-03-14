#!/bin/env python
import csv
import sys
from variant_annotation.missense_scores_tabix import MissenseScoresDB
from variant_annotation.variant import Variant
import argparse

mDB = MissenseScoresDB()

def get_argument_parser():
    parser = argparse.ArgumentParser(
        description='Add missense scores from dbSNFP',
        epilog="Supported columns:\n" + '\n'.join(mDB.get_field_names()))
    parser.add_argument('--input-file')
    parser.add_argument('--output-file')
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-v', help='variant column number/name', action='store')
    parser.add_argument('-e', help='effect type column number/name', action='store')
    parser.add_argument('--columns', action='append', default=[], dest="columns")
    return parser

def give_column_number(s, header):
    try:
        c = header.index(s)
        return(c+1)
    except:
        sys.stderr.write("Used parameter: " + s + " does NOT exist in the input file header\n")
        sys.exit(-678)

def assign_values(param, header=None):
    if param == None:
        return(param)
    try:
        param = int(param)
    except:
        if header == None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, header)
    return(param)

class MissenseScoresAnnotator(object):

    def __init__(self, opts=None, args=None, header=None):
        if opts is not None:
            self.opts = opts
        elif args is not None:
            self.opts = get_argument_parser().parse_args(args)
        else:
            raise ValueError('Either opts or args argument must be provided')
        self.header = header
        if self.opts.columns is not None:
            self.header.extend(self.opts.columns)
        self._init_cols()
        self.mDB = mDB

    def _init_cols(self):
        opts = self.opts
        header = self.header

        if opts.x is None and opts.c is None:
            opts.x = 'location'
        if opts.v is None:
            opts.v = 'variant'
        if opts.e is None:
            opts.e = 'effectType'

        self.argColumnNs = []
        for opt in [opts.c, opts.p, opts.x, opts.v]:
            self.argColumnNs.append(assign_values(opt, header))
        self.effectTypeColumn = assign_values(opts.e, header)

    def annotate_file(self, input, output):
        opts = self.opts
        reader = csv.DictReader(input, delimiter='\t')
        writer = csv.DictWriter(output, delimiter='\t', fieldnames=self.header)
        writer.writeheader()
        for row in reader:
            values = self.line_annotations(row.values(), opts.columns)
            row.update({opts.columns[i]: values[i] for i in range(0, len(opts.columns))})
            writer.writerow(row)

    def line_annotations(self, line, new_cols_order):
        if line[self.effectTypeColumn-1]:
            params = [line[i-1] if i!=None else None for i in self.argColumnNs]
            variant = Variant(*params)
            missense_scores = self.mDB.get_missense_score(variant)
            if missense_scores is not None:
                return [missense_scores[k] for k in new_cols_order]
        return ['' for col in new_cols_order]


if __name__ == "__main__":
    opts = get_argument_parser().parse_args()
    with open(args.input_file, "r") as csvfile, \
            open(args.output_file, "w") as output:
        header = csvfile.readline()
        annotator = MissenseScoresAnnotator(opts=opts, header=header.split('\t'))
        annotator.annotate_file(csvfile, output)
