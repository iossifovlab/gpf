#!/usr/bin/env python

import sys
import os

import pysam
import numpy as np
import pandas as pd
from collections import defaultdict

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.score_file_conf import score_file_conf_schema

from dae.annotation.tools.file_io_tsv import (
    TSVFormat,
    TabixReader,
    handle_chrom_prefix,
)
from dae.annotation.tools.schema import Schema

try:
    bigwig_enabled = True
    from dae.annotation.tools.score_file_io_bigwig import BigWigAccess
except ImportError:
    bigwig_enabled = False


class LineAdapter(object):
    def __init__(self, score_file, line):
        self.line = list(line)

        self.header_len = len(score_file.header)
        self.chr_index = score_file.chr_index
        self.pos_begin_index = score_file.pos_begin_index
        self.pos_end_index = score_file.pos_end_index

        self.line[self.pos_begin_index] = int(self.line[self.pos_begin_index])
        self.line[self.pos_end_index] = int(self.line[self.pos_end_index])

    @property
    def pos_begin(self):
        return self.line[self.pos_begin_index]

    @property
    def pos_end(self):
        return self.line[self.pos_end_index]

    @property
    def chrom(self):
        return self.line[self.chr_index]

    def __getitem__(self, index):
        return self.line[index]

    def __len__(self):
        return self.header_len


class NoLine(object):
    def __init__(self, score_file):
        self.no_score_value = score_file.no_score_value
        self.pos_begin = -1
        self.pos_end = -1
        self.chrom = None

    def __getitem__(self, index):
        return self.no_score_value


class ScoreFile(object):
    def __init__(self, score_filename, config_filename=None):
        self.score_filename = score_filename
        assert os.path.exists(self.score_filename), self.score_filename

        if config_filename is None:
            config_filename = "{}.conf".format(self.score_filename)

        self.config = GPFConfigParser.load_config(
            config_filename, score_file_conf_schema
        )

        assert self.config.general.header is not None
        assert self.config.columns.score is not None
        self.header = self.config.general.header
        self.score_names = self.config.columns.score

        self.schema = Schema.from_dict(
            self.config.score_schema._asdict()
        ).order_as(self.header)

        assert all([sn in self.schema for sn in self.score_names]), [
            self.score_filename,
            self.score_names,
            self.schema.col_names,
        ]

        self.chr_index = self.schema.col_names.index(self.chr_name)
        self.pos_begin_index = self.schema.col_names.index(self.pos_begin_name)
        self.pos_end_index = self.schema.col_names.index(self.pos_end_name)

        self.chr_prefix = getattr(self.config.general, "chr_prefix", False)

        self.no_score_value = self.config.general.no_score_value or "na"
        if self.no_score_value.lower() in ("na", "none"):
            self.no_score_value = None

        self._init_access()

    def _init_access(self):
        score_format = (
            self.config.misc.format.lower() if self.config.misc else "tsv"
        )
        assert score_format in ["bedgraph", "tsv", "bigwig", "bw"], (
            score_format,
            self.config.options.scores_config_file,
        )

        if score_format == "bigwig" or score_format == "bw":
            assert bigwig_enabled, "pyBigWig module is not installed"
            self.accessor = BigWigAccess(self)
        else:
            self.accessor = TabixAccess(self)

    @property
    def chr_name(self):
        return self.config.columns.chr

    @property
    def pos_begin_name(self):
        return self.config.columns.pos_begin

    @property
    def pos_end_name(self):
        return self.config.columns.pos_end or self.pos_begin_name

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
            df[score_name] = df[score_name].replace(["NA"], np.nan)
            df[score_name] = df[score_name].astype("float32")
        return df

    def fetch_scores(self, chrom, pos_begin, pos_end):
        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        score_lines = self.accessor._fetch(stripped_chrom, pos_begin, pos_end)
        result = defaultdict(list)

        for line in score_lines:
            count = (
                min(pos_end, line.pos_end) - max(line.pos_begin, pos_begin) + 1
            )
            assert count >= 1
            result["COUNT"].append(count)
            for index, column in enumerate(self.schema.col_names):
                result[column].append(line[index])
        return result

    def fetch_highest_scores(self, chrom, pos_begin, pos_end):
        result = dict()

        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        for line in self.accessor.direct_infile.fetch(
            stripped_chrom, pos_begin - 1, pos_end, parser=pysam.asTuple()
        ):
            line = LineAdapter(self.accessor.score_file, line)
            for column in self.score_names:
                score_index = self.schema.col_names.index(column)
                score_value = float(line[score_index]) \
                    if str.lower(line[score_index]) \
                    != self.config.general.no_score_value else np.nan
                result[column] = max(score_value, result.get(column, np.nan))

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
            assert line.chrom == self.chrom, (line.chrom, self.chrom)
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
                pos_begin, pos_end, line.pos_begin, line.pos_end
            ):
                result.append(line)
        return result


class TabixAccess(TabixReader):
    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def __init__(self, score_file):
        assert TSVFormat.is_gzip(
            score_file.score_filename
        ), score_file.score_filename
        assert os.path.exists(
            "{}.tbi".format(score_file.score_filename)
        ), score_file.score_filename
        self.infile = pysam.TabixFile(score_file.score_filename)
        self.direct_infile = pysam.TabixFile(score_file.score_filename)
        self.score_file = score_file

        self.buffer = LineBufferAdapter(self.score_file, self)
        self._has_chrom_prefix = self.score_file.chr_prefix
        self.last_pos = 0

        self.filename = score_file.score_filename

    def _reset(self, chrom, pos_begin):
        self.buffer.reset()
        self._region_reset("{}:{}".format(chrom, pos_begin))

    def _fetch(self, chrom, pos_begin, pos_end):
        if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
            self.last_pos = pos_end
            return self._fetch_direct(chrom, pos_begin, pos_end)
        else:
            self.last_pos = pos_end
            return self._fetch_sequential(chrom, pos_begin, pos_end)

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if (
            chrom != self.buffer.chrom
            or pos_begin < self.buffer.pos_begin
            or (pos_begin - self.buffer.pos_end) > self.LONG_JUMP_THRESHOLD
        ):
            self._reset(chrom, pos_begin)

        if self.lines_iterator is None:
            return []

        self.buffer.purge(chrom, pos_begin, pos_end)
        self.buffer.fill(chrom, pos_begin, pos_end)
        return self.buffer.select_lines(chrom, pos_begin, pos_end)

    def _fetch_direct(self, chrom, pos_begin, pos_end):
        try:
            result = []
            for line in self.direct_infile.fetch(
                str(chrom), pos_begin - 1, pos_end, parser=pysam.asTuple()
            ):
                result.append(LineAdapter(self.score_file, line))
            return result
        except ValueError as ex:
            print(
                f"could not find region {chrom}:{pos_begin}-{pos_end} "
                f"in {self.filename}: ",
                ex,
                file=sys.stderr,
            )
            return []
