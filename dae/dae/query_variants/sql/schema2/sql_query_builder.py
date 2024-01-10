import logging
from typing import Optional, cast
from dataclasses import dataclass

from dae.pedigrees.families_data import FamiliesData
from dae.genomic_resources.gene_models import GeneModels
from dae.utils.regions import BedRegion, Region, collapse


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

    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000

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
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> str:
        summary_where: list[str] = ["ha"]
        return " ".join(summary_where)

    def _build_gene_regions_heuristic(
        self, genes: list[str], regions: Optional[list[BedRegion]]
    ) -> Optional[list[BedRegion]]:
        assert genes is not None
        assert self.gene_models is not None

        if len(genes) == 0 or len(genes) > self.GENE_REGIONS_HEURISTIC_CUTOFF:
            return regions

        gene_regions = []
        for gene_name in genes:
            gene_model = self.gene_models.gene_models_by_gene_name(gene_name)
            if gene_model is None:
                logger.warning("gene model for %s not found", gene_name)
                continue
            for gm in gene_model:
                gene_regions.append(
                    BedRegion(
                        gm.chrom,
                        max(1, gm.tx[0] - self.GENE_REGIONS_HEURISTIC_EXTEND),
                        gm.tx[1] + self.GENE_REGIONS_HEURISTIC_EXTEND,
                    )
                )
        gene_regions = collapse(gene_regions)
        if not regions:
            regions = gene_regions
        else:
            result = []
            for gene_region in gene_regions:
                for region in regions:
                    intersection = cast(
                        BedRegion, gene_region.intersection(region))
                    if intersection:
                        result.append(intersection)
            result = collapse(result)
            logger.info("original regions: %s; result: %s", regions, result)
            regions = result

        return regions

    def _build_regions_where(
        self, regions: list[BedRegion]
    ) -> str:

        where: list[str] = []
        for reg in regions:
            reg_where = (
                f"sa.chromosome = '{reg.chrom}'"
                f" AND ( "
                f"({reg.start} <= sa.position AND "
                f"sa.position <= {reg.end}) OR "
                f"(COALESCE(sa.end_position, -1) >= {reg.start} AND "
                f"COALESCE(sa.end_position, -1) <= {reg.end}) OR "
                f"(sa.position <= {reg.start} AND "
                f"COALESCE(sa.end_position, -1) >= {reg.end}) "
                f")"
            )
            where.append(f"( {reg_where} )")
        return " OR ".join(where)

    def _build_real_attr_where(
        self, real_attr_filter: RealAttrFilterType,
        is_frequency: bool = False
    ) -> str:

        where = []
        for attr_name, attr_range in real_attr_filter:
            if attr_name not in self.db_layout.summary_schema:
                where.append("false")
                continue

            left, right = attr_range

            if left is None and right is None:
                # if the filter is frequency and we have no range, we
                # we want to include all variants - don't add filter to query
                # otherwise we want to exclude variants that have no value
                if not is_frequency:
                    where.append(f"sa.{attr_name} is not null")
            elif left is None:
                assert right is not None
                if is_frequency:
                    where.append(
                        f"sa.{attr_name} <= {right} or sa.{attr_name} is null"
                    )
                else:
                    where.append(
                        f"sa.{attr_name} <= {right}"
                    )
            elif right is None:
                assert left is not None
                where.append(f"sa.{attr_name} >= {left}")
            else:
                where.append(
                    f"sa.{attr_name} >= {left} AND sa.{attr_name} <= {right}"
                )
        return " AND ".join(f"( {w} )" for w in where)

    def _build_ultra_rare_where(self) -> str:
        """Create ultra rare variants filter.

        Ultra rare variants are variants that are present in only one family.
        Given ultra rare filter we return ultra rare variants and de novo
        that have no frequency information.
        """
        return self._build_real_attr_where(
            real_attr_filter=[("af_allele_count", (None, 1))],
            is_frequency=True,
        )
