#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function
import sys
import gzip
import pysam
import argparse
import pandas as pd
from configparser import ConfigParser
import os
from box import Box
from annotation.tools.annotator_config import LineConfig
from annotation.tools.utilities import AnnotatorBase, \
    assign_values, main, give_column_number
# from annotation.preannotators import variant_format


def get_argument_parser():
    """
    ScoreAnnotator options::

        usage: annotate_score_base.py [-h] [-c C] [-p P] [-x X] [-H]
                                 [-F SCORES_FILE]
                                 [--scores-config-file]
                                 [--direct]
                                 [--labels LABELS]
                                 [infile] [outfile]

        Program to annotate variants with frequencies

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -c C                  chromosome column number/name
          -p P                  position column number/name
          -x X                  location (chr:pos) column number/name
          --search-columns      additional columns in the file to use for
                                matching scores
          -H                    no header in the input file
          -F SCORES_FILE, --scores-file SCORES_FILE
                                file containing the scores
          --scores-config-file  .conf file for the scores file; defaults to
                                score file name
          --direct              the score files is tabix indexed
          --labels LABEL        label of the new column; defaults to the name
                                of the score column
    """
    desc = """Program to annotate variants with scores"""
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        '-c', help='chromosome column number/name', action='store')
    parser.add_argument(
        '-p', help='position column number/name', action='store')
    parser.add_argument(
        '-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument(
        '--search-columns',
        help='additional columns in file to use for matching scores')
    parser.add_argument(
        '-H', help='no header in the input file',
        action='store_true', dest='no_header')
    parser.add_argument(
        '-F', '--scores-file', help='file containing the scores',
        type=str, action='store')
    parser.add_argument(
        '--scores-config-file',
        help='file containing configurations for the score file',
        type=str, action='store')
    parser.add_argument(
        '--direct', help='the score files is tabix indexed',
        action='store_true')
    parser.add_argument(
        '--labels',
        help='labels of the new column; '
        'defaults to the name of the score column',
        type=str, action='store')

    # for name, args in variant_format.get_arguments().items():
    #     parser.add_argument(name, **args)

    return parser


def conf_to_dict(path):
    conf_parser = ConfigParser()
    conf_parser.optionxform = str
    conf_parser.read_file(path)

    conf_settings = dict(conf_parser.items('general'))
    conf_settings_cols = {'columns': dict(conf_parser.items('columns'))}
    conf_settings.update(conf_settings_cols)
    return conf_settings


def normalize_value(score_value):
    if ';' in score_value:
        result = score_value.split(';')
    elif ',' in score_value:
        result = score_value.split(',')
    else:
        result = [score_value]
    return [None if value in ['.', ''] else float(value)
            for value in result]


class ScoreFile(object):

    def __init__(self, score_file_name, config_input):
        self.filename = score_file_name
        self._load_config(config_input)
        self.line_config = LineConfig(self.config.header)

    def _load_config(self, config_input=None):
        # try default config path
        if config_input is None:
            config_input = self.filename + '.conf'
        # config is dict case
        if isinstance(config_input, dict):
            self.config = Box(config_input,
                              default_box=True, default_box_attr=None)
        elif os.path.exists(config_input):
            with open(config_input, 'r') as conf_file:
                conf_settings = conf_to_dict(conf_file)
                self.config = Box(
                    conf_settings, default_box=True,
                    default_box_attr=None)
        else:
            print(
                "You must provide a configuration file "
                "for the score file '{}'.\n".format(self.filename),
                file=sys.stderr)
            sys.exit(1)

        self.file = gzip.open(self.filename, 'rt', encoding='utf8')
        if self.config.header is None:
            header_str = self.file.readline().rstrip()
            if header_str[0] == '#':
                header_str = header_str[1:]
            self.config.header = header_str.split('\t')
        else:
            self.config.header = self.config.header.split(',')

        if self.config.columns.pos_end is None:
            self.config.columns.pos_end = self.config.columns.pos_begin

        self.search_indices = []
        self.search_columns = []
        if hasattr(self.config.columns, 'search'):
            if self.config.columns.search is not None:
                self.config.columns.search = \
                    self.config.columns.search.split(',')
                self.search_indices = [
                    self.config.header.index(col)
                    for col in self.config.columns.search]
                self.search_columns = self.config.columns.search
        self.config.columns.score = self.config.columns.score.split(',')
        self.scores_indices = [self.config.header.index(col)
                               for col in self.config.columns.score]

    def _fetch(self, chrom, pos_begin, pos_end):
        raise NotImplementedError()

    def fetch_score_lines(self, chrom, pos_begin, pos_end):
        score_lines = self._fetch(chrom, pos_begin, pos_end)
        res = []
        for line in score_lines:
            res.append(self.line_config.build(list(line)).columns)
        df = pd.DataFrame.from_records(
            res, columns=self.line_config.source_header)
        for score_name in self.config.columns.score:
            df[score_name] = df[score_name].astype("float32")
        return df

    def get_scores(self, new_columns, chrom, pos, *args):
        args = list(args)
        new_col_indices = [
            give_column_number(col, self.config.header) - 1
            for col in new_columns]
        try:
            score_lines = self._fetch(chrom, pos, pos)
            for line in score_lines:
                if args == [line[i] for i in self.search_indices]:
                    return [line[i] for i in new_col_indices]
        except ValueError:
            pass
        return [self.config.noScoreValue] * len(new_col_indices)


