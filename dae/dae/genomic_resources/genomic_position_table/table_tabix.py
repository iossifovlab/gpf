import logging
from typing import Optional, Tuple, List, Union
from copy import copy
from collections import Counter
# pylint: disable=no-member
import pysam  # type: ignore

from dae.genomic_resources.repository import GenomicResource
from .table import GenomicPositionTable
from .line import Line, LineBuffer


PysamFile = Union[pysam.TabixFile, pysam.VariantFile]
logger = logging.getLogger(__name__)


class TabixGenomicPositionTable(GenomicPositionTable):
    """Represents Tabix file genome position table."""

    BUFFER_MAXSIZE = 20_000

    def __init__(self, genomic_resource: GenomicResource, table_definition):
        super().__init__(genomic_resource, table_definition)
        self.jump_threshold: int = 2_500
        if "jump_threshold" in self.definition:
            threshold = self.definition["jump_threshold"]
            if threshold == "none":
                self.jump_threshold = 0
            else:
                self.jump_threshold = int(threshold)

        self.jump_threshold = min(
            self.jump_threshold, self.BUFFER_MAXSIZE // 2)

        self._last_call: Tuple[str, int, Optional[int]] = "", -1, -1
        self.buffer = LineBuffer()
        self.stats: Counter = Counter()
        # pylint: disable=no-member
        self.variants_file: Optional[PysamFile] = None
        self.line_iterator = None

    def _open_variants_file(self):
        return self.genomic_resource.open_tabix_file(self.definition.filename)

    def open(self):
        self.variants_file = self._open_variants_file()
        if self.header_mode == "file":
            self.header = self._get_header()
        self._set_special_column_indexes()
        self._build_chrom_mapping()

    def _get_header(self):
        assert isinstance(self.variants_file, pysam.TabixFile)
        return tuple(self.variants_file.header[-1].strip("#").split("\t"))

    def get_file_chromosomes(self) -> List[str]:
        assert isinstance(self.variants_file, pysam.TabixFile)
        return self.variants_file.contigs

    def _map_file_chrom(self, chrom: str) -> str:
        """Transfrom chromosome name to the chromosomes from score file."""
        if self.chrom_map:
            return self.chrom_map[chrom]
        return chrom

    def _map_result_chrom(self, chrom: str) -> str:
        """Transfroms chromosome from score file to the genome chromosomes."""
        if self.rev_chrom_map:
            return self.rev_chrom_map[chrom]
        return chrom

    def _transform_result(self, line: Line) -> Line:
        rchrom = self._map_result_chrom(line.chrom)
        if rchrom is None:
            return None
        line_copy = copy(line)
        line_copy.chrom = rchrom
        return line_copy

    def get_all_records(self):
        # pylint: disable=no-member
        for line in self.get_line_iterator():
            if self.rev_chrom_map:
                if line.chrom in self.rev_chrom_map:
                    yield self._transform_result(line)
                else:
                    continue
            else:
                yield line

    def _should_use_sequential_seek_forward(self, chrom, pos) -> bool:
        """Determine if sequentially seeking forward is appropriate.

        Determine whether to use sequential access or jump-ahead
        optimization for a given chromosome and position. Sequential access is
        used if the position is on the same chromosome and the distance between
        it and the last line in the buffer is less than the jump threshold.
        """
        if self.jump_threshold == 0:
            return False

        assert chrom is not None
        if len(self.buffer) == 0:
            return False

        last_chrom, _last_begin, last_end, *_ = self.buffer.peek_last()
        if chrom != last_chrom:
            return False
        if pos < last_end:
            return False

        if pos - last_end >= self.jump_threshold:
            return False
        return True

    def _sequential_seek_forward(self, chrom, pos):
        """Advance the buffer forward to the given position."""
        assert len(self.buffer) > 0
        assert self.jump_threshold > 0

        last_chrom, last_begin, last_end, *_ = self.buffer.peek_last()
        assert chrom == last_chrom
        assert pos >= last_begin

        self.stats["sequential seek forward"] += 1

        for row in self._gen_from_tabix(chrom, pos, buffering=True):
            last_chrom, last_begin, last_end, *_ = row
        return bool(pos >= last_end)

    def _gen_from_tabix(self, chrom, pos, buffering=True):
        try:
            assert self.line_iterator is not None
            while True:
                line = next(self.line_iterator)

                if buffering:
                    self.buffer.append(line)

                if line.chrom != chrom:
                    return
                if pos is not None and line.pos_begin > pos:
                    return
                result = self._transform_result(line)
                self.stats["yield from tabix"] += 1
                if result:
                    yield result
        except StopIteration:
            pass

    def _gen_from_buffer_and_tabix(self, chrom, beg, end):
        for line in self.buffer.fetch(chrom, beg, end):
            self.stats["yield from buffer"] += 1
            result = self._transform_result(line)
            if result:
                yield result
        _, _last_beg, last_end, *_ = self.buffer.peek_last()
        if end < last_end:
            return

        yield from self._gen_from_tabix(chrom, end, buffering=True)

    def get_records_in_region(
        self, chrom: str,
        pos_begin: Optional[int] = None,
        pos_end: Optional[int] = None
    ):
        self.stats["calls"] += 1

        if chrom not in self.get_chromosomes():
            logger.error(
                "chromosome %s not found in the tabix file "
                "from %s; %s",
                chrom, self.genomic_resource.resource_id, self.definition)
            raise ValueError(
                f"The chromosome {chrom} is not part of the table.")

        fchrom = self._map_file_chrom(chrom)
        buffering = True
        if pos_begin is None:
            pos_begin = 1
        if pos_end is None or pos_end - pos_begin > self.BUFFER_MAXSIZE:
            buffering = False
            self.stats["without buffering"] += 1
        else:
            self.stats["with buffering"] += 1

        prev_call_chrom, _prev_call_beg, prev_call_end = self._last_call
        self._last_call = fchrom, pos_begin, pos_end

        if buffering and len(self.buffer) > 0 and prev_call_chrom == fchrom:

            first_chrom, first_beg, _first_end, *_ = self.buffer.peek_first()
            if first_chrom == fchrom and prev_call_end is not None \
                    and pos_begin > prev_call_end and pos_end < first_beg:

                assert first_chrom == prev_call_chrom
                self.stats["not found"] += 1
                return

            if self.buffer.contains(fchrom, pos_begin):
                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    self.stats["yield from buffer and tabix"] += 1
                    yield row

                self.buffer.prune(fchrom, pos_begin)
                return

            if self._should_use_sequential_seek_forward(fchrom, pos_begin):
                self._sequential_seek_forward(fchrom, pos_begin)

                for row in self._gen_from_buffer_and_tabix(
                        fchrom, pos_begin, pos_end):
                    yield row

                self.buffer.prune(fchrom, pos_begin)
                return

        # without using buffer
        self.line_iterator = self.get_line_iterator(fchrom, pos_begin - 1)

        for row in self._gen_from_tabix(fchrom, pos_end, buffering=buffering):
            yield row

        self.buffer.prune(fchrom, pos_begin)

    def get_line_iterator(self, chrom=None, pos_begin=None):
        """Extract raw lines and wrap them in our Line adapter."""
        assert isinstance(self.variants_file, pysam.TabixFile)

        self.stats["tabix fetch"] += 1
        self.buffer.clear()

        other_indices, other_columns = self._get_other_columns()

        # Yes, the argument for the chromosome/contig is called "reference".
        for raw in self.variants_file.fetch(
            reference=chrom, start=pos_begin, parser=pysam.asTuple()
        ):
            if other_indices and other_columns:
                attributes = dict(
                    zip(other_columns, (raw[i] for i in other_indices))
                )
            else:
                attributes = {str(idx): value for idx, value in enumerate(raw)
                              if idx not in (self.chrom_column_i,
                                             self.pos_begin_column_i,
                                             self.pos_end_column_i)}
            ref = attributes.get(self.ref_key)
            alt = attributes.get(self.alt_key)
            yield Line(
                raw[self.chrom_column_i],
                raw[self.pos_begin_column_i],
                raw[self.pos_end_column_i],
                attributes, self.score_definitions,
                ref=ref, alt=alt,
            )

    def close(self):
        if self.variants_file is not None:
            self.variants_file.close()