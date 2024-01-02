import logging
from typing import Optional
from dataclasses import dataclass

from dae.pedigrees.families_data import FamiliesData
from dae.genomic_resources.gene_models import GeneModels


logger = logging.getLogger(__name__)


# A type describing a schema as expected by the query builders
TableSchema = dict[str, str]
RealAttrFilterType = list[tuple[str, tuple[Optional[float], Optional[float]]]]


# family_variant_table & summary_allele_table are mandatory
# - no reliance on a variants table as in impala
@dataclass(frozen=True)
class Db2Layout:
    """Genotype data layout in the database."""

    db: str
    study: str
    pedigree: str
    pedigree_schema: dict[str, str]
    summary: str
    summary_schema: dict[str, str]
    family: str
    family_schema: dict[str, str]
    meta: str


class SqlQueryBuilder:
    """Class that abstracts away the process of building a query."""

    def __init__(
        self,
        db_layout: Db2Layout,
        partition_descriptor: Optional[dict],
        families: FamiliesData,
        gene_models: Optional[GeneModels] = None,
    ):
        self.db_layout = db_layout
        self.partition_descriptor = partition_descriptor

        self.families = families
        self.gene_models = gene_models

    def build_summary_query(
        self,
    ) -> str:
        return ""
