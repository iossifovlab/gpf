import collections
from typing import Optional, List, Any, TextIO

from dae.genomic_resources.repository import GenomicResource
from .table import GenomicPositionTable
from .line import Line


class InmemoryGenomicPositionTable(GenomicPositionTable):
    """In-memory genomic position table."""

    FORMAT_DEF = {
        # parameters are <column separator>, <strip_chars>, <space replacement>
        "mem": (None, " \t\n\r", True),
        "tsv": ("\t", "\n\r", False),
        "csv": (",", "\n\r", False)
    }

    def __init__(
        self, genomic_resource: GenomicResource, table_definition, fileformat
    ):
        self.format = fileformat
        self.str_stream: Optional[TextIO] = None
        self.records_by_chr: dict[str, Any] = {}
        super().__init__(genomic_resource, table_definition)

    def _make_line(self, data):
        return Line(
            data,
            self.chrom_key,
            self.pos_begin_key, self.pos_end_key,
            self.ref_key, self.alt_key,
            self.header
        )

    def open(self):
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
            for line in self.str_stream:
                line = line.strip(strip_chars)
                if not line:
                    continue
                hcs = line.split(clmn_sep)
                break
            if not hcs:
                raise ValueError("No header found")

            self.header = tuple(hcs)
        col_number = len(self.header) if self.header else None

        self._set_core_column_keys()

        records_by_chr = collections.defaultdict(list)

        for line in self.str_stream:
            line = line.strip(strip_chars)
            if not line:
                continue
            columns = tuple(line.split(clmn_sep))
            if col_number and len(columns) != col_number:
                raise ValueError("Inconsistent number of columns")

            col_number = len(columns)
            if space_replacement:
                columns = tuple("" if v == "EMPTY" else v for v in columns)

            line = self._make_line(columns)
            records_by_chr[line.chrom].append(line)

        self.records_by_chr = {
            c: sorted(pss, key=lambda l: (l.chrom, l.pos_begin, l.pos_end,
                                          l.ref, l.alt))
            for c, pss in records_by_chr.items()
        }
        self._build_chrom_mapping()
        return self

    def get_file_chromosomes(self) -> List[str]:
        return sorted(self.records_by_chr.keys())

    def _transform_result(self, line: Line, chrom) -> Line:
        new_data = list(line.data)
        chrom_idx = self.header.index(self.chrom_key) \
            if isinstance(self.chrom_key, str) \
            else self.chrom_key
        new_data[chrom_idx] = chrom
        return self._make_line(tuple(new_data))

    def get_all_records(self):
        for chrom in self.get_chromosomes():
            if self.chrom_map:
                if chrom not in self.chrom_map:
                    continue
                fchrom = self.chrom_map[chrom]
                for line in self.records_by_chr[fchrom]:
                    yield self._transform_result(line, chrom)
            else:
                for line in self.records_by_chr[chrom]:
                    yield line

    def get_records_in_region(
        self, chrom: str,
        pos_begin: Optional[int] = None,
        pos_end: Optional[int] = None
    ):
        if self.chrom_map:
            fch = self.chrom_map[chrom]
        else:
            fch = chrom
        for line in self.records_by_chr[fch]:
            if pos_begin and pos_begin > line.pos_end:
                continue
            if pos_end and pos_end < line.pos_begin:
                continue
            if self.chrom_map:
                yield self._transform_result(line, chrom)
            else:
                yield line

    def close(self):
        if self.str_stream is not None:
            self.str_stream.close()
