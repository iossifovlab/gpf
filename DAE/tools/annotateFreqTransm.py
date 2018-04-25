#!/usr/bin/env python

import optparse
import sys
import gzip
import pysam

import GenomeAccess
from utilities import *

def get_argument_parser():
    desc = """Program to annotate variants with frequencies"""
    parser = optparse.OptionParser(description=desc)
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_option('-v', help='variant column number/name', action='store')

    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_option('-G', help='genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ', type='string', action='store')
    parser.add_option('--Graw', help='outside genome file', type='string', action='store')

    parser.add_option('-F', '--scores-file', help='file containing the scores', type='string', action='store')
    parser.add_option('--direct', help='the score files is tabix indexed', default=False, action='store_true')
    parser.add_option('--score-column', help='column in score file that contains the score (default: all.altFreq)', default='all.altFreq', type='string', action='store')
    parser.add_option('--label', help='label of the new column; defaults to the name of the score column', type='string', action='store')

    return parser


class IterativeAccess:

    XY_INDEX = {'X': 23, 'Y': 24}

    def __init__(self, file_name, score_column):
        self.file = gzip.open(file_name, 'rb')
        self.header = self.file.readline().rstrip('\n').split('\t')
        self.chr_index = self.header.index('chr')
        self.pos_index = self.header.index('position')
        self.var_index = self.header.index('variant')
        self.score_index = self.header.index(score_column)
        self.current = (-1, 0, 0)

    def next_line(self):
        line = self.file.readline()
        if line is not None:
            line = line.rstrip('\n')
        if line != '':
            return line.split('\t')
        else:
            return None

    def key_of(self, line):
        return (self.chr_to_int(line[self.chr_index]),
            int(line[self.pos_index]),
            line[self.var_index])

    def chr_to_int(self, chr):
        chr = chr.replace('chr', '')
        return self.XY_INDEX.get(chr, int(chr))

    def get_score(self, chr, pos, var):
        search_key = (self.chr_to_int(chr), pos, var)
        while self.current < search_key:
            self.current_line = self.next_line()
            if self.current_line is None:
                break
            self.current = self.key_of(self.current_line)

        if self.current < search_key:
            self.current = (100000, 0, 0)

        if self.current == search_key and self.current_line:
            return self.current_line[self.score_index]
        return ''


class DirectAccess:

    def __init__(self, file_name, score_column):
        with gzip.open(file_name) as file:
            self.header = file.readline().strip('\n\r').split('\t')
        self.score_index = self.header.index(score_column)
        self.var_index = self.header.index('variant')
        self.file = pysam.Tabixfile(file_name)

    def get_score(self, chr, pos, var):
        try:
            for l in self.file.fetch(chr, pos-1, pos):
                line = l.strip("\n\r").split("\t")
                if var != line[self.var_index]:
                    continue
                return line[self.score_index]
        except ValueError:
            pass
        return ''

class FrequencyAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(FrequencyAnnotator, self).__init__(opts, header)
        self._init_cols()
        self._init_score_file()
        self.header.append(opts.label if opts.label else opts.score_column)

    def _init_cols(self):
        opts = self.opts
        header = self.header
        if opts.x == None and opts.c == None:
            opts.x = "location"
        if (opts.v == None and opts.a == None) and (opts.v == None and opts.t == None):
            opts.v = "variant"

        chrCol = assign_values(opts.c, header)
        posCol = assign_values(opts.p, header)
        locCol = assign_values(opts.x, header)
        varCol = assign_values(opts.v, header)

        self.argColumnNs = [chrCol, posCol, locCol, varCol]

    def _init_score_file(self):
        if not self.opts.scores_file:
            sys.stderr.write("You should provide a score file location.\n")
            sys.exit(-78)
        else:
            if self.opts.direct:
                self.file = DirectAccess(self.opts.scores_file,
                    self.opts.score_column)
            else:
                self.file = IterativeAccess(self.opts.scores_file,
                    self.opts.score_column)

    @property
    def new_columns(self):
        return [self.opts.score_column]

    def _get_score(self, chr=None, pos=None, loc=None, var=None):
        if loc != None:
            chr, pos = loc.split(':')
        if chr != '':
            return self.file.get_score(chr, int(pos), var)
        else:
            return ''

    def line_annotations(self, line, new_columns):
        params = [line[i-1] if i!=None else None for i in self.argColumnNs]
        return [self._get_score(*params)]


if __name__ == "__main__":
    main(get_argument_parser(), FrequencyAnnotator)
