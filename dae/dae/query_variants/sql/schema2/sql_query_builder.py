import logging
import textwrap
from typing import Optional, Any, Sequence
from dataclasses import dataclass

import sqlglot

from dae.pedigrees.families_data import FamiliesData
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.genomic_resources.gene_models import GeneModels
from dae.utils.regions import Region, collapse


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
        partition_descriptor: Optional[PartitionDescriptor],
        families: FamiliesData,
        gene_models: Optional[GeneModels] = None,
    ):
        self.db_layout = db_layout
        self.partition_descriptor = partition_descriptor

        self.families = families
        self.gene_models = gene_models

    def build_summary_variants_query(
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
        """Build a query for summary variants."""
        summary_subclause = self._build_summary_subclause(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
        )
        eg_join_clause = ""
        if genes is not None or effect_types is not None:
            where_parts: list[str] = []
            if genes is not None:
                where_parts.append(self._build_gene_where(genes))
            if effect_types is not None:
                where_parts.append(self._build_effect_type_where(effect_types))
            eg_where = " AND ".join(where_parts)
            eg_join_clause = textwrap.dedent(f"""
                CROSS JOIN
                    (SELECT UNNEST (effect_gene) as eg)
                WHERE
                    {eg_where}
            """)

        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"

        query = textwrap.dedent(f"""
            {summary_subclause}
            SELECT
                bucket_index, summary_index,
                list(allele_index), first(summary_variant_data)
            FROM summary
            {eg_join_clause}
            GROUP BY bucket_index, summary_index
            {limit_clause}
        """)

        sqlglot.pretty = True
        tr_query = sqlglot.transpile(query, "duckdb", "duckdb")
        assert len(tr_query) == 1
        return tr_query[0]

    def _build_summary_subclause(
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
        **kwargs: Any
    ) -> str:
        """Build a subclause for the summary table.

        This is the part of the query that is specific to the summary table.
        """
        where_parts: list[str] = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
        if regions is not None:
            where_parts.append(self._build_regions_where(regions))
        if frequency_filter is not None:
            where_parts.append(
                self._build_real_attr_where(
                    frequency_filter, is_frequency=True)
            )
        if real_attr_filter is not None:
            where_parts.append(
                self._build_real_attr_where(
                    real_attr_filter, is_frequency=False)
            )
        if ultra_rare is not None and ultra_rare:
            where_parts.append(self._build_ultra_rare_where())

        where_parts = self._add_coding_bin_heuristic(
            where_parts,
            effect_types=effect_types
        )

        # Do not look into reference alleles
        where_parts.append("sa.allele_index > 0")

        summary_where = ""
        if where_parts:
            where = " AND ".join(where_parts)
            summary_where = textwrap.dedent(f"""WHERE
                {where}
            """)
        query = textwrap.dedent(f"""
            WITH summary AS (
                SELECT
                    *
                FROM
                    {self.db_layout.summary} sa
                {summary_where}
            )
            """)
        return query

    def _build_gene_regions_heuristic(
        self, genes: list[str], regions: Optional[list[Region]]
    ) -> Optional[list[Region]]:
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
                    Region(
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
                    intersection = gene_region.intersection(region)
                    if intersection:
                        result.append(intersection)
            result = collapse(result)
            logger.info("original regions: %s; result: %s", regions, result)
            regions = result

        return regions

    def _build_regions_where(
        self, regions: list[Region]
    ) -> str:

        where: list[str] = []
        for reg in regions:
            if reg.start is None and reg.stop is None:
                reg_where = f"sa.chromosome = '{reg.chrom}'"
            elif reg.start is None:
                assert reg.stop is not None
                reg_where = (
                    f"sa.chromosome = '{reg.chrom}'"
                    f" AND NOT ( "
                    f"sa.position > {reg.stop} )"
                )
            elif reg.stop is None:
                assert reg.start is not None
                reg_where = (
                    f"sa.chromosome = '{reg.chrom}'"
                    f" AND ( "
                    f"COALESCE(sa.end_position, sa.position) > {reg.start} )"
                )
            else:
                assert reg.stop is not None
                assert reg.start is not None

                reg_where = (
                    f"sa.chromosome = '{reg.chrom}'"
                    f" AND NOT ( "
                    f"COALESCE(sa.end_position, sa.position) < {reg.start} OR "
                    f"sa.position > {reg.stop} )"
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

    def _build_gene_where(self, genes: list[str]) -> str:
        gene_set = ",".join(f"'{g}'" for g in genes)
        where = f"eg.effect_gene_symbols in ({gene_set})"
        return where

    def _build_effect_type_where(self, effect_types: list[str]) -> str:
        effect_set = ",".join(f"'{g}'" for g in effect_types)
        where = f"eg.effect_types in ({effect_set})"
        return where

    def _add_coding_bin_heuristic(
        self, where_parts: list[str],
        effect_types: Optional[Sequence[str]]
    ) -> list[str]:
        assert self.partition_descriptor is not None
        if effect_types is None:
            return where_parts
        if "coding_bin" not in self.db_layout.summary_schema:
            return where_parts
        assert "coding_bin" in self.db_layout.summary_schema
        assert "coding_bin" in self.db_layout.family_schema

        assert effect_types is not None
        query_effect_types = set(effect_types)
        intersection = query_effect_types & set(
            self.partition_descriptor.coding_effect_types
        )

        logger.debug(
            "coding bin heuristic: query effect types: %s; "
            "coding_effect_types: %s; => %s",
            effect_types, self.partition_descriptor.coding_effect_types,
            intersection == query_effect_types
        )

        coding_bin = ""

        if intersection == query_effect_types:
            coding_bin = "1"
        elif not intersection:
            coding_bin = "0"

        if coding_bin:
            where_parts.append(f"sa.coding_bin = {coding_bin}")
        return where_parts
