import optparse
import sys
import gzip
import pysam

import GenomeAccess
from utilities import *

class ScoreFile(object):

    def __init__(self, score_file_name, score_file_header, scores_default_values,
            scores_columns, *search_columns):
        self.scores_default_values = scores_default_values
        self.search_indices = [self.header.index(col)
                               for col in search_columns]
        self.scores_indices = [self.header.index(col)
                               for col in scores_columns]

    def get_scores(self, chr, pos, *args):
        args = list(args)
        try:
            for line in self._fetch(chr, pos):
                if args == [line[i] for i in self.search_indices]:
                    return [line[i] for i in self.scores_indices]
        except ValueError:
            pass
        return self.scores_default_values


class IterativeAccess(ScoreFile):

    XY_INDEX = {'X': 23, 'Y': 24}

    def __init__(self, score_file_name, score_file_header, scores_default_values,
            scores_columns, chr_column, pos_begin_column, pos_end_column,
            *search_columns):
        self.file = gzip.open(score_file_name, 'rb')
        self.header = score_file_header
        if self.header is None:
            self.header = self.file.readline().rstrip('\n')[1:].split('\t')
        super(IterativeAccess, self).__init__(score_file_name, score_file_header,
            scores_default_values, scores_columns, *search_columns)
        self.chr_index = self.header.index(chr_column)
        self.pos_begin_index = self.header.index(pos_begin_column)
        self.pos_end_index = self.header.index(pos_end_column)
        self.current_lines = []

    def _fetch(self, chr, pos):
        # TODO this implements closed interval because we want to support
        # files with single position column
        chr = self._chr_to_int(chr)

        self.current_lines = [
            line for line in self.current_lines
            if line[self.chr_index] > chr or (line[self.chr_index] == chr and \
                line[self.pos_end_index] >= pos)
        ]

        while len(self.current_lines) == 0 or \
                self.current_lines[-1][self.pos_begin_index] <= pos or \
                self.current_lines[-1][self.chr_index] > chr:
            line = self._next_line()
            if line is not None:
                self.current_lines.append(line)
            else:
                break

        return [
            line for line in self.current_lines
            if line[self.pos_end_index] >= pos and line[self.chr_index] == chr
        ]

    def _next_line(self):
        line = self.file.readline()
        if line is not None:
            line = line.rstrip('\n')
        if line != '':
            return line.split('\t')
        return None

    def _chr_to_int(self, chr):
        chr = chr.replace('chr', '')
        return self.XY_INDEX.get(chr) or int(chr)

    def get_scores(self, chr, pos, *args):
        for line in self._fetch(chr, pos):
            if [line[i] for i in self.search_indices] == args:
                return [line[i] for i in self.scores_indices]
        return self.scores_default_values


class DirectAccess(ScoreFile):

    def __init__(self, score_file_name, score_file_header, scores_default_values,
            scores_columns, *search_columns):
        self.header = score_file_header
        if self.header is None:
            with gzip.open(score_file_name, 'rb') as file:
                self.header = file.readline().rstrip('\n')[1:].split('\t')
        super(DirectAccess, self).__init__(score_file_name, score_file_header,
            scores_default_values, scores_columns, *search_columns)
        self.file = pysam.Tabixfile(score_file_name)

    def _fetch(self, chr, pos):
        return self.file.fetch(chr, pos-1, pos, parser=pysam.asTuple())


class ScoreAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None, search_columns=[],
            score_file_header=None,
            score_file_index_columns=['chr', 'position', 'position']):
        super(ScoreAnnotator, self).__init__(opts, header)
        self.search_columns = search_columns
        self.score_file_header = score_file_header
        self.score_file_index_columns = score_file_index_columns
        self.scores_columns = opts.scores_columns.split(',')
        self._init_cols()
        self._init_score_file()
        self.header.append(opts.labels.split(',') if opts.labels else self.scores_columns)

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
                    self.score_file_header,
                    self.opts.default_values.split(','), self.scores_columns,
                    *self.score_file_index_columns[3:])
            else:
                self.file = IterativeAccess(self.opts.scores_file,
                    self.score_file_header,
                    self.opts.default_values.split(','), self.scores_columns,
                    *self.score_file_index_columns)

    @property
    def new_columns(self):
        return self.scores_columns

    def _get_scores(self, chr=None, pos=None, loc=None, *args):
        if loc != None:
            chr, pos = loc.split(':')
        if chr != '':
            return self.file.get_scores(chr, int(pos), *args)
        else:
            return ''

    def line_annotations(self, line, new_columns):
        params = [line[i-1] if i!=None else None for i in self.arg_columns]
        return self._get_scores(*params)
