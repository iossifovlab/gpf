import sys
import os
import logging

import pysam
import numpy as np
import pandas as pd
from collections import defaultdict

from dae.annotation.tools.utils import AnnotatorFactory, \
    handle_chrom_prefix, is_gzip, is_tabix, regions_intersect

logger = logging.getLogger(__name__)


class ScoreFile:

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def __init__(self, config):

        self.config = config
        self.filename = config.filename
        self.tabix_filename = config.index_file.filename
        self.separator = "\t" if config.separator is None else config.separator
        self.buffer = []
        self.last_pos = 0

        assert os.path.exists(self.filename)
        assert os.path.exists(self.tabix_filename)
        assert is_gzip(self.filename)
        assert is_tabix(self.tabix_filename)

        required_columns = AnnotatorFactory.name_to_class(
            self.config.score_type
        ).required_columns

        file_columns = {rc: self.config[rc] for rc in required_columns}
        file_columns = file_columns.update({
            sc.id: sc for sc in self.config.scores
        })

        self._setup()

        if self.config.has_header:
            header = self.header
            col_indexes = dict()
            for col_name, desc in file_columns:
                col_indexes[col_name] = header.index(desc.name)
        else:
            col_indexes = {
                k: file_columns[k].index for k in file_columns.keys()
            }

        self.col_indexes = col_indexes

    @property
    def _chrom_idx(self):
        return self.col_indexes["chrom"]

    @property
    def _pos_begin_idx(self):
        return self.col_indexes["pos_begin"]

    @property
    def _pos_end_idx(self):
        return self.col_indexes["pos_end"]

    @property
    def _buffer_chrom(self):
        if len(self.buffer) == 0:
            return None

        return self.buffer[0][self._chrom_idx]

    @property
    def _buffer_pos_begin(self):
        if len(self.buffer) == 0:
            return -1

        return self.buffer[0][self._pos_begin_idx]

    @property
    def _buffer_pos_end(self):
        if len(self.buffer) == 0:
            return -1

        return self.buffer[0][self._pos_end_idx]

    def fetch_lines(self, chrom, pos_begin, pos_end):
        self.last_pos = pos_end
        if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
            return self._fetch_direct(chrom, pos_begin, pos_end)
        return self._fetch_sequential(chrom, pos_begin, pos_end)

    def close(self):
        self.infile.close()
        self.direct_infile.close()

    def _parse_line(self, line):
        return {
            col: line[idx] for col, idx in self.col_indexes
        }

    def _setup(self):
        self.infile = pysam.TabixFile(self.filename, index=self.tabix_filename)
        self.direct_infile = pysam.TabixFile(
            self.filename,
            index=self.tabix_filename
        )
        contig_name = self.infile.contigs[-1]
        self._has_chrom_prefix = contig_name.startswith("chr")
        self._lines_iterator = self.infile.fetch(parser=pysam.asTuple())

    @property
    def header(self):
        return self.infile.header.strip("#").split(self.separator)

    def _purge_buffer(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while len(self.buffer) > 0:
            line = self.buffer[0]
            if (
                line[self._chrom_idx] == chrom and
                line[self._pos_end_idx] >= pos_begin
            ):
                break
            self.buffer.pop(0)

    def _fill_buffer(self, chrom, pos_begin, pos_end):
        if self._buffer_chrom == chrom and self._buffer_pos_end > pos_end:
            return
        if self._lines_iterator is None:
            return

        line = None
        for line in self._lines_iterator:
            if line[self._pos_end_idx] >= pos_begin:
                break

        if not line:
            return

        self.buffer.append(line)

        for line in self._lines_iterator:
            chrom = line[self._chrom_idx]
            assert chrom == self._buffer_chrom, (chrom, self._buffer_chrom)
            self.buffer.append(line)
            if line[self._pos_end_idx] > pos_end:
                break

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if (
            chrom != self._buffer_chrom
            or pos_begin < self._buffer_pos_begin
            or (pos_begin - self._buffer_pos_end) > self.LONG_JUMP_THRESHOLD
        ):
            self.buffer = list()
            self._lines_iterator = self.infile.fetch(
                f"{chrom}:{pos_begin}", parser=pysam.asTuple()
            )

        if self._lines_iterator is None:
            return []

        self._purge_buffer(chrom, pos_begin, pos_end)
        self._fill_buffer(chrom, pos_begin, pos_end)
        return self._select_lines(chrom, pos_begin, pos_end)

    def _select_lines(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.buffer:
            if line[self._chrom_idx] != chrom:
                continue
            if regions_intersect(
                pos_begin, pos_end,
                line[self._pos_begin_idx], line[self._pos_end_idx]
            ):
                result.append(self._parse_line(line))
        return result

    def _fetch_direct(self, chrom, pos_begin, pos_end):
        try:
            result = []
            for line in self.direct_infile.fetch(
                str(chrom), pos_begin - 1, pos_end, parser=pysam.asTuple()
            ):
                result.append(self._parse_line(line))
            return result
        except ValueError as ex:
            print(
                f"could not find region {chrom}:{pos_begin}-{pos_end} "
                f"in {self.filename}: ",
                ex,
                file=sys.stderr,
            )
            return []

    def fetch_scores_df(self, chrom, pos_begin, pos_end):
        scores = self.fetch_scores(chrom, pos_begin, pos_end)
        return self.scores_to_dataframe(scores)

    def scores_to_dataframe(self, scores):
        df = pd.DataFrame(scores)
        for score in self.config.scores:
            score_id = score.id
            df[score_id] = df[score_id].replace(["NA"], np.nan)
            df[score_id] = df[score_id].astype("float32")
        return df

    def fetch_scores_iterator(self, chrom, pos_begin, pos_end):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        for line in self.fetch_lines(chrom, pos_begin, pos_end):
            yield line

    def fetch_scores(self, chrom, pos_begin, pos_end):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        score_lines = self.fetch_lines(chrom, pos_begin, pos_end)
        logger.debug(f"score lines found: {score_lines}")
        result = defaultdict(list)

        for line in score_lines:
            logger.debug(
                f"pos_end: {pos_end}; line.pos_end: {line.get(pos_end)}; "
                f"pos_begin: {pos_begin}; "
                f"line.pos_begin: {line.get(pos_begin)}"
            )
            count = (
                min(pos_end, line.get(pos_end)) -
                max(line.get(pos_begin), pos_begin) + 1
            )
            if count <= 0:
                continue

            assert count >= 1, count
            result["COUNT"].append(count)
            for col, val in line:
                result[col].append(val)
        logger.debug(f"fetch scores: {result}")
        return result

    def fetch_highest_scores(self, chrom, pos_begin, pos_end):
        result = dict()
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        for line in self._fetch_direct(chrom, pos_begin - 1, pos_end):
            for score in self.config.scores:
                score_id = score.id
                score_value = float(line[score_id]) \
                    if line.get(score_id) not in (None, "") else None
                result[score_id] = max(
                    score_value, result.get(score_id, np.nan))
        return result
