#!/bin/env python

# Jan 21th 2014
# by Ewa

from dbSNP import load_dbSNP
from utilities import *
import sys
import optparse
import os

def get_argument_parser():
    desc = """Program to annotate genetic variants with dbSNP"""
    parser = optparse.OptionParser(version='%prog version 1.0 21/January/2014', description=desc, add_help_option=False)
    parser.add_option('-h', '--help', default=False, action='store_true')
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_option('-v', help='variant column number/name', action='store')
    parser.add_option('-a', help='alternative allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_option('-r', help='reference allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_option('-t', help='type of mutation column number/name', action='store')
    parser.add_option('-q', help='seq column number/name', action='store')
    parser.add_option('-l', help ='length column number/name', action='store')

    parser.add_option('-F', help='dbSNP file', action='store') #
    parser.add_option('-C', help='dbSNP column numbers to annotate with', default="5", action='store')
    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

class DbSNPAnnotator(object):

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header

        if opts.x == None and opts.c == None:
            opts.x = "location"
        if (opts.v == None and opts.a == None) and (opts.v == None and opts.t == None):
            opts.v = "variant"

        chrCol = assign_values(opts.c, header)
        posCol = assign_values(opts.p, header)
        locCol = assign_values(opts.x, header)
        varCol = assign_values(opts.v, header)
        altCol = assign_values(opts.a, header)
        refCol = assign_values(opts.r, header)
        typeCol = assign_values(opts.t, header)
        seqCol = assign_values(opts.q, header)
        lengthCol = assign_values(opts.l, header)

        self.argColumnNs = [chrCol, posCol, locCol, varCol, refCol, altCol]

        self.db_snp = load_dbSNP(file=opts.F)
        self.score_names = self.db_snp.Scores[self.db_snp.Scores.keys()[0]].dtype.names
        self.new_columns = self.score_names
        if opts.C is not None:
            opts.C = opts.C.replace(" ", "")
            self.db_columns = map(int, opts.C.split(":"))
            self.new_columns = [score_names[i-1] for i in self.db_columns]
        self.chr_format = None

    def annotate_file(self, input, output):
        if self.opts.no_header == False:
            output.write("\t".join(self.header + self.new_columns))

        k = 0
        for l in input:
            if l[0] == "#":
                output.write(l)
                continue
            k += 1
            if k%1000 == 0:
                sys.stderr.write(str(k) + " lines processed\n")

            line = l[:-1].split("\t")
            line_annotations = self.line_annotations(line, self.new_columns)
            
            output.write("\t".join(line + line_annotations) + "\n")

    def line_annotations(self, line, columns_in_order):
        params = [line[i-1] if i != None else None for i in self.argColumnNs]

        column_values_indices = [self.score_names.index(col)
                                 for col in columns_in_order]

        if self.chr_format is None:
            if params[0] == None:
                chr = params[3].split(":")[0]
            else:
                chr = params[0]
            if chr.startswith("chr"):
                self.chr_format = "hg19"
            else:
                self.chr_format = "GATK"
                self.db_snp.relabel_chromosomes()

        values_array = self.db_snp.find_variant(*params)

        if not values_array:
            values = [''] * len(columns_in_order)
        else:
            values = []
            for index in column_values_indices:
                values.append("|".join([str(value_array[index])
                                        for value_array in values_array]))
        return values

if __name__ == "__main__":
    main(get_argument_parser(), DbSNPAnnotator)
