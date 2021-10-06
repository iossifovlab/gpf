import os
import sys
import pysam

from urllib.parse import urlparse

from dae.genomic_resources.resources import GenomicResource
from dae.annotation.tools.utils import is_gzip, regions_intersect


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
        scores_filename = self._url + "/" + self._config.filename
        index_filename = self._url + "/" + self._config.index_file.filename
        if urlparse(self._url).scheme == "file":
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
            lines = list(self.infile.fetch(
                f"{chrom}:{pos_begin}", parser=pysam.asTuple()
            ))
            self._lines_iterator = list(map(
                self._parse_line,
                lines
            ))

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

    def get_default_scores(self):
        return [s.source for s in self._config.default_annotation.attributes]

    def get_default_annotation(self):
        return self._config.default_annotation
