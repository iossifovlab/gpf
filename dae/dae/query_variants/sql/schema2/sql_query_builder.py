import logging
import textwrap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import duckdb
import sqlglot

from dae.effect_annotation.effect import EffectTypesMixin
from dae.genomic_resources.gene_models import (
    GeneModels,
    create_regions_from_genes,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.attributes_query import (
    QueryTreeToSQLBitwiseTransformer,
    role_query,
    sex_query,
)
from dae.query_variants.attributes_query import (
    variant_type_query as VARIANT_TYPE_PARSER,
)
from dae.query_variants.attributes_query_inheritance import (
    InheritanceTransformer,
    inheritance_parser,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role

logger = logging.getLogger(__name__)


# A type describing a schema as expected by the query builders
TableSchema = dict[str, str]
RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]


# family_variant_table & summary_allele_table are mandatory
# - no reliance on a variants table as in impala
@dataclass(frozen=True)
class Db2Layout:
    """Genotype data layout in the database."""

    db: str | None
    study: str
    pedigree: str
    summary: str | None
    family: str | None
    meta: str


@dataclass(frozen=True)
class QueryHeuristics:
    """Heuristics for a query."""

    region_bins: list[str]
    coding_bins: list[str]
    frequency_bins: list[str]
    family_bins: list[str]

    def is_empty(self) -> bool:
        """Check if all heuristics are empty."""
        return len(self.region_bins) == 0 and len(self.coding_bins) == 0 and \
            len(self.frequency_bins) == 0 and len(self.family_bins) == 0


class QueryBuilderBase:
    """Base class for building SQL queries."""

    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000
    REGION_BINS_HEURISTIC_CUTOFF = 20

    def __init__(
        self,
        pedigree_schema: dict[str, str],
        summary_schema: dict[str, str],
        family_schema: dict[str, str],
        partition_descriptor: PartitionDescriptor | None,
        gene_models: GeneModels,
        reference_genome: ReferenceGenome,
    ):
        if gene_models is None:
            raise ValueError("gene_models are required")
        self.gene_models = gene_models

        if reference_genome is None:
            raise ValueError("reference genome isrequired")
        self.reference_genome = reference_genome

        self.pedigree_schema = pedigree_schema
        self.summary_schema = summary_schema
        self.family_schema = family_schema
        self.partition_descriptor = partition_descriptor

    def build_gene_regions_heuristic(
        self, genes: list[str], regions: list[Region] | None,
    ) -> list[Region] | None:
        """Build a list of regions based on genes."""
        assert self.gene_models is not None
        return create_regions_from_genes(
            self.gene_models, genes, regions,
            self.GENE_REGIONS_HEURISTIC_CUTOFF,
            self.GENE_REGIONS_HEURISTIC_EXTEND,
        )

    @staticmethod
    def build_regions_where(
        regions: list[Region],
    ) -> str:
        """Build a WHERE clause for regions."""
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

    def calc_coding_bins(
        self,
        effect_types: Sequence[str] | None,
    ) -> list[str]:
        """Calculate applicable coding bins for a query."""
        if self.partition_descriptor is None:
            return []
        if effect_types is None:
            return []
        if "coding_bin" not in self.summary_schema:
            return []
        assert "coding_bin" in self.summary_schema
        assert "coding_bin" in self.family_schema

        assert effect_types is not None
        query_effect_types = set(effect_types)
        intersection = query_effect_types & set(
            self.partition_descriptor.coding_effect_types,
        )

        coding_bins = []
        if intersection == query_effect_types:
            coding_bins.append("1")
        return coding_bins

    def calc_region_bins(
        self, regions: list[Region] | None,
    ) -> list[str]:
        """Calculate applicable region bins for a query."""
        if self.partition_descriptor is None:
            return []
        if not regions or not self.partition_descriptor.has_region_bins():
            return []

        chroms = set(self.partition_descriptor.chromosomes)
        region_length = self.partition_descriptor.region_length
        region_bins: set[str] = set()
        for region in regions:
            chrom_bin = region.chrom if region.chrom in chroms else "other"
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
            region_bins.update(
                f"'{chrom_bin}_{position_bin}'"
                for position_bin in range(start, stop + 1))
        assert len(region_bins) > 0

        if len(region_bins) > self.REGION_BINS_HEURISTIC_CUTOFF:
            return []

        return list(region_bins)

    def build_roles_query(self, roles_query: str, attr: str) -> str:
        """Construct a roles query."""
        parsed = role_query.transform_query_string_to_tree(roles_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    def check_roles_query_value(self, roles_query: str, value: int) -> bool:
        """Check if value satisfies a given roles query."""
        with duckdb.connect(":memory:") as con:
            query = self.build_roles_query(
                roles_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def build_inheritance_query(
        self, inheritance_query: Sequence[str], attr: str,
    ) -> str:
        """Construct an inheritance query."""
        result = []
        transformer = InheritanceTransformer(attr, use_bit_and_function=False)
        for query in inheritance_query:
            parsed = inheritance_parser.parse(query)
            result.append(str(transformer.transform(parsed)))
        if not result:
            return ""
        return " AND ".join(result)

    def check_inheritance_query_value(
        self, inheritance_query: Sequence[str], value: int,
    ) -> bool:
        """Check if value satisfies a given inheritance query."""
        with duckdb.connect(":memory:") as con:
            query = self.build_inheritance_query(
                inheritance_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def check_roles_denovo_only(self, roles_query: str) -> bool:
        """Check if roles query is de novo only."""
        return self.check_roles_query_value(
            roles_query,
            Role.prb.value | Role.sib.value) and \
            not self.check_roles_query_value(
                roles_query,
                Role.prb.value | Role.sib.value
                | Role.dad.value | Role.mom.value)

    def check_inheritance_denovo_only(
        self, inheritance_query: Sequence[str],
    ) -> bool:
        """Check if inheritance query is de novo only."""
        return not self.check_inheritance_query_value(
            inheritance_query,
            Inheritance.mendelian.value) \
            and not self.check_inheritance_query_value(
                inheritance_query,
                Inheritance.possible_denovo.value) \
            and not self.check_inheritance_query_value(
                inheritance_query,
                Inheritance.possible_omission.value) \
            and not self.check_inheritance_query_value(
                inheritance_query,
                Inheritance.missing.value)

    def build_sexes_query(self, sexes_query: str, attr: str) -> str:
        """Build sexes query."""
        parsed = sex_query.transform_query_string_to_tree(sexes_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    def check_sexes_query_value(self, sexes_query: str, value: int) -> bool:
        """Check if value matches a given sexes query."""
        with duckdb.connect(":memory:") as con:
            query = self.build_sexes_query(
                sexes_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def build_variant_types_query(
        self, variant_types_query: str, attr: str,
    ) -> str:
        """Build a variant types query."""
        parsed = VARIANT_TYPE_PARSER.transform_query_string_to_tree(
            variant_types_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    def check_variant_types_value(
        self, variant_types_query: str, value: int,
    ) -> bool:
        """Check if value satisfies a given variant types query."""
        with duckdb.connect(":memory:") as con:
            query = self.build_variant_types_query(
                variant_types_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    def calc_frequency_bins(
        self, *,
        inheritance: Sequence[str] | None = None,
        roles: str | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
    ) -> list[str]:
        """Calculate applicable frequency bins for a query."""
        if self.partition_descriptor is None:
            return []
        if "frequency_bin" not in self.summary_schema:
            return []
        assert "frequency_bin" in self.summary_schema
        assert "frequency_bin" in self.family_schema

        if roles and self.check_roles_denovo_only(roles):
            return ["0"]
        if inheritance and self.check_inheritance_denovo_only(inheritance):
            return ["0"]

        if not ultra_rare and frequency_filter is None:
            return []

        frequency_bins: set[int] = {0}  # always search de Novo variants
        if ultra_rare is not None and ultra_rare:
            frequency_bins.add(1)
        if frequency_filter is not None:
            for freq, (_, right) in frequency_filter:
                if freq != "af_allele_freq":
                    continue
                if right is None:
                    return []
                assert right is not None
                if right <= self.partition_descriptor.rare_boundary:
                    frequency_bins.add(2)
                elif right > self.partition_descriptor.rare_boundary:
                    return []
        result: list[str] = []
        if frequency_bins and len(frequency_bins) < 4:
            result = [
                str(fb) for fb in range(max(frequency_bins) + 1)
            ]

        return result

    def calc_family_bins(
        self,
        family_ids: Iterable[str] | None,
    ) -> list[str]:
        """Calculate family bins for a query."""
        if self.partition_descriptor is None:
            return []
        if not self.partition_descriptor.has_family_bins():
            return []
        if "family_bin" not in self.family_schema:
            return []
        if family_ids is None:
            return []

        assert family_ids is not None
        family_ids = set(family_ids)

        family_bins: set[str] = set()
        family_bins.update(
            str(self.partition_descriptor.make_family_bin(family_id))
            for family_id in family_ids)
        if len(family_bins) >= self.partition_descriptor.family_bin_size // 2:
            return []
        return list(family_bins)

    def all_region_bins(self) -> list[str]:
        """Return all region bins."""
        if self.partition_descriptor is None:
            return []
        if not self.partition_descriptor.has_region_bins():
            return []
        chrom_lens = dict(self.reference_genome.get_all_chrom_lengths())
        return [
            str(rb)
            for rb in self.partition_descriptor.make_all_region_bins(
                chrom_lens,
            )
        ]

    def calc_heuristic_bins(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        inheritance: Sequence[str] | None = None,
        roles: str | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        family_ids: Iterable[str] | None = None,
    ) -> QueryHeuristics:
        """Calculate heuristic bins for a query."""
        heuristics_region_bins = []
        if genes is not None:
            regions = self.build_gene_regions_heuristic(genes, regions)
        region_bins = self.calc_region_bins(regions)
        if region_bins:
            heuristics_region_bins = region_bins

        heuristics_coding_bins = []
        coding_bins = self.calc_coding_bins(effect_types)
        if coding_bins:
            heuristics_coding_bins = coding_bins

        heuristics_frequency_bins = []
        frequency_bins = self.calc_frequency_bins(
            inheritance=inheritance,
            roles=roles,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
        )
        if frequency_bins:
            heuristics_frequency_bins = frequency_bins

        heuristics_family_bins = []
        family_bins = self.calc_family_bins(family_ids)
        if family_bins:
            heuristics_family_bins = family_bins

        return QueryHeuristics(
            region_bins=heuristics_region_bins,
            coding_bins=heuristics_coding_bins,
            frequency_bins=heuristics_frequency_bins,
            family_bins=heuristics_family_bins,
        )


class SqlQueryBuilder(QueryBuilderBase):
    """Class that abstracts away the process of building a query."""

    def __init__(
        self,
        db_layout: Db2Layout, *,
        pedigree_schema: dict[str, str],
        summary_schema: dict[str, str],
        family_schema: dict[str, str],
        partition_descriptor: PartitionDescriptor | None,
        families: FamiliesData,
        gene_models: GeneModels,
        reference_genome: ReferenceGenome,
    ):
        super().__init__(
            pedigree_schema=pedigree_schema,
            summary_schema=summary_schema,
            family_schema=family_schema,
            partition_descriptor=partition_descriptor,
            gene_models=gene_models,
            reference_genome=reference_genome,
        )

        self.db_layout = db_layout
        self.families = families

    def build_summary_variants_query(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """Build a query for summary variants."""
        heuristics = self.calc_heuristic_bins(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
        )
        region_batches: list[list[str]] = [[]]
        if heuristics.region_bins:
            region_batches = [heuristics.region_bins]
        elif self.partition_descriptor \
                and self.partition_descriptor.has_region_bins() \
                and heuristics.region_bins:
            region_batches = [
                [f"'{rb}'"]
                for rb in self.all_region_bins()
            ]

        result = []
        for rb in region_batches:
            batch_heuristics = QueryHeuristics(
                region_bins=rb,
                coding_bins=heuristics.coding_bins,
                frequency_bins=heuristics.frequency_bins,
                family_bins=heuristics.family_bins,
            )
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
                heuristics=batch_heuristics,
            )
            eg_summary_clause = self._build_gene_effect_clause(
                genes, effect_types)

            limit_clause = ""
            if limit is not None:
                limit_clause = f"LIMIT {limit}"
            summary_source = "summary"
            if eg_summary_clause:
                summary_source = "effect_gene"
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
            result.append(tr_query[0])
        return result

    def _build_gene_effect_clause(
        self,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
    ) -> str:
        assert self.gene_models is not None

        eg_subclause = ""
        if genes is not None or effect_types is not None:
            where_parts: list[str] = []
            if genes is not None:
                genes = [g for g in genes if g in self.gene_models.gene_models]
                where_parts.append(self._build_gene_where(genes))
            if effect_types is not None:
                effect_types = [
                    et for et in effect_types
                    if et in EffectTypesMixin.EFFECT_TYPES]
                if set(effect_types) != set(EffectTypesMixin.EFFECT_TYPES):
                    where_parts.append(
                        self._build_effect_type_where(effect_types))
            eg_where = " AND ".join([wp for wp in where_parts if wp])
            if not eg_where:
                return ""
            eg_subclause = textwrap.dedent(f""",
                effect_gene_all AS (
                    SELECT *, UNNEST(effect_gene) as eg
                    FROM summary
                ),
                effect_gene AS (
                    SELECT *
                    FROM effect_gene_all
                    WHERE
                        {eg_where}
                )
            """)  # noqa: S608
        return eg_subclause

    @staticmethod
    def _heuristic_where(
        alias: str,
        heuristic: str,
        bins: list[str],
    ) -> str:
        if len(bins) == 0:
            return ""
        if len(bins) == 1:
            return f"{alias}.{heuristic} = {bins[0]}"
        return f"{alias}.{heuristic} IN ({', '.join(bins)})"

    def _build_summary_subclause(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        heuristics: QueryHeuristics | None = None,
        **_kwargs: Any,
    ) -> str:
        """Build a subclause for the summary table.

        This is the part of the query that is specific to the summary table.
        """
        where_parts: list[str] = []
        if genes is not None:
            regions = self.build_gene_regions_heuristic(genes, regions)
        if regions is not None:
            where_parts.append(self.build_regions_where(regions))
        if frequency_filter is not None:
            where_parts.append(
                self._build_real_attr_where(
                    frequency_filter, is_frequency=True),
            )
        if real_attr_filter is not None:
            where_parts.append(
                self._build_real_attr_where(
                    real_attr_filter, is_frequency=False),
            )
        if ultra_rare is not None and ultra_rare:
            where_parts.append(self._build_ultra_rare_where())
        if variant_type is not None:
            where_parts.append(
                self._build_variant_types_where(variant_type),
            )

        if heuristics is not None and not heuristics.is_empty():
            where_parts.extend([
                self._heuristic_where(
                    "sa", "region_bin", heuristics.region_bins),
                self._heuristic_where(
                    "sa", "frequency_bin", heuristics.frequency_bins),
                self._heuristic_where(
                    "sa", "coding_bin", heuristics.coding_bins),
            ])

        if not return_reference and not return_unknown:
            where_parts.append("sa.allele_index > 0")

        summary_where = ""
        if where_parts:
            where = " AND ".join([wp for wp in where_parts if wp])
            summary_where = textwrap.dedent(f"""WHERE
                {where}
            """)
        return textwrap.dedent(f"""
            summary AS (
                SELECT
                    *
                FROM
                    {self.db_layout.summary} sa
                {summary_where}
            )
            """)

    def _build_real_attr_where(
        self, real_attr_filter: RealAttrFilterType, *,
        is_frequency: bool = False,
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
                        f"sa.{attr_name} <= {right} OR sa.{attr_name} IS NULL",
                    )
                else:
                    where.append(
                        f"sa.{attr_name} <= {right}",
                    )
            elif right is None:
                assert left is not None
                where.append(f"sa.{attr_name} >= {left}")
            else:
                where.append(
                    f"sa.{attr_name} >= {left} AND sa.{attr_name} <= {right}",
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
        if len(genes) == 0:
            return "eg.effect_gene_symbols IS NULL"
        gene_set = ",".join(f"'{g}'" for g in genes)
        return f"eg.effect_gene_symbols in ({gene_set})"

    def _build_effect_type_where(self, effect_types: list[str]) -> str:
        effect_types = [et.replace("'", "''") for et in effect_types]
        if len(effect_types) == 0:
            return "eg.effect_types IS NULL"
        effect_set = ",".join(f"'{g}'" for g in effect_types)
        return f"eg.effect_types in ({effect_set})"

    def _adapt_family_and_person_ids(
        self, family_ids: Sequence[str] | None,
        person_ids: Sequence[str] | None,
    ) -> tuple[Sequence[str] | None, Sequence[str] | None]:
        if family_ids is None:
            return None, person_ids
        if person_ids is None:
            return family_ids, person_ids
        result = set()
        person_ids_set = set()
        family_ids_set = set(family_ids)
        for pid in person_ids:
            persons = self.families.persons_by_person_id.get(pid)
            if persons is None:
                continue
            for person in persons:
                if person.family_id not in family_ids_set:
                    continue
                result.add(person.family_id)
                person_ids_set.add(pid)
        family_ids = list(result & family_ids_set)
        return family_ids, list(person_ids_set)

    def _build_person_subclause(
        self, person_ids: Sequence[str] | None,
    ) -> str:
        if person_ids is None:
            return ""
        if len(person_ids) == 0:
            person_where = "fa.aim IS NULL"
        else:
            person_ids = [f"'{pid}'" for pid in person_ids]
            person_where = f"fa.aim IN ({', '.join(person_ids)})"

        return f"""
            ,
            allele_in_member AS (
                SELECT
                    *,
                    UNNEST(allele_in_members) as aim
                FROM
                    family
            ),
            family_person AS (
                SELECT
                    *
                FROM allele_in_member as fa
                WHERE
                    {person_where}
            )
        """

    def _build_roles_query_where(self, roles_query: str) -> str:
        subquery = self.build_roles_query(roles_query, "fa.allele_in_roles")
        return f"({subquery})"

    def _build_inheritance_query_where(
        self, inheritance_query: Sequence[str],
    ) -> str:
        subquery = self.build_inheritance_query(
            inheritance_query, "fa.inheritance_in_members")
        return f"({subquery})"

    def _build_sexes_query_where(self, sexes_query: str) -> str:
        subquery = self.build_sexes_query(sexes_query, "fa.allele_in_sexes")
        return f"({subquery})"

    def _build_variant_types_where(
        self, variant_types_query: str,
    ) -> str:
        subquery = self.build_variant_types_query(
            variant_types_query, "sa.variant_type")
        return f"({subquery})"

    def build_family_variants_query(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        inheritance: Sequence[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **_kwargs: Any,
    ) -> list[str]:
        """Build a query for family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        heuristics = self.calc_heuristic_bins(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            inheritance=inheritance,
            roles=roles,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            family_ids=family_ids,
        )

        region_batches: list[list[str]] = [[]]
        if heuristics.region_bins:
            region_batches = [heuristics.region_bins]
        elif self.partition_descriptor \
                and self.partition_descriptor.has_region_bins():
            region_batches = [
                [f"'{rb}'"]
                for rb in self.all_region_bins()
            ]

        result = []
        for rb in region_batches:
            batch_heuristics = QueryHeuristics(
                region_bins=rb,
                coding_bins=heuristics.coding_bins,
                frequency_bins=heuristics.frequency_bins,
                family_bins=heuristics.family_bins,
            )

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
                heuristics=batch_heuristics,
            )
            family_ids, person_ids = self._adapt_family_and_person_ids(
                family_ids, person_ids,
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
                heuristics=batch_heuristics,
            )

            effect_gene_subclause = self._build_gene_effect_clause(
                genes, effect_types)
            summary_from = "summary"
            if effect_gene_subclause:
                summary_from = "effect_gene"

            person_subclause = self._build_person_subclause(
                person_ids=person_ids)
            family_from = "family"
            if person_subclause:
                family_from = "family_person"

            limit_clause = ""
            if limit is not None:
                limit_clause = f"LIMIT {limit}"

            join_on_clause = textwrap.dedent("""
                ON (
                    fa.summary_index = sa.summary_index AND
                    fa.bucket_index = sa.bucket_index AND
                    fa.allele_index = sa.allele_index)
            """)
            if "sj_index" in self.summary_schema and \
                    "sj_index" in self.family_schema:
                join_on_clause = textwrap.dedent("""
                    ON fa.sj_index = sa.sj_index
                """)

            query = f"""
                WITH
                {summary_subclause}
                {effect_gene_subclause}
                ,
                {family_subclause}
                {person_subclause}
                SELECT
                    fa.bucket_index, fa.summary_index, fa.family_index,
                    sa.allele_index,
                    sa.summary_variant_data,
                    fa.family_variant_data
                FROM
                    {summary_from} as sa
                JOIN
                    {family_from} as fa
                {join_on_clause}
                {limit_clause}
            """
            sqlglot.pretty = True
            tr_query = sqlglot.transpile(query, "duckdb", "duckdb")
            assert len(tr_query) == 1
            result.append(tr_query[0])
        return result

    def _build_family_subclause(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        family_ids: Sequence[str] | None = None,
        _person_ids: Sequence[str] | None = None,
        inheritance: str | Sequence[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        heuristics: QueryHeuristics | None = None,
        **_kwargs: Any,
    ) -> str:
        """Build a subclause for the family table.

        This is the part of the query that is specific to the family table.
        """
        # pylint: disable=too-many-arguments
        query: list[str] = []
        where_parts: list[str] = []
        from_clause = f"{self.db_layout.family} AS fa"
        if heuristics and not heuristics.is_empty():
            where_parts.extend([
                self._heuristic_where(
                    "fa", "region_bin", heuristics.region_bins),
                self._heuristic_where(
                    "fa", "frequency_bin", heuristics.frequency_bins),
                self._heuristic_where(
                    "fa", "coding_bin", heuristics.coding_bins),
                self._heuristic_where(
                    "fa", "family_bin", heuristics.family_bins),
            ])
            assert where_parts

            where = " AND ".join([wp for wp in where_parts if wp])
            family_where = textwrap.dedent(f"""WHERE
                {where}
            """)

            query.append(f"""
                family_bins AS (
                    SELECT
                        *
                    FROM {from_clause}
                    {family_where}
                )
            """)
            from_clause = "family_bins AS fa"

        where_parts = []
        if genes is not None:
            regions = self.build_gene_regions_heuristic(genes, regions)
        if roles is not None:
            where_parts.append(self._build_roles_query_where(roles))
        if sexes is not None:
            where_parts.append(self._build_sexes_query_where(sexes))
        if inheritance is not None:
            if isinstance(inheritance, str):
                inheritance = [inheritance]
            where_parts.append(
                self._build_inheritance_query_where(inheritance),
            )
        if family_ids is not None:
            where_parts.append(self._build_family_ids_query_where(family_ids))

        # Do not look into reference alleles if not requested
        if not return_reference and not return_unknown:
            where_parts.append("fa.allele_index > 0")

        family_where = ""
        if where_parts:
            where = " AND ".join([wp for wp in where_parts if wp])
            family_where = textwrap.dedent(f"""WHERE
                {where}
            """)
        query.append(
            textwrap.dedent(f"""
                family AS (
                    SELECT
                        *
                    FROM
                        {from_clause}
                    {family_where}
                )
            """),
        )
        return ",".join(query)

    def _build_family_ids_query_where(self, family_ids: Sequence[str]) -> str:
        if not family_ids:
            return "fa.family_id IS NULL"
        family_ids = [f"'{fid}'" for fid in family_ids]
        return f"fa.family_id IN ({', '.join(family_ids)})"
