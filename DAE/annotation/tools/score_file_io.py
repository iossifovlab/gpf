#!/usr/bin/env python

from __future__ import print_function, absolute_import
# from builtins import str
import sys
import os

import pysam
import numpy as np
import pandas as pd
import reusables
from collections import defaultdict
from box import ConfigBox

from annotation.tools.file_io_tsv import TSVFormat, TabixReader, \
        handle_chrom_prefix
from annotation.tools.schema import Schema
try:
    bigwig_enabled = True
    from annotation.tools.score_file_io_bigwig import BigWigAccess
except ImportError:
    bigwig_enabled = False


class LineAdapter(object):
    def __init__(self, score_file, line):
        self.line = line

        self.header = score_file.header
        self.chr_index = score_file.chr_index
        self.pos_begin_index = score_file.pos_begin_index
        self.pos_end_index = score_file.pos_end_index

    @property
    def pos_begin(self):
        return int(self.line[self.pos_begin_index])

    @property
    def pos_end(self):
        return int(self.line[self.pos_end_index])

    @property
    def chrom(self):
        return self.line[self.chr_index]

    def __getitem__(self, index):
        if index == self.pos_begin_index:
            return self.pos_begin
        elif index == self.pos_end_index:
            return self.pos_end
        else:
            return self.line[index]

    def __len__(self):
        return len(self.header)


class NoLine(LineAdapter):
    def __init__(self, score_file):
        super(NoLine, self).__init__(score_file, [])
        self.no_score_value = score_file.no_score_value

    @property
    def pos_begin(self):
        return -1

    @property
    def pos_end(self):
        return -1

    @property
    def chrom(self):
        return None

    def __getitem__(self, index):
        if index == self.pos_begin_index:
            return self.pos_begin
        if index == self.pos_end_index:
            return self.pos_end
        if index == self.chr_index:
            return self.chrom
        else:
            return self.no_score_value


class ScoreFile(object):

    def __init__(self, score_filename, config_filename=None):
        self.score_filename = score_filename
        assert os.path.exists(self.score_filename), self.score_filename

        if config_filename is None:
            config_filename = "{}.conf".format(self.score_filename)
        self.config = ConfigBox(reusables.config_dict(config_filename))
        assert 'header' in self.config.general

        self.schema = Schema.from_dict(dict(self.config.schema)) \
                            .order_as(self.header)

        assert all([sn in self.schema for sn in self.score_names]), \
            [self.score_filename, self.score_names, self.schema.col_names]

        self.chr_index = \
            self.schema.col_names.index(self.chr_name)
        self.pos_begin_index = \
            self.schema.col_names.index(self.pos_begin_name)
        self.pos_end_index = \
            self.schema.col_names.index(self.pos_end_name)

        if 'chr_prefix' in self.config.misc:
            self.chr_prefix = self.config.misc.bool('chr_prefix')
        else:
            self.chr_prefix = False

        if 'noscorevalue' in self.config.general:
            self.no_score_value = self.config.general.noscorevalue
        else:
            self.no_score_value = 'na'
        if self.no_score_value.lower() in set(['na', 'none']):
            self.no_score_value = None

        self._init_access()

    def _init_access(self):
        if 'format' in self.config.general:
            score_format = self.config.general.format.lower()
        else:
            score_format = 'tsv'
        assert score_format in ['tsv', 'bigwig'], \
            (score_format, self.config.options.scores_config_file)

        if score_format == 'bigwig':
            assert bigwig_enabled, 'pyBigWig module is not installed'
            self.accessor = BigWigAccess(self)
        else:
            self.accessor = TabixAccess(self)

    @property
    def header(self):
        return self.config.general.list('header')

    @property
    def score_names(self):
        return self.config.columns.list('score')

    @property
    def chr_name(self):
        return self.config.columns.chr

    @property
    def pos_begin_name(self):
        return self.config.columns.pos_begin

    @property
    def pos_end_name(self):
        if 'pos_end' in self.config.columns:
            return self.config.columns.pos_end
        else:
            return self.pos_begin_name

    @property
    def ref_name(self):
        return self.config.columns.ref

    @property
    def alt_name(self):
        return self.config.columns.alt

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
        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        score_lines = self.accessor._fetch(stripped_chrom, pos_begin, pos_end)
        result = defaultdict(list)
        for line in score_lines:
            count = min(pos_end, line.pos_end) - \
                    max(line.pos_begin, pos_begin) + 1
            assert count >= 1
            result["COUNT"].append(count)
            for index, column in enumerate(self.schema.col_names):
                result[column].append(line[index])
        return result


class LineBufferAdapter(object):

    def __init__(self, score_file, access):
        self.score_file = score_file
        self.access = access
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
        if self.chrom == chrom and self.pos_end > pos_end:
            return
        if self.access.lines_iterator is None:
            return

        line = None
        for line in self.access.lines_iterator:
            line = LineAdapter(self.score_file, line)
            if line.pos_end >= pos_begin:
                break

        if not line:
            return

        self.append(line)

        for line in self.access.lines_iterator:
            line = LineAdapter(self.score_file, line)
            assert line.chrom == self.chrom, \
                (line.chrom, self.chrom)
            self.append(line)
            if line.pos_end > pos_end:
                break

    @staticmethod
    def regions_intersect(b1, e1, b2, e2):
        assert b1 <= e1
        assert b2 <= e2
        if e2 < b1 or b2 > e1:
            return False
        return True

    def select_lines(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.buffer:
            line = LineAdapter(self.score_file, line)
            if line.chrom != chrom:
                continue
            if self.regions_intersect(
                    pos_begin, pos_end, line.pos_begin, line.pos_end):
                result.append(line)
        return result


class TabixAccess(TabixReader):
    LONG_JUMP_THRESHOLD = 5000

    def __init__(self, score_file):
        assert TSVFormat.is_gzip(score_file.score_filename), \
             score_file.score_filename
        assert os.path.exists("{}.tbi".format(score_file.score_filename)), \
            score_file.score_filename
        self.infile = pysam.TabixFile(score_file.score_filename)
        self.score_file = score_file

        self.buffer = LineBufferAdapter(self.score_file, self)
        self._has_chrom_prefix = self.score_file.chr_prefix
        self.last_pos = 0

    def _reset(self, chrom, pos_begin):
        self.buffer.reset()
        self._region_reset("{}:{}".format(chrom, pos_begin))

    def _fetch(self, chrom, pos_begin, pos_end):
        if pos_begin - pos_end <= 1:
            if (pos_begin - self.last_pos) > 1500:
                return self._fetch_direct(chrom, pos_begin, pos_end)
            else:
                return self._fetch_sequential(chrom, pos_begin, pos_end)
        else:
            return self._fetch_sequential(chrom, pos_begin, pos_end)

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        self.last_pos = pos_end

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
        self.last_pos = pos_end
        try:
            result = []
            for line in self.infile.fetch(
                    chrom, pos_begin-1, pos_end, parser=pysam.asTuple()):
                result.append(LineAdapter(self.score_file, line))
            return result
        except ValueError as ex:
            print("could not find region: ", chrom, pos_begin, pos_end,
                  ex, file=sys.stderr)
            return []
