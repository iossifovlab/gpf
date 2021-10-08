import os
import sys
import pysam
import logging

from copy import deepcopy
from typing import List

from urllib.parse import urlparse

from dae.genomic_resources.resources import GenomicResource
from dae.annotation.tools.utils import is_gzip, regions_intersect, \
    handle_chrom_prefix
from dae.configuration.schemas.genomic_resources_database import attr_schema, \
    genomic_score_schema

logger = logging.getLogger(__name__)


class ScoreLine:
    def __init__(self, values: dict, score_ids: list):
        self.values = values
        self.scores = {
            score_id: float(self.values[score_id])
            if self.values[score_id] not in (None, "") else None
            for score_id in score_ids
        }

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __repr__(self):
        return f"{self.chrom}:{self.pos_begin}-{self.pos_end} {self.scores}"

    @property
    def chrom(self):
        return self.values["chrom"]

    @property
    def pos_begin(self):
        return int(self.values["pos_begin"])

    @property
    def pos_end(self):
        if "pos_end" not in self.values:
            return self.pos_begin
        return int(self.values["pos_end"])


class GenomicScoresResource(GenomicResource):

    LONG_JUMP_THRESHOLD = 5000
    ACCESS_SWITCH_THRESHOLD = 1500

    def open(self):
        scores_filename = f"{self.get_url()}/{self._config.filename}"
        self.filename = scores_filename  # Kept for legacy try catch code
        index_filename = f"{self.get_url()}/{self._config.index_file.filename}"
        if urlparse(self.get_url()).scheme == "file":
            scores_filename = urlparse(scores_filename).path
            index_filename = urlparse(index_filename).path
            assert os.path.exists(scores_filename), scores_filename
            assert os.path.exists(index_filename), index_filename
            assert is_gzip(scores_filename)
        self.infile = self.tabix_access(scores_filename, index_filename)
        self.direct_infile = self.tabix_access(scores_filename, index_filename)
        self.separator = "\t" if self._config.separator is None \
            else self._config.separator
        self.buffer = []
        self.last_pos = 0

        file_columns = {rc: self._config[rc] for rc in self.required_columns()}
        file_columns.update({
            sc.id: sc for sc in self._config.scores
        })

        contig_name = self.infile.contigs[-1]
        self._has_chrom_prefix = contig_name.startswith("chr")
        self._lines_iterator = map(
            self._parse_line, self.infile.fetch(parser=pysam.asTuple())
        )

        if self._config.has_header:
            header = self._get_header()
            col_indexes = dict()
            for col_name, desc in file_columns.items():
                if desc is not None:
                    col_indexes[col_name] = header.index(desc.name)
        else:
            col_indexes = {
                k: file_columns[k].index for k in file_columns.keys()
            }

        self.col_indexes = col_indexes

    def close(self):
        self.infile.close()
        self.direct_infile.close()

    @classmethod
    def required_columns(cls):
        raise NotImplementedError

    @classmethod
    def get_config_schema(cls):
        cols = cls.required_columns()
        attributes_schemas = {
            attr_name: attr_schema for attr_name in cols
        }
        schema = deepcopy(genomic_score_schema)
        schema.update(attributes_schemas)
        return schema

    @property
    def _buffer_chrom(self):
        if len(self.buffer) == 0:
            return None

        return self.buffer[0].chrom

    @property
    def _buffer_pos_begin(self):
        if len(self.buffer) == 0:
            return -1
        return self.buffer[0].pos_begin

    @property
    def _buffer_pos_end(self):
        if len(self.buffer) == 0:
            return -1
        return self.buffer[0].pos_end

    def _get_header(self):
        return self.infile.header[-1].strip("#").split(self.separator)

    def _parse_line(self, line):
        return ScoreLine({
            col: line[idx] for col, idx in self.col_indexes.items()
        }, self.get_all_scores())

    def _purge_buffer(self, chrom, pos_begin, pos_end):
        # purge start of line buffer
        while len(self.buffer) > 0:
            line = self.buffer[0]
            if line.chrom == chrom and line.pos_end >= pos_begin:
                break
            self.buffer.pop(0)

    def _fill_buffer(self, chrom, pos_begin, pos_end):
        if self._buffer_chrom == chrom and self._buffer_pos_end > pos_end:
            return
        if self._lines_iterator is None:
            return

        line = None
        for line in self._lines_iterator:
            if line.pos_end >= pos_begin:
                break

        if not line:
            return

        self.buffer.append(line)

        for line in self._lines_iterator:
            assert line.chrom == self._buffer_chrom, \
                (line.chrom, self._buffer_chrom)
            self.buffer.append(line)
            if line.pos_end > pos_end:
                break

    def _fetch_lines(self, chrom, pos_begin, pos_end):
        self.last_pos = pos_end
        if abs(pos_begin - self.last_pos) > self.ACCESS_SWITCH_THRESHOLD:
            return self._fetch_direct(chrom, pos_begin, pos_end)
        return self._fetch_sequential(chrom, pos_begin, pos_end)

    def _fetch_sequential(self, chrom, pos_begin, pos_end):
        if (
            chrom != self._buffer_chrom
            or pos_begin < self._buffer_pos_begin
            or (pos_begin - self._buffer_pos_end) > self.LONG_JUMP_THRESHOLD
        ):
            self.buffer = list()
            lines = self.infile.fetch(
                f"{chrom}:{pos_begin}", parser=pysam.asTuple()
            )
            self._lines_iterator = map(
                self._parse_line,
                lines
            )

        if self._lines_iterator is None:
            return []

        self._purge_buffer(chrom, pos_begin, pos_end)
        self._fill_buffer(chrom, pos_begin, pos_end)
        return self._select_lines(chrom, pos_begin, pos_end)

    def _select_lines(self, chrom, pos_begin, pos_end):
        result = []
        for line in self.buffer:
            if line.chrom != chrom:
                continue
            if regions_intersect(
                pos_begin, pos_end, line.pos_begin, line.pos_end
            ):
                result.append(line)
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

    def get_all_chromosomes(self):
        return self.infile.contigs

    def get_all_scores(self):
        return [s.id for s in self._config.scores]

    def get_score_config(self, score_id):
        for config in self._config.scores:
            if config.id == score_id:
                return config

    def get_default_scores(self):
        return [s.source for s in self._config.default_annotation.attributes]

    def get_default_annotation(self):
        return self._config.default_annotation

    def get_score_default_annotation(self, score_id):
        for conf in self._config.default_annotation.attributes:
            if conf.source == score_id:
                return conf
        return None