class IterativeAccess(ScoreFile):

    XY_INDEX = {'X': 23, 'Y': 24}

    def __init__(self, score_file_name, score_config=None, region=None):
        super(IterativeAccess, self).__init__(score_file_name, score_config)

        self.chr_index = \
            self.config.header.index(self.config.columns.chr)
        self.pos_begin_index = \
            self.config.header.index(self.config.columns.pos_begin)
        self.pos_end_index = \
            self.config.header.index(self.config.columns.pos_end)

        self.file = pysam.Tabixfile(score_file_name)
        try:
            self.file_iterator = self.file.fetch(
                region=region, parser=pysam.asTuple())
        except ValueError:
            self.file_iterator = iter([])
        self.current_lines = [self._next_line()]

    def _purge_line_buffer(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while len(self.current_lines) > 0:
            line = self.current_lines[0]
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
            if line_chrom > chrom or \
                    (line_chrom == chrom and line_pos_end >= pos_begin):
                break
            self.current_lines.pop(0)

    def _line_buffer_last_pos(self):
        if len(self.current_lines) == 0:
            return -1, -1, -1
        return self._line_pos(self.current_lines[-1])

    def _line_pos(self, line):
        return self._chr_to_int(line[self.chr_index]), \
            int(line[self.pos_begin_index]), \
            int(line[self.pos_end_index])

    def _fill_line_buffer(self, chrom, pos_begin, pos_end):
        buffer_chrom, buffer_pos_begin, buffer_pos_end = \
            self._line_buffer_last_pos()
        if (buffer_chrom == chrom and buffer_pos_end > pos_end) or \
                buffer_chrom > chrom:
            # the line buffer is full enough
            return
        line = self._next_line()
        line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
        while line_chrom < chrom or \
                (line_chrom == chrom and line_pos_end < pos_begin):
            line = self._next_line()
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)

        self.current_lines.append(line)
        while line_chrom == chrom and line_pos_end <= pos_end:
            line = self._next_line()
            self.current_lines.append(line)
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)

    def _regions_intersect(self, b1, e1, b2, e2):
        if b1 >= b2 and b1 <= e2:
            return True
        if e1 >= b2 and e1 <= e2:
            return True
        if b2 >= b1 and b2 <= e1:
            return True
        if e2 >= b1 and e2 <= e1:
            return True
        return False

    def _select_line_buffer(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.current_lines:
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
            if line_chrom != chrom:
                continue
            if self._regions_intersect(
                    pos_begin, pos_end,
                    line_pos_begin, line_pos_end):
                result.append(line)
        return result

    def _fetch(self, chrom, pos_begin, pos_end):
        chrom = self._chr_to_int(chrom)

        self._purge_line_buffer(chrom, pos_begin, pos_end)

        # fill the file buffer
        self._fill_line_buffer(chrom, pos_begin, pos_end)
        return self._select_line_buffer(chrom, pos_begin, pos_end)

    def _next_line(self):
        try:
            return next(self.file_iterator)
        except StopIteration:
            line = self.config.header[:]
            line[self.chr_index] = '25'
            line[self.pos_begin_index] = '-1'
            line[self.pos_end_index] = '-1'
            return line

    def _chr_to_int(self, chrom):
        chrom = chrom.replace('chr', '')
        return self.XY_INDEX.get(chrom) or int(chrom)


class DirectAccess(ScoreFile):

    def __init__(self, score_file_name, score_config=None):
        super(DirectAccess, self).__init__(score_file_name, score_config)
        self.file = pysam.Tabixfile(score_file_name)

    def _fetch(self, chrom, pos_begin, pos_end):
        return self.file.fetch(
            chrom, pos_begin-1, pos_end, parser=pysam.asTuple())


class ScoreAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(ScoreAnnotator, self).__init__(opts, header)
        self.labels = opts.labels.split(',') if opts.labels else None
        self._init_score_file()
        if opts.search_columns is not None and opts.search_columns != '':
            self.search_columns = opts.search_columns.split(',')
        else:
            self.search_columns = []
        self._init_cols()

    def _init_cols(self):
        opts = self.opts
        header = self.header
        if opts.x is None and opts.c is None:
            opts.x = "location"

        chr_col = assign_values(opts.c, header)
        pos_col = assign_values(opts.p, header)
        loc_col = assign_values(opts.x, header)

        self.arg_columns = [chr_col, pos_col, loc_col] + \
            [assign_values(col, header) for col in self.search_columns]

    def _init_score_file(self):
        if not self.opts.scores_file:
            print("You should provide a score file location.", file=sys.stderr)
            sys.exit(1)

        if self.opts.direct:
            self.file = DirectAccess(
                self.opts.scores_file,
                self.opts.scores_config_file)
        else:
            self.file = IterativeAccess(
                self.opts.scores_file,
                self.opts.scores_config_file,
                self.opts.region)

        self.header.extend(self.labels if self.labels
                           else self.file.config.columns.score)

    @property
    def new_columns(self):
        return self.file.config.columns.score

    def _get_scores(self, new_columns, chr=None, pos=None, loc=None, *args):
        if loc is not None:
            chr, pos = loc.split(':')
        if chr != '':
            return [normalize_value(score)
                    for score
                    in self.file.get_scores(new_columns, chr, int(pos), *args)]
        else:
            return [None for col in new_columns]

    def line_annotations(self, line, new_columns):
        params = [
            line[i-1] if i is not None else None for i in self.arg_columns
        ]
        return self._get_scores(new_columns, *params)


if __name__ == "__main__":
    main(get_argument_parser(), ScoreAnnotator)
