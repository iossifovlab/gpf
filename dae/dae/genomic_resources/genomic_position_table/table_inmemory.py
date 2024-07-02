import collections
from collections.abc import Generator
from typing import IO, ClassVar, Optional

from dae.genomic_resources.repository import GenomicResource

from .line import Line, LineBase
from .table import GenomicPositionTable, get_idx, zero_based_adjust


class InmemoryGenomicPositionTable(GenomicPositionTable):
    """In-memory genomic position table."""

    FORMAT_DEF: ClassVar[dict] = {
        # parameters are <column separator>, <strip_chars>, <space replacement>
        "mem": (None, " \t\n\r", True),
        "tsv": ("\t", "\n\r", False),
        "csv": (",", "\n\r", False),
    }

    def __init__(
        self,
        genomic_resource: GenomicResource,
        table_definition: dict,
        file_format: str,
    ):
        self.format = file_format
        self.str_stream: Optional[IO] = None
        self.records_by_chr: dict[str, list[Line]] = {}
        super().__init__(genomic_resource, table_definition)

    def _make_line(self, data: tuple) -> Line:
        return Line(
            data,
            self.chrom_key,
            self.pos_begin_key, self.pos_end_key,
            self.ref_key, self.alt_key,
        )

    def open(self) -> "InmemoryGenomicPositionTable":
        compression = None
        if self.definition.filename.endswith(".gz"):
            compression = "gzip"
        self.str_stream = self.genomic_resource.open_raw_file(
            self.definition.filename, mode="rt", compression=compression)
        assert self.str_stream is not None
        clmn_sep, strip_chars, space_replacement = \
            InmemoryGenomicPositionTable.FORMAT_DEF[self.format]
        if self.header_mode == "file":
            hcs = None
            for row in self.str_stream:
                row = row.strip(strip_chars)
                if not row:
                    continue
                hcs = row.split(clmn_sep)
                break
            if not hcs:
                raise ValueError("No header found")

            self.header = tuple(hcs)
        col_number = len(self.header) if self.header else None

        self._set_core_column_keys()

        records_by_chr = collections.defaultdict(list)

        for row in self.str_stream:
            row = row.strip(strip_chars)
            if not row:
                continue
            columns = tuple(row.split(clmn_sep))
            if col_number and len(columns) != col_number:
                raise ValueError("Inconsistent number of columns")

            col_number = len(columns)
            if space_replacement:
                columns = tuple("" if v == "EMPTY" else v for v in columns)

            if self.definition.get("zero_based") is True:
                assert self.pos_begin_key is not None
                assert self.pos_end_key is not None
                assert self.header is not None
                columns = zero_based_adjust(
                    columns, self.pos_begin_key,
                    self.pos_end_key, self.header,
                )
            line = self._make_line(columns)
            records_by_chr[line.chrom].append(line)

        self.records_by_chr = {
            c: sorted(pss, key=lambda line: (line.chrom, line.pos_begin,
                                             line.pos_end, line.ref, line.alt))
            for c, pss in records_by_chr.items()
        }
        self._build_chrom_mapping()
        return self

    def get_file_chromosomes(self) -> list[str]:
        return sorted(self.records_by_chr.keys())

    def _transform_result(self, line: Line, chrom: str) -> Line:
        assert self.chrom_key is not None
        assert self.header is not None
        new_data = list(line._data)  # pylint: disable=protected-access  # noqa: SLF001
        chrom_idx = get_idx(self.chrom_key, self.header)
        new_data[chrom_idx] = chrom
        return self._make_line(tuple(new_data))

    def get_all_records(self) -> Generator[LineBase, None, None]:
        for chrom in self.get_chromosomes():
            if self.chrom_map:
                if chrom not in self.chrom_map:
                    continue
                fchrom = self.chrom_map[chrom]
                for line in self.records_by_chr[fchrom]:
                    yield self._transform_result(line, chrom)
            else:
                yield from self.records_by_chr[chrom]

    def get_records_in_region(
        self,
        chrom: str,
        pos_begin: Optional[int] = None,
        pos_end: Optional[int] = None,
    ) -> Generator[LineBase, None, None]:
        fch = self.chrom_map[chrom] if self.chrom_map else chrom
        if pos_begin is not None and self.definition.get("zero_based") is True:
            pos_begin -= 1
        if fch not in self.records_by_chr:
            raise ValueError(
                f"The chromosome {chrom} is not present in the table")

        for line in self.records_by_chr[fch]:
            if pos_begin and pos_begin > line.pos_end:
                continue
            if pos_end and pos_end < line.pos_begin:
                continue
            if self.chrom_map:
                yield self._transform_result(line, chrom)
            else:
                yield line

    def get_chromosome_length(self, chrom: str, _step: int = 0) -> int:
        if chrom not in self.get_chromosomes():
            raise ValueError(
                f"contig {chrom} not present in the table's contigs: "
                f"{self.get_chromosomes()}")
        fch = self.chrom_map[chrom] if self.chrom_map else chrom
        return max(line.pos_end for line in self.records_by_chr[fch]) + 1

    def close(self) -> None:
        if self.str_stream is not None:
            self.str_stream.close()