class PositionScoreResource(GenomicScoresResource):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end")

    def fetch_scores(
        self, chrom: str, position: int, scores: List[str] = None
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()

        line = self._fetch_lines(chrom, position, position)
        if not line:
            return None

        result = dict()

        for col, val in line[0].scores.items():
            if scores is None or col in scores:
                result[col] = val

        return result

    def fetch_scores_agg(
        self, chrom: str, pos_begin: int, pos_end: int, scores_aggregators
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()
        score_lines = self._fetch_lines(chrom, pos_begin, pos_end)
        logger.debug(f"score lines found: {score_lines}")

        aggregators = {
            score_id: aggregator_type()
            for score_id, aggregator_type
            in scores_aggregators.items()
        }

        for line in score_lines:
            logger.debug(
                f"pos_end: {pos_end}; line.pos_end: {line.pos_end}; "
                f"pos_begin: {pos_begin}; line.pos_begin: {line.pos_begin}"
            )

            for col, val in line.scores.items():
                if col not in aggregators:
                    continue
                left = (
                    pos_begin
                    if pos_begin >= line.pos_begin
                    else line.pos_begin
                )
                right = (
                    pos_end
                    if pos_end <= line.pos_end
                    else line.pos_end
                )
                for i in range(left, right+1):
                    aggregators[col].add(val)

        return {
            score_id: aggregator.get_final()
            for score_id, aggregator
            in aggregators.items()
        }


class NPScoreResource(PositionScoreResource):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end", "reference", "alternative")

    def fetch_scores(
        self, chrom: str, position: int, ref: str, alt: str,
        scores: List[str] = None
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()

        lines = self._fetch_lines(chrom, position, position)
        if not lines:
            return None

        line = None
        for li in lines:
            if li["reference"] == ref and li["alternative"] == alt:
                line = li
                break

        if not line:
            return None

        result = dict()

        for col, val in line.scores.items():
            if scores is None or col in scores:
                result[col] = val

        return result

    def fetch_scores_agg(
        self, chrom: str, pos_begin: int, pos_end: int, scores_aggregators
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()
        score_lines = self._fetch_lines(chrom, pos_begin, pos_end)
        logger.debug(f"score lines found: {score_lines}")

        pos_aggregators = {
            score_id: aggregator_types[0]()
            for score_id, aggregator_types
            in scores_aggregators.items()
        }

        nuc_aggregators = {
            score_id: aggregator_types[1]()
            for score_id, aggregator_types
            in scores_aggregators.items()
        }

        if not score_lines:
            return None

        def aggregate_nucleotides():
            for col, nuc_agg in nuc_aggregators.items():
                pos_aggregators[col].add(nuc_agg.get_final())
                nuc_agg.clear()

        last_pos: int = score_lines[0].pos_begin
        for line in score_lines:
            if line.pos_begin != last_pos:
                aggregate_nucleotides()
            for col, val in line.scores.items():
                if col not in nuc_aggregators:
                    continue
                left = (
                    pos_begin
                    if pos_begin >= line.pos_begin
                    else line.pos_begin
                )
                right = (
                    pos_end
                    if pos_end <= line.pos_end
                    else line.pos_end
                )
                for i in range(left, right+1):
                    nuc_aggregators[col].add(val)
            last_pos = line.pos_begin
        aggregate_nucleotides()

        return {
            score_id: aggregator.get_final()
            for score_id, aggregator
            in pos_aggregators.items()
        }


class AlleleScoreResource(GenomicScoresResource):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end", "variant")

    def fetch_scores(
        self, chrom: str, position: int, variant: str, scores: List[str] = None
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()

        lines = self._fetch_lines(chrom, position, position)
        if not lines:
            return None

        line = None
        for li in lines:
            if li["variant"] == variant:
                line = li
                break

        if line is None:
            return None

        result = dict()

        for col, val in line.scores.items():
            if scores is None or col in scores:
                result[col] = val

        return result
