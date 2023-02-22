import logging
from typing import Optional, Tuple, List, Union
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
        self.pysam_file: Optional[PysamFile] = None
        self.line_iterator = None

    def _load_header(self):
        header_lines = []
        with self.genomic_resource.open_raw_file(
                self.definition.filename, compression="gzip") as infile:
            while True:
                line = infile.readline()
                if line[0] != "#":
                    break
                header_lines.append(line)
        assert len(header_lines) > 0
        return tuple(header_lines[-1].strip("#\n").split("\t"))

    def open(self):
        self.pysam_file = self.genomic_resource.open_tabix_file(
            self.definition.filename)
        if self.header_mode == "file":
            self.header = self._load_header()
        self._set_core_column_keys()
        self._build_chrom_mapping()
        return self

    def close(self):
        self.buffer.clear()
        if self.pysam_file is not None:
            if self.line_iterator:
                self.line_iterator.close()
            self.pysam_file.close()

        self.stats = Counter()
        self.pysam_file = None
        self.line_iterator = None

    def get_file_chromosomes(self) -> List[str]:
        assert isinstance(self.pysam_file, pysam.TabixFile)
        return self.pysam_file.contigs

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

    def _make_line(self, data):
        return Line(
            data,
            self.chrom_key,
            self.pos_begin_key, self.pos_end_key,
            self.ref_key, self.alt_key,
            self.header
        )

    def _transform_result(self, line: Line) -> Line:
        rchrom = self._map_result_chrom(line.chrom)
        if rchrom is None:
            return None
        new_data = list(line.data)
        if isinstance(self.chrom_key, int):
            chrom_idx = self.chrom_key
        else:
            chrom_idx = self.header.index(self.chrom_key)
        new_data[chrom_idx] = rchrom
        return self._make_line(tuple(new_data))

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

        last = self.buffer.peek_last()
        if chrom != last.chrom:
            return False
        if pos < last.pos_end:
            return False

        if pos - last.pos_end >= self.jump_threshold:
            return False
        return True

    def _sequential_seek_forward(self, chrom, pos):
        """Advance the buffer forward to the given position."""
        assert len(self.buffer) > 0
        assert self.jump_threshold > 0

        last = self.buffer.peek_last()
        assert chrom == last.chrom
        assert pos >= last.pos_begin

        self.stats["sequential seek forward"] += 1

        for row in self._gen_from_tabix(chrom, pos, buffering=True):
            last = row
        return bool(pos >= last.pos_end)

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
        last = self.buffer.peek_last()
        if end < last.pos_end:
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

            first = self.buffer.peek_first()
            if first.chrom == fchrom \
               and prev_call_end is not None \
               and pos_begin > prev_call_end \
               and pos_end < first.pos_begin:

                assert first.chrom == prev_call_chrom
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
        assert isinstance(self.pysam_file, pysam.TabixFile)

        self.stats["tabix fetch"] += 1
        self.buffer.clear()

        # Yes, the argument for the chromosome/contig is called "reference".
        for raw in self.pysam_file.fetch(
            reference=chrom, start=pos_begin, parser=pysam.asTuple()
        ):
            yield self._make_line(raw)
