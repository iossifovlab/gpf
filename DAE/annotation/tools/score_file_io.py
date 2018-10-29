#!/usr/bin/env python

from __future__ import print_function

import sys
import os

import pysam
import pandas as pd
from collections import defaultdict
from configparser import ConfigParser
from box import Box
from annotation.tools.annotator_config import LineConfig
from annotation.tools.file_io import TabixReader, Schema


def conf_to_dict(path):
    conf_parser = ConfigParser()
    conf_parser.optionxform = str
    conf_parser.read_file(path)

    conf_settings = dict(conf_parser.items('general'))
    conf_settings['columns'] = dict(conf_parser.items('columns'))
    conf_settings['schema'] = Schema(dict(conf_parser.items('schema')))
    return conf_settings


# def normalize_value(score_value):
#     if ';' in score_value:
#         result = score_value.split(';')
#     elif ',' in score_value:
#         result = score_value.split(',')
#     else:
#         result = [score_value]
#     return [None if value in ['.', ''] else float(value)
#             for value in result]


class ScoreFile(TabixReader):

    def __init__(self, options, score_filename, config_filename=None):
        super(ScoreFile, self).__init__(options, filename=score_filename)

        self.score_filename = score_filename
        self.config_filename = config_filename

    def _setup(self):
        super(ScoreFile, self)._setup()

        self._load_config()
        self.line_config = LineConfig(self.config.header)

        self.chr_name = self.config.columns.chr
        self.pos_begin_name = self.config.columns.pos_begin
        self.pos_end_name = self.config.columns.pos_end
        self.ref_name = self.config.columns.ref
        self.alt_name = self.config.columns.alt

        self.chr_index = self.header.index(self.chr_name)
        self.pos_begin_index = self.header.index(self.pos_begin_name)
        self.pos_end_index = self.header.index(self.pos_end_name)

    def _load_config(self, config_filename=None):
        if self.config_filename is None:
            self.config_filename = "{}.conf".format(self.filename)
        assert os.path.exists(self.config_filename)

        with open(self.config_filename, 'r') as conf_file:
            conf_settings = conf_to_dict(conf_file)
            self.config = Box(
                conf_settings, default_box=True,
                default_box_attr=None)

        if self.config.header is not None:
            self.config.header = self.config.header.split(',')
            self.header = self.config.header

        if self.config.columns.pos_end is None:
            self.config.columns.pos_end = self.config.columns.pos_begin

        self.config.columns.score = self.config.columns.score.split(',')
        self.score_names = self.config.columns.score
        assert all([sn in self.header for sn in self.score_names])

    def _fetch(self, chrom, pos_begin, pos_end):
        raise NotImplementedError()

    def fetch_scores_df(self, chrom, pos_begin, pos_end):
        scores = self.fetch_scores(chrom, pos_begin, pos_end)
        return self.scores_to_dataframe(scores)

    def scores_to_dataframe(self, scores):
        df = pd.DataFrame(scores)

        for score_name in self.score_names:
            df[score_name] = df[score_name].astype("float32")
        return df

    def fetch_scores(self, chrom, pos_begin, pos_end):
        stripped_chrom = self._handle_chrom_prefix(chrom)

        score_lines = self._fetch(stripped_chrom, pos_begin, pos_end)
        result = defaultdict(list)
        for line in score_lines:
            count = line[self.pos_end_index] - \
                max(line[self.pos_begin_index], pos_begin) + 1
            assert count >= 1
            result["COUNT"].append(count)
            for index, column in enumerate(self.header):
                result[column].append(line[index])
        return result

    @property
    def schema(self):
        return self.config.schema


class IterativeAccess(ScoreFile):

    def __init__(self, options, score_filename, score_config_filename=None):
        super(IterativeAccess, self).__init__(
            options, score_filename, score_config_filename)

        self.current_lines = []
        self.current_chrom = None

    def _purge_line_buffer(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while len(self.current_lines) > 0:
            line = self.current_lines[0]
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
            if line_chrom > chrom or \
                    (line_chrom == chrom and line_pos_end >= pos_begin):
                break
            self.current_lines.pop(0)

    def _buffer_pos(self):
        if len(self.current_lines) == 0:
            return None, -1, -1
        chrom_begin, pos_begin, _ = self._line_pos(self.current_lines[0])
        chrom_end, _, pos_end = self._line_pos(self.current_lines[-1])
        assert chrom_begin == chrom_end

        return chrom_begin, pos_begin, pos_end

    def _line_pos(self, line):
        return line[self.chr_index], \
            line[self.pos_begin_index], \
            line[self.pos_end_index]

    def _fill_line_buffer(self, chrom, pos_begin, pos_end):
        buffer_chrom, buffer_pos_begin, buffer_pos_end = \
            self._buffer_pos()
        assert buffer_chrom is None or buffer_chrom == self.current_chrom

        if buffer_pos_end >= pos_end and buffer_pos_begin <= pos_begin:
            # the line buffer is full enough
            return

        for line in self.lines_iterator:
            line = list(line)

            line[self.pos_begin_index] = int(line[self.pos_begin_index])
            line[self.pos_end_index] = int(line[self.pos_end_index])

            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
            assert line_chrom == self.current_chrom

            if line_pos_end >= pos_begin:
                break

        self.current_lines.append(line)
        for line in self.lines_iterator:
            line = list(line)
            line[self.pos_begin_index] = int(line[self.pos_begin_index])
            line[self.pos_end_index] = int(line[self.pos_end_index])
            line_chrom, line_pos_begin, line_pos_end = self._line_pos(line)
            assert line_chrom == self.current_chrom
            self.current_lines.append(line)
            if line_pos_end > pos_end:
                break

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

    def _reset(self, chrom, pos_begin):
        self.current_chrom = chrom
        self.current_lines = []

        region = "{}:{}".format(chrom, pos_begin)
        self._region_reset(region)

    def _fetch(self, chrom, pos_begin, pos_end):
        if chrom != self.current_chrom:
            self._reset(chrom, pos_begin)

        self._purge_line_buffer(chrom, pos_begin, pos_end)
        self._fill_line_buffer(chrom, pos_begin, pos_end)
        return self._select_line_buffer(chrom, pos_begin, pos_end)


class DirectAccess(ScoreFile):

    def __init__(self, options, score_filename, config_filename=None):
        super(DirectAccess, self).__init__(
            options, score_filename, config_filename=None)

    def _fetch(self, chrom, pos_begin, pos_end):
        try:
            result = []
            for line in self.infile.fetch(
                    chrom, pos_begin-1, pos_end, parser=pysam.asTuple()):
                line = list(line)
                line[self.pos_begin_index] = int(line[self.pos_begin_index])
                line[self.pos_end_index] = int(line[self.pos_end_index])
                result.append(line)
            return result
        except ValueError as ex:
            print("could not find region: ", chrom, pos_begin, pos_end,
                  ex, file=sys.stderr)
            return []
