from __future__ import absolute_import
import optparse
import sys
import gzip
import pysam

import GenomeAccess
from .utilities import *

class IterativeAccess:

    XY_INDEX = {'X': 23, 'Y': 24}

    def __init__(self, score_file_name, score_default_value, score_column,
            chr_column, pos_begin_column, pos_end_column, *search_columns):
        self.score_default_value = score_default_value
        self.file = gzip.open(score_file_name, 'rb')
        self.header = self.file.readline().rstrip('\n').split('\t')
        self.chr_index = self.header.index(chr_column)
        self.pos_begin_index = self.header.index(pos_begin_column)
        self.pos_end_index = self.header.index(pos_end_column)
        self.search_columns = search_columns
        self.search_indices = [self.header.index(col)
                               for col in search_columns]
        self.score_index = self.header.index(score_column)
        self.current = (-1, 0)

    def next_line(self):
        line = self.file.readline()
        if line is not None:
            line = line.rstrip('\n')
        if line != '':
            return line.split('\t')
        else:
            return None

    def chr_to_int(self, chr):
        chr = chr.replace('chr', '')
        return self.XY_INDEX.get(chr) or int(chr)

    def key_of(self, line):
        return (self.chr_to_int(line[self.chr_index]),
            int(line[self.pos_end_index]))

    def get_score(self, chr, pos, *args):
        chr = self.chr_to_int(chr)
        while self.current < (chr, pos):
            self.current_line = self.next_line()
            if self.current_line is None:
                break
            self.current = self.key_of(self.current_line)

        if self.current[1] < pos:
            # file is over
            self.current = (100000, 0)
        elif int(self.current_line[self.pos_begin_index]) <= pos:
            if [self.current_line[i] for i in self.search_indices] == list(args):
                return self.current_line[self.score_index]
        return self.score_default_value


class DirectAccess:

    def __init__(self, score_file_name, score_default_value, score_column,
            *search_columns):
        self.score_default_value = score_default_value
        with gzip.open(score_file_name) as file:
            self.header = file.readline().strip('\n\r').split('\t')
        self.search_columns = search_columns
        self.search_indices = [self.header.index(col)
                                  for col in search_columns]
        self.score_index = self.header.index(score_column)
        self.file = pysam.Tabixfile(score_file_name)

    def get_score(self, chr, pos, *args):
        args = list(args)
        try:
            for line in self.file.fetch(chr, pos-1, pos, parser=pysam.asTuple()):
                if args == [line[i] for i in self.search_indices]:
                    return line[self.score_index]
        except ValueError:
            pass
        return self.score_default_value


class ScoreAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None, search_columns=[],
            columns_in_score_file=['chr', 'position', 'position']):
        super(ScoreAnnotator, self).__init__(opts, header)
        self.search_columns = search_columns
        self.columns_in_score_file = columns_in_score_file
        self._init_cols()
        self._init_score_file()
        self.header.append(opts.label if opts.label else opts.score_column)

    def _init_cols(self):
        opts = self.opts
        header = self.header
        if opts.x == None and opts.c == None:
            opts.x = "location"

        chr_col = assign_values(opts.c, header)
        pos_col = assign_values(opts.p, header)
        loc_col = assign_values(opts.x, header)

        self.arg_columns = [chr_col, pos_col, loc_col] + \
            [assign_values(col, header) for col in self.search_columns]

    def _init_score_file(self):
        if not self.opts.scores_file:
            sys.stderr.write("You should provide a score file location.\n")
            sys.exit(-78)
        else:
            if self.opts.default_value is None:
                self.opts.default_value = ''
            if self.opts.direct:
                self.file = DirectAccess(self.opts.scores_file,
                    self.opts.default_value, self.opts.score_column,
                    *self.columns_in_score_file[3:])
            else:
                self.file = IterativeAccess(self.opts.scores_file,
                    self.opts.default_value, self.opts.score_column,
                    *self.columns_in_score_file)

    @property
    def new_columns(self):
        return [self.opts.score_column]

    def _get_score(self, chr=None, pos=None, loc=None, *args):
        if loc != None:
            chr, pos = loc.split(':')
        if chr != '':
            return self.file.get_score(chr, int(pos), *args)
        else:
            return ''

    def line_annotations(self, line, new_columns):
        params = [line[i-1] if i!=None else None for i in self.arg_columns]
        return [self._get_score(*params)]
