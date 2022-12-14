from functools import cache
from typing import List
# pylint: disable=no-member
import pysam  # type: ignore

from .line import VCFLine
from .table import ScoreDef
from .table_tabix import TabixGenomicPositionTable

class VCFGenomicPositionTable(TabixGenomicPositionTable):
    """Represents a VCF file genome position table."""

    CHROM = "CHROM"
    POS_BEGIN = "POS"
    POS_END = "POS"

    VCF_TYPE_CONVERSION_MAP = {
        "Integer": "int",
        "Float": "float",
        "String": "str",
        "Flag": "bool",
    }

    def _open_pysam_file(self):
        return self.genomic_resource.open_vcf_file(self.definition.filename)

    def open(self):
        super().open()
        assert isinstance(self.pysam_file, pysam.VariantFile)
        if "scores" not in self.definition and self.pysam_file is not None:
            def converter(val):
                try:
                    return ",".join(map(str, val))
                except TypeError:
                    return val
            self.score_definitions = {
                key: ScoreDef(
                    key,
                    value.description or "",
                    self.VCF_TYPE_CONVERSION_MAP[value.type],
                    converter if value.number not in (1, "A", "R") else None,
                    tuple(),
                    None,
                    None
                ) for key, value in self.pysam_file.header.info.items()
            }

    def _validate_scoredefs(self):
        if "scores" not in self.definition:
            return None
        for score in self.definition.scores:
            if "name" in score:
                assert score.name in self.pysam_file.header.info
            elif "index" in score:
                assert 0 <= score.index < len(self.pysam_file.header.info)
            else:
                raise AssertionError("Either an index or name must"
                                        " be configured for scores!")

    def _get_index_prop_for_special_column(self, key):
        return None

    def _get_header(self):
        return tuple()

    @cache
    def get_file_chromosomes(self) -> List[str]:
        assert isinstance(self.pysam_file, pysam.VariantFile)
        return list(map(str, self.pysam_file.header.contigs))

    def get_line_iterator(self, *args):
        assert isinstance(self.pysam_file, pysam.VariantFile)
        self.stats["tabix fetch"] += 1
        self.buffer.clear()
        for raw_line in self.pysam_file.fetch(*args):
            for allele_index, alt in enumerate(raw_line.alts or [None]):
                assert raw_line.ref is not None
                yield VCFLine(
                    raw_line.contig, raw_line.pos, raw_line.pos,
                    self.score_definitions,
                    allele_index=allele_index if alt is not None else None,
                    ref=raw_line.ref,
                    alt=alt,
                    info=raw_line.info,
                    info_meta=raw_line.header.info,
                )
