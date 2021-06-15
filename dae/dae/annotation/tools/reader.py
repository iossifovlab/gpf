import sys
import os
import logging
import gzip

import pysam
import numpy as np
import pandas as pd
from collections import defaultdict

from dae.annotation.tools.schema import Schema
from dae.annotation.tools.utils import handle_header, handle_chrom_prefix, \
    AnnotatorFactory

logger = logging.getLogger(__name__)


def is_gzip(filename):
    try:
        if filename == "-":
            return False
        if not os.path.exists(filename):
            return False

        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:
        return False


def is_tabix(filename):
    if not is_gzip(filename):
        return False
    if not os.path.exists("{}.tbi".format(filename)):
        return False
    return True


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


class FileReader:
    def __init__(self):
        self.linecount = 0
        self.linecount_threshold = 1000

    def _setup(self):
        raise NotImplementedError()

    def _cleanup(self):
        raise NotImplementedError()

    def lines_read_iterator(self):
        raise NotImplementedError()

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def _progress_step(self):
        self.linecount += 1
        if self.linecount % self.linecount_threshold == 0:
            logger.log(f"{self.linecount} lines read")


class TSVReader(FileReader):
    def __init__(
        self, filename, col_order=None,
        separator=None
    ):
        super.__init__()

        self.filename = filename
        self.separator = "\t" if separator is None else separator

        assert os.path.exists(self.filename)

    def _header_read(self):
        if self.schema:
            return self.schema.col_names

        if self.col_order:
            return self.col_order

        line = self.infile.readline()
        header_str = line.strip()
        if header_str.startswith("#"):
            header_str = header_str[1:]
        return handle_header(header_str.split(self.separator))

    def _setup(self):
        if is_gzip(self.filename):
            self.infile = gzip.open(self.filename, "rt")
        else:
            self.infile = open(self.filename, "r")

        self.schema = Schema.from_dict({"str": self._header_read()})

    def _cleanup(self):
        self.infile.close()

    def line_read(self):
        line = self.infile.readline().rstrip("\n")

        if not line:
            return None
        self._progress_step()
        return line.split(self.separator)

    def lines_read_iterator(self):
        line = self.line_read()
        while line:
            yield line
            line = self.line_read()


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
        if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
            self.last_pos = pos_end
            return self._fetch_direct(chrom, pos_begin, pos_end)
        else:
            self.last_pos = pos_end
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

        self._region_reset(self.region)

    @property
    def header(self):
        return self.infile.header

    def _region_reset(self, region):
        region = handle_chrom_prefix(self._has_chrom_prefix, region)
        try:
            self._lines_iterator = self.infile.fetch(
                region=region, parser=pysam.asTuple()
            )
        except ValueError as ex:
            print(
                f"could not find region {region} in {self.filename}:",
                ex, file=sys.stderr)
            self._lines_iterator = None

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

        self.append(line)

        for line in self.access.lines_iterator:
            chrom = line[self._chrom_idx]
            assert chrom == self._buffer_chrom, (chrom, self._buffer_chrom)
            self.append(line)
            if line[self._pos_end_idx] > pos_end:
                break

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if (
            chrom != self._buffer_chrom
            or pos_begin < self._buffer_pos_begin
            or (pos_begin - self._buffer_pos_end) > self.LONG_JUMP_THRESHOLD
        ):
            self._reset(chrom, pos_begin)

        if self.lines_iterator is None:
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
        for score_name in self.score_names:
            df[score_name] = df[score_name].replace(["NA"], np.nan)
            df[score_name] = df[score_name].astype("float32")
        return df

    def fetch_scores_iterator(self, chrom, pos_begin, pos_end):
        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        for line in self.fetch_lines(stripped_chrom, pos_begin, pos_end):
            yield line

    def fetch_scores(self, chrom, pos_begin, pos_end):
        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        score_lines = self.fetch_lines(stripped_chrom, pos_begin, pos_end)
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

        stripped_chrom = handle_chrom_prefix(self.chr_prefix, chrom)

        for line in self._fetch_direct(
                stripped_chrom, pos_begin - 1, pos_end,
                parser=pysam.asTuple()):
            for score in self.config.scores:
                score_id = score.id
                score_value = float(line[score_id]) \
                    if line.get(score_id) not in (None, "") else None
                result[score_id] = max(
                    score_value, result.get(score_id, np.nan))
        return result
