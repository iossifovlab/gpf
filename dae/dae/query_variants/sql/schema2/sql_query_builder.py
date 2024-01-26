import logging
import textwrap
from typing import Optional, Any, Sequence, cast, Union
from dataclasses import dataclass

import sqlglot
import duckdb

from dae.utils.regions import Region, collapse
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.attributes_query import role_query, sex_query, \
    QueryTreeToSQLBitwiseTransformer
from dae.query_variants.attributes_query_inheritance import \
    InheritanceTransformer, \
    inheritance_parser

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
    summary: str
    family: str
    meta: str


class SqlQueryBuilder:
    """Class that abstracts away the process of building a query."""

    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000
    REGION_BINS_HEURISTIC_CUTOFF = 20

    def __init__(
        self,
        db_layout: Db2Layout,
        pedigree_schema: dict[str, str],
        summary_schema: dict[str, str],
        family_schema: dict[str, str],
        partition_descriptor: Optional[PartitionDescriptor],
        families: FamiliesData,
        gene_models: Optional[GeneModels] = None,
        reference_genome: Optional[ReferenceGenome] = None,
    ):
        self.db_layout = db_layout
        self.pedigree_schema = pedigree_schema
        self.summary_schema = summary_schema
        self.family_schema = family_schema
        self.partition_descriptor = partition_descriptor

        self.families = families
        self.gene_models = gene_models
        self.reference_genome = reference_genome

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
        eg_summary_clause = self._build_gene_effect_clause(genes, effect_types)

        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"
        summary_source = "summary"
        if eg_summary_clause:
            summary_source = "effect_gene_summary"
        query = textwrap.dedent(f"""
            WITH
            {summary_subclause}
            {eg_summary_clause}
            SELECT
                bucket_index, summary_index,
                allele_index, summary_variant_data
            FROM {summary_source}
            {limit_clause}
        """)

        sqlglot.pretty = True
        tr_query = sqlglot.transpile(query, "duckdb", "duckdb")
        assert len(tr_query) == 1
        return tr_query[0]

    def _build_gene_effect_clause(
        self,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
    ) -> str:
        eg_join_clause = ""
        if genes or effect_types:
            where_parts: list[str] = []
            if genes:
                genes = [g for g in genes if g]
                if genes:
                    where_parts.append(self._build_gene_where(genes))
            if effect_types:
                effect_types = [et for et in effect_types if et]
                if effect_types:
                    where_parts.append(
                        self._build_effect_type_where(effect_types))
            eg_where = " AND ".join([wp for wp in where_parts if wp])
            if not eg_where:
                return ""
            eg_join_clause = textwrap.dedent(f""",
                effect_gene AS (
                    SELECT *, UNNEST(effect_gene) as eg
                    FROM summary
                ),
                effect_gene_summary AS (
                    SELECT *
                    FROM effect_gene
                    WHERE
                        {eg_where}
                )
            """)
        return eg_join_clause

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

        where_parts = self._add_region_bin_heuristic(
            where_parts, regions, "sa")
        where_parts = self._add_coding_bin_heuristic(
            where_parts, effect_types, "sa")
        where_parts = self._add_frequency_bin_heuristic(
            where_parts, ultra_rare, frequency_filter, "sa")

        if not return_reference and not return_unknown:
            where_parts.append("sa.allele_index > 0")

        summary_where = ""
        if where_parts:
            where = " AND ".join([wp for wp in where_parts if wp])
            summary_where = textwrap.dedent(f"""WHERE
                {where}
            """)
        query = textwrap.dedent(f"""
            summary AS (
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
                        max(1,
                            gm.tx[0] - 1 - self.GENE_REGIONS_HEURISTIC_EXTEND),
                        gm.tx[1] + 1 + self.GENE_REGIONS_HEURISTIC_EXTEND,
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
            if attr_name not in self.summary_schema:
                where.append("false")
                continue

            left, right = attr_range

            if left is None and right is None:
                # if the filter is frequency and we have no range, we
                # we want to include all variants - don't add filter to query
                # otherwise we want to exclude variants that have no value
                if not is_frequency:
                    where.append(f"sa.{attr_name} IS NOT NULL")
            elif left is None:
                assert right is not None
                if is_frequency:
                    where.append(
                        f"sa.{attr_name} <= {right} OR sa.{attr_name} IS NULL"
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
        effect_types = [et.replace("'", "''") for et in effect_types]
        effect_set = ",".join(f"'{g}'" for g in effect_types)
        where = f"eg.effect_types in ({effect_set})"
        return where

    def _add_coding_bin_heuristic(
        self, where_parts: list[str],
        effect_types: Optional[Sequence[str]],
        table_alias: str = "sa"
    ) -> list[str]:
        if self.partition_descriptor is None:
            return where_parts
        if effect_types is None:
            return where_parts
        if "coding_bin" not in self.summary_schema:
            return where_parts
        assert "coding_bin" in self.summary_schema
        assert "coding_bin" in self.family_schema

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
        # elif not intersection:
        #     coding_bin = "0"

        if coding_bin:
            where_parts.append(
                f"{table_alias}.coding_bin = {coding_bin}")
        return where_parts

    def _add_region_bin_heuristic(
        self, where_parts: list[str],
        regions: Optional[list[Region]],
        table_alias: str = "sa"
    ) -> list[str]:
        if self.partition_descriptor is None:
            return where_parts
        if not regions or self.partition_descriptor.region_length == 0:
            return where_parts

        chroms = set(self.partition_descriptor.chromosomes)
        region_length = self.partition_descriptor.region_length
        region_bins = set()
        for region in regions:
            if region.chrom in chroms:
                chrom_bin = region.chrom
            else:
                chrom_bin = "other"
            stop = region.stop
            if stop is None:
                if self.reference_genome is None:
                    continue
                stop = self.reference_genome.get_chrom_length(region.chrom)

            start = region.start
            if start is None:
                start = 1

            start = start // region_length
            stop = stop // region_length
            for position_bin in range(start, stop + 1):
                region_bins.add(f"{chrom_bin}_{position_bin}")
        if len(region_bins) == 0:
            return where_parts
        if len(region_bins) > self.REGION_BINS_HEURISTIC_CUTOFF:
            return where_parts
        region_bins_set = ", ".join(f"'{rb}'" for rb in region_bins)
        where_parts.append(
            f"{table_alias}.region_bin in ({region_bins_set})"
        )
        return where_parts

    def _add_frequency_bin_heuristic(
        self, where_parts: list[str],
        ultra_rare: Optional[bool],
        frequency_filter: Optional[RealAttrFilterType],
        table_alias: str = "sa"
    ) -> list[str]:
        if self.partition_descriptor is None:
            return where_parts
        if not ultra_rare and frequency_filter is None:
            return where_parts
        if "frequency_bin" not in self.summary_schema:
            return where_parts
        assert "frequency_bin" in self.summary_schema
        assert "frequency_bin" in self.family_schema

        frequency_bins: set[int] = set([0])  # always search de Novo variants
        if ultra_rare is not None and ultra_rare:
            frequency_bins.add(1)
        if frequency_filter is not None:
            for freq, (_, right) in frequency_filter:
                if freq != "af_allele_freq":
                    continue
                if right is None:
                    return where_parts
                assert right is not None
                if right <= self.partition_descriptor.rare_boundary:
                    frequency_bins.add(2)
                elif right > self.partition_descriptor.rare_boundary:
                    return where_parts
        if frequency_bins and len(frequency_bins) < 4:
            frequency_bins_set = ", ".join(
                str(fb) for fb in range(0, max(frequency_bins) + 1))
            where_parts.append(
                f"{table_alias}.frequency_bin in ({frequency_bins_set})")
        return where_parts

    def build_family_variants_query(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[Sequence[str]] = None,
        person_ids: Optional[Sequence[str]] = None,
        inheritance: Optional[Sequence[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any
    ) -> str:
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
        )
        family_subclause = self._build_family_subclause(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
        )
        effect_gene_subclause = self._build_gene_effect_clause(
            genes, effect_types)

        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"

        query = f"""
            WITH
            {summary_subclause}
            {effect_gene_subclause}
            ,
            {family_subclause}
            SELECT
                fa.bucket_index, fa.summary_index, fa.family_index,
                sa.allele_index,
                sa.summary_variant_data,
                fa.family_variant_data
            FROM
                summary as sa
            JOIN
                family as fa
            ON (
                fa.summary_index = sa.summary_index AND
                fa.bucket_index = sa.bucket_index AND
                fa.allele_index = sa.allele_index)
            {limit_clause}
        """
        sqlglot.pretty = True
        tr_query = sqlglot.transpile(query, "duckdb", "duckdb")
        assert len(tr_query) == 1
        return tr_query[0]

    def _build_family_subclause(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[Sequence[str]] = None,
        person_ids: Optional[Sequence[str]] = None,
        inheritance: Optional[Union[str, Sequence[str]]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Build a subclause for the summary table.

        This is the part of the query that is specific to the summary table.
        """
        where_parts: list[str] = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
        if roles is not None:
            where_parts.append(self._build_roles_query_where(roles))
        if sexes is not None:
            where_parts.append(self._build_sexes_query_where(sexes))
        if inheritance is not None:
            if isinstance(inheritance, str):
                inheritance = [inheritance]
            where_parts.append(
                self._build_inheritance_query_where(inheritance)
            )

        where_parts = self._add_region_bin_heuristic(
            where_parts, regions, "fa")
        where_parts = self._add_coding_bin_heuristic(
            where_parts, effect_types, "fa")
        where_parts = self._add_frequency_bin_heuristic(
            where_parts, ultra_rare, frequency_filter, "fa")

        # Do not look into reference alleles
        if not return_reference and not return_unknown:
            where_parts.append("fa.allele_index > 0")

        family_where = ""
        if where_parts:
            where = " AND ".join([wp for wp in where_parts if wp])
            family_where = textwrap.dedent(f"""WHERE
                {where}
            """)
        query = textwrap.dedent(f"""
            family AS (
                SELECT
                    *
                FROM
                    {self.db_layout.family} fa
                {family_where}
            )
            """)
        return query

    def _build_roles_query(self, roles_query: str, attr: str) -> str:
        parsed = role_query.transform_query_string_to_tree(roles_query)
        transformer = QueryTreeToSQLBitwiseTransformer(attr, False)
        return cast(str, transformer.transform(parsed))

    def _check_roles_query_value(self, roles_query: str, value: int) -> bool:
        with duckdb.connect(":memory:") as con:
            query = self._build_roles_query(
                roles_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def _build_roles_query_where(self, roles_query: str) -> str:
        return self._build_roles_query(roles_query, "fa.allele_in_roles")

    def _build_sexes_query(self, sexes_query: str, attr: str) -> str:
        parsed = sex_query.transform_query_string_to_tree(sexes_query)
        transformer = QueryTreeToSQLBitwiseTransformer(attr, False)
        return cast(str, transformer.transform(parsed))

    def _check_sexes_query_value(self, sexes_query: str, value: int) -> bool:
        with duckdb.connect(":memory:") as con:
            query = self._build_sexes_query(
                sexes_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def _build_sexes_query_where(self, sexes_query: str) -> str:
        return self._build_sexes_query(sexes_query, "fa.allele_in_sexes")

    def _build_inheritance_query(
        self, inheritance_query: Sequence[str], attr: str
    ) -> str:
        result = []
        transformer = InheritanceTransformer(attr, use_bit_and_function=False)
        for query in inheritance_query:
            parsed = inheritance_parser.parse(query)
            result.append(str(transformer.transform(parsed)))
        if not result:
            return ""
        return " AND ".join(result)        

    def _check_inheritance_query_value(
        self, inheritance_query: Sequence[str], value: int
    ) -> bool:
        with duckdb.connect(":memory:") as con:
            query = self._build_inheritance_query(
                inheritance_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def _build_inheritance_query_where(
        self, inheritance_query: Sequence[str]
    ) -> str:
        return self._build_inheritance_query(
            inheritance_query, "fa.inheritance_in_members")
