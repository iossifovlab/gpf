from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any
from dae.genomic_resources.genomic_position_table.table_tabix import TabixGenomicPositionTable
from dae.genomic_resources.genomic_position_table.table_vcf import \
    VCFGenomicPositionTable
from dae.genomic_resources.genomic_position_table.utils import \
    build_genomic_position_table
from dae.genomic_resources.genomic_scores import GenomicScore
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, InfoImplementationMixin
from dae.task_graph.graph import Task
from dae.task_graph.graph import TaskGraph

logger = logging.getLogger(__name__)


@dataclass
class CNV:
    """Copy number object from a cnv_collection."""

    chrom: str
    pos_begin: int
    pos_end: int
    attributes: dict[str, Any]

    @property
    def size(self):
        return self.pos_end - self.pos_begin


class CnvCollection:
    """A collection of CNVs."""

    def __init__(self, resource: GenomicResource):
        self.resource = resource
        self.table_loaded = False

        assert self.resource.config is not None
        self.table = build_genomic_position_table(
            self.resource, self.resource.config["table"]
        )
        self.score_defs = GenomicScore._parse_scoredef_config(
            self.resource.config)

    def close(self):
        self.table.close()
        self.table_loaded = False

    def is_open(self):
        return self.table_loaded

    def open(self) -> CnvCollection:
        """Open genomic score resource and returns it."""
        if self.is_open():
            logger.info(
                "opening already opened cnv collection: %s",
                self.resource.resource_id)
            return self
        self.table.open()
        self.table_loaded = True

        assert not isinstance(self.table, VCFGenomicPositionTable)
        for score_def in self.score_defs.values():
            if score_def.col_index is None:
                assert self.table.header is not None
                assert score_def.col_name is not None
                score_def.score_index = self.table.header.index(
                    score_def.col_name)
            else:
                assert score_def.col_name is None
                score_def.score_index = score_def.col_index

        return self

    def fetch_cnvs(self, chrom: str, start: int, stop: int) -> list[CNV]:
        """Return list of CNVs that overlap with the provided region."""
        assert self.is_open()
        cnvs = []
        for line in self.table.get_records_in_region(chrom, start, stop):
            attributes = {}
            for score_id, score_def in self.score_defs.items():
                value = line.get(score_def.score_index)
                if value in score_def.na_values:
                    value = None
                elif score_def.value_parser is not None:
                    try:
                        value = score_def.value_parser(value)
                    except Exception as err:  # pylint: disable=broad-except
                        logger.error(err)
                        value = None
                attributes[score_id] = value
            cnvs.append(CNV(line.chrom, line.pos_begin, line.pos_end,
                            attributes))
        return cnvs


class CnvCollectionImplementation(GenomicResourceImplementation,
                                  InfoImplementationMixin):
    """Assists in the management of resource of type cnv_collection."""

    def add_statistics_build_tasks(self, _: TaskGraph,
                                   **_kwargs) -> list[Task]:
        return []

    def calc_info_hash(self) -> bytes:
        return b""

    def calc_statistics_hash(self) -> bytes:
        return b""

    def get_info(self) -> str:
        return InfoImplementationMixin.get_info(self)

    @property
    def files(self) -> set[str]:
        cnv_collection = CnvCollection(self.resource)

        files = set()
        files.add(cnv_collection.table.definition.filename)
        if isinstance(cnv_collection.table, TabixGenomicPositionTable):
            files.add(f"{cnv_collection.table.definition.filename}.tbi")

        return files
