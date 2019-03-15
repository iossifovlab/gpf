#!/usr/bin/env python

from __future__ import print_function, absolute_import
# from builtins import str
import sys
import os

import pysam
import numpy as np
import pandas as pd
from collections import defaultdict
from configparser import ConfigParser
from box import Box

from annotation.tools.annotator_config import LineConfig
from annotation.tools.file_io_tsv import TabixReader
from annotation.tools.schema import Schema


def conf_to_dict(path):
    conf_parser = ConfigParser()
    conf_parser.optionxform = str
    conf_parser.read_file(path)

    assert 'general' in conf_parser
    assert 'columns' in conf_parser
    assert 'schema' in conf_parser
    conf_settings = dict(conf_parser.items('general'))
    conf_settings['columns'] = dict(conf_parser.items('columns'))
    conf_settings['schema'] = \
        Schema.from_dict(dict(conf_parser.items('schema')))
    return conf_settings


class ScoreFile(TabixReader):

    def __init__(
            self, options, score_filename, config_filename=None,
            score_config=None):

        super(ScoreFile, self).__init__(options, filename=score_filename)

        self.score_filename = score_filename
        # self.config_filename = config_filename
        if score_config is None:
            self._load_config(config_filename)
        else:
            self._setup_config(score_config)

    def _setup(self):
        super(ScoreFile, self)._setup()

        self.schema = Schema()
        for col in self.config.header:
            assert col in self.config.schema.columns, [
                self.score_filename, col, self.config.schema.columns,
            ]
            self.schema.columns[col] = self.config.schema.columns[col]
        assert all([sn in self.schema.col_names for sn in self.score_names]), \
            [self.score_filename, self.score_names, self.schema.col_names]
        self.options.update(self.config)

        self.line_config = LineConfig(self.schema.col_names)

        self.chr_name = self.config.columns.chr
        self.pos_begin_name = self.config.columns.pos_begin
        self.pos_end_name = self.config.columns.pos_end
        self.ref_name = self.config.columns.ref
        self.alt_name = self.config.columns.alt

        self.chr_index = self.schema.col_names.index(self.chr_name)
        self.pos_begin_index = self.schema.col_names.index(self.pos_begin_name)
        self.pos_end_index = self.schema.col_names.index(self.pos_end_name)

        self.no_score_value = self.config.noScoreValue

    def _load_config(self, config_filename=None):
        if config_filename is None:
            config_filename = "{}.conf".format(self.filename)
        assert os.path.exists(config_filename)

        with open(config_filename, 'r') as conf_file:
            conf_settings = conf_to_dict(conf_file)
            score_config = Box(
                conf_settings, default_box=True,
                default_box_attr=None)
            self._setup_config(score_config)

    def _setup_config(self, score_config):
        self.config = score_config

        if self.config.header:
            self.config.header = self.config.header.split(',')
        else:
            print('ERROR: Missing header in score {} config.'
                  .format(self.filename),
                  file=sys.stderr)
            sys.exit(-1)

        if self.config.columns.pos_end is None:
            self.config.columns.pos_end = self.config.columns.pos_begin

        self.config.columns.score = self.config.columns.score.split(',')
        self.score_names = self.config.columns.score

    def _fetch(self, chrom, pos_begin, pos_end):
        raise NotImplementedError()

    def fetch_scores_df(self, chrom, pos_begin, pos_end):
        scores = self.fetch_scores(chrom, pos_begin, pos_end)
        return self.scores_to_dataframe(scores)

    def scores_to_dataframe(self, scores):
        df = pd.DataFrame(scores)
        for score_name in self.score_names:
            df[score_name] = df[score_name].replace(['NA'], np.nan)
            df[score_name] = df[score_name].astype("float32")
        return df

    def fetch_scores(self, chrom, pos_begin, pos_end):
        stripped_chrom = self._handle_chrom_prefix(chrom)

        score_lines = self._fetch(stripped_chrom, pos_begin, pos_end)
        result = defaultdict(list)
        for line in score_lines:
            count = min(pos_end, line.pos_end) - \
                max(line.pos_begin, pos_begin) + 1
            assert count >= 1
            result["COUNT"].append(count)
            for index, column in enumerate(self.schema.col_names):
                result[column].append(line[index])
        return result


class LineAdapter(object):
    def __init__(self, score_file, line):
        self.score_file = score_file
        self.line = list(line)

        self.line[self.score_file.pos_begin_index] = int(self.pos_begin)
        self.line[self.score_file.pos_end_index] = int(self.pos_end)

    @property
    def pos_begin(self):
        return self.line[self.score_file.pos_begin_index]

    @property
    def pos_end(self):
        return self.line[self.score_file.pos_end_index]

    @property
    def chrom(self):
        return self.line[self.score_file.chr_index]

    def __getitem__(self, index):
        return self.line[index]

    def __len__(self):
        return len(self.line)


