import collections
from typing import Optional, List, Any, TextIO
from copy import copy

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

    def open(self):
        self.str_stream = self.genomic_resource.open_raw_file(
            self.definition.filename, mode="rt", uncompress=True
        )
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

        self._set_special_column_indexes()
        self._validate_scoredefs()

        other_indices, other_columns = self._get_other_columns()

        assert self.chrom_column_i is not None \
            and self.pos_begin_column_i is not None \
            and self.pos_end_column_i is not None

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
            chrom = columns[self.chrom_column_i]
            ps_begin = int(columns[self.pos_begin_column_i])
            ps_end = int(columns[self.pos_end_column_i])

            if other_indices and other_columns:
                attributes = dict(
                    zip(other_columns, (columns[i] for i in other_indices))
                )
            else:
                attributes = {str(idx): val for idx, val in enumerate(columns)
                              if idx not in (self.chrom_column_i,
                                             self.pos_begin_column_i,
                                             self.pos_end_column_i)}
            ref = attributes.get(self.ref_key)
            alt = attributes.get(self.alt_key)
            records_by_chr[chrom].append(
                Line(chrom, ps_begin, ps_end,
                     attributes,
                     self.score_definitions,
                     ref=ref, alt=alt)
            )
        self.records_by_chr = {
            c: sorted(pss, key=lambda l: (l[:3], l.ref, l.alt))
            for c, pss in records_by_chr.items()
        }
        self._build_chrom_mapping()

    def get_file_chromosomes(self) -> List[str]:
        return sorted(self.records_by_chr.keys())

    def get_all_records(self):
        for chrom in self.get_chromosomes():
            if self.chrom_map:
                if chrom not in self.chrom_map:
                    continue
                fchrom = self.chrom_map[chrom]
                for line in self.records_by_chr[fchrom]:
                    transformed_line = copy(line)
                    transformed_line.chrom = chrom
                    yield transformed_line
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
                transformed_line = copy(line)
                transformed_line.chrom = chrom
                yield transformed_line
            else:
                yield line

    def close(self):
        if self.str_stream is not None:
            self.str_stream.close()