class NoLine(object):
    def __init__(self, score_file):
        self.score_file = score_file
        self.pos_begin = -1
        self.pos_end = -1
        self.chrom = None

    def __getitem__(self, index):
        return self.score_file.no_score_value


class LineBufferAdapter(object):

    def __init__(self, score_file):
        self.score_file = score_file
        self.buffer = []
        self.no_line = NoLine(score_file)

    def __len__(self):
        return len(self.buffer)

    def __iter__(self):
        return iter(self.buffer)

    def append(self, line):
        self.buffer.append(line)

    def reset(self):
        self.buffer = []

    def pop(self):
        return self.buffer.pop(0)

    def empty(self):
        return len(self.buffer) == 0

    def front(self):
        if self.empty():
            return self.no_line
        return self.buffer[0]

    def back(self):
        if self.empty():
            return self.no_line
        return self.buffer[-1]

    @property
    def chrom(self):
        return self.front().chrom

    @property
    def pos_begin(self):
        return self.front().pos_begin

    @property
    def pos_end(self):
        return self.back().pos_end

    def purge(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while not self.empty():
            line = self.front()
            if line.chrom == chrom and line.pos_end >= pos_begin:
                break
            self.pop()

    def fill(self, chrom, pos_begin, pos_end):
        if self.chrom == chrom and \
                self.pos_end > pos_end:
            return
        if self.score_file.lines_iterator is None:
            return
        line = None
        for line in self.score_file.lines_iterator:
            line = LineAdapter(self.score_file, line)
            if line.pos_end >= pos_begin:
                break

        if not line:
            return

        self.append(line)

        for line in self.score_file.lines_iterator:
            line = LineAdapter(self.score_file, line)
            assert line.chrom == self.chrom, \
                (line.chrom, self.chrom)
            self.append(line)
            if line.pos_end > pos_end:
                break

    @staticmethod
    def regions_intersect(b1, e1, b2, e2):
        if b1 >= b2 and b1 <= e2:
            return True
        if e1 >= b2 and e1 <= e2:
            return True
        if b2 >= b1 and b2 <= e1:
            return True
        if e2 >= b1 and e2 <= e1:
            return True
        return False

    def select_lines(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.buffer:
            if line.chrom != chrom:
                continue
            if self.regions_intersect(
                    pos_begin, pos_end,
                    line.pos_begin, line.pos_end):
                result.append(line)
        return result


class HybridAccess(ScoreFile):
    LONG_JUMP_THRESHOLD = 5000

    def __init__(self, options, score_filename,
                 config_filename=None, score_config=None):
        super(IterativeAccess, self).__init__(
            options, score_filename,
            config_filename=config_filename, score_config=score_config)

        self.buffer = LineBufferAdapter(self)
        self.direct_infile = pysam.TabixFile(self.filename)
        self.last_line = [None, None]

    def _reset(self, chrom, pos_begin):
        self.buffer.reset()

        region = "{}:{}".format(chrom, pos_begin)

        self._region_reset(region)

    def _fetch(self, chrom, pos_begin, pos_end):
        if self.last_line[0] is None:
            self.last_line[0] = pos_begin
        if self.last_line[1] is None:
            self.last_line[1] = pos_end

        if pos_begin - pos_end <= 1:
            if (pos_begin - self.last_line[1]) > 1500:
                self.last_line[0] = pos_begin
                self.last_line[1] = pos_end
                return self._fetch_direct(chrom, pos_begin, pos_end)
            else:
                self.last_line[0] = pos_begin
                self.last_line[1] = pos_end
                return self._fetch_sequential(chrom, pos_begin, pos_end)
        else:
            self.last_line[0] = pos_begin
            self.last_line[1] = pos_end
            return self._fetch_sequential(chrom, pos_begin, pos_end)

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if chrom != self.buffer.chrom or \
                pos_begin < self.buffer.pos_begin or \
                (pos_begin - self.buffer.pos_end) > self.LONG_JUMP_THRESHOLD:
            self._reset(chrom, pos_begin)

        if self.lines_iterator is None:
            return []

        self.buffer.purge(chrom, pos_begin, pos_end)
        self.buffer.fill(chrom, pos_begin, pos_end)
        return self.buffer.select_lines(chrom, pos_begin, pos_end)

    def _fetch_direct(self, chrom, pos_begin, pos_end):
        try:
            result = []
            chrom = str(chrom)

            for line in self.direct_infile.fetch(
                    chrom, pos_begin-1, pos_end, parser=pysam.asTuple()):
                line = LineAdapter(self, line)
                result.append(line)
            return result
        except ValueError as ex:
            print("could not find region: ", chrom, pos_begin, pos_end,
                  ex, file=sys.stderr)
            return []
