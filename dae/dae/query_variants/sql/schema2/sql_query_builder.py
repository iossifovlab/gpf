from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import duckdb
from sqlglot import condition, exp, or_, parse_one
from sqlglot.expressions import (
    Condition,
    Select,
    replace_placeholders,
)
from sqlglot.schema import Schema, ensure_schema

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
        schema: Schema,
        families: FamiliesData,
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

        self.families = families
        self.schema = schema
        self.partition_descriptor = partition_descriptor

    def build_gene_regions(
        self, genes: list[str], regions: list[Region] | None,
    ) -> list[Region] | None:
        """Build a list of regions based on genes."""
        assert self.gene_models is not None
        return create_regions_from_genes(
            self.gene_models, genes, regions,
            self.GENE_REGIONS_HEURISTIC_CUTOFF,
            self.GENE_REGIONS_HEURISTIC_EXTEND,
        )

    def calc_coding_bins(
        self,
        effect_types: Sequence[str] | None,
    ) -> list[str]:
        """Calculate applicable coding bins for a query."""
        if self.partition_descriptor is None:
            return []
        if effect_types is None:
            return []

        if "coding_bin" not in self.schema.column_names("summary_table"):
            return []
        assert "coding_bin" in self.schema.column_names("summary_table")
        assert "coding_bin" in self.schema.column_names("family_table")

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

    @staticmethod
    def build_roles_query(roles_query: str, attr: str) -> str:
        """Construct a roles query."""
        parsed = role_query.transform_query_string_to_tree(roles_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    @staticmethod
    def check_roles_query_value(roles_query: str, value: int) -> bool:
        """Check if value satisfies a given roles query."""
        with duckdb.connect(":memory:") as con:
            query = QueryBuilderBase.build_roles_query(
                roles_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    @staticmethod
    def build_inheritance_query(
        inheritance_query: Sequence[str], attr: str,
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

    @staticmethod
    def check_inheritance_query_value(
        inheritance_query: Sequence[str], value: int,
    ) -> bool:
        """Check if value satisfies a given inheritance query."""
        with duckdb.connect(":memory:") as con:
            query = QueryBuilderBase.build_inheritance_query(
                inheritance_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    @staticmethod
    def check_roles_denovo_only(roles_query: str) -> bool:
        """Check if roles query is de novo only."""
        return QueryBuilderBase.check_roles_query_value(
            roles_query,
            Role.prb.value | Role.sib.value) and \
            not QueryBuilderBase.check_roles_query_value(
                roles_query,
                Role.prb.value | Role.sib.value
                | Role.dad.value | Role.mom.value)

    @staticmethod
    def check_inheritance_denovo_only(
        inheritance_query: Sequence[str],
    ) -> bool:
        """Check if inheritance query is de novo only."""
        return not QueryBuilderBase.check_inheritance_query_value(
            inheritance_query,
            Inheritance.mendelian.value) \
            and not QueryBuilderBase.check_inheritance_query_value(
                inheritance_query,
                Inheritance.possible_denovo.value) \
            and not QueryBuilderBase.check_inheritance_query_value(
                inheritance_query,
                Inheritance.possible_omission.value) \
            and not QueryBuilderBase.check_inheritance_query_value(
                inheritance_query,
                Inheritance.missing.value)

    @staticmethod
    def build_sexes_query(sexes_query: str, attr: str) -> str:
        """Build sexes query."""
        parsed = sex_query.transform_query_string_to_tree(sexes_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    @staticmethod
    def check_sexes_query_value(sexes_query: str, value: int) -> bool:
        """Check if value matches a given sexes query."""
        with duckdb.connect(":memory:") as con:
            query = QueryBuilderBase.build_sexes_query(
                sexes_query, str(value))
            res = con.execute(f"SELECT {query}").fetchall()
            assert len(res) == 1
            assert len(res[0]) == 1

            return cast(bool, res[0][0])

    @staticmethod
    def build_variant_types_query(
        variant_types_query: str, attr: str,
    ) -> str:
        """Build a variant types query."""
        parsed = VARIANT_TYPE_PARSER.transform_query_string_to_tree(
            variant_types_query)
        transformer = QueryTreeToSQLBitwiseTransformer(
            attr, use_bit_and_function=False)
        return cast(str, transformer.transform(parsed))

    @staticmethod
    def check_variant_types_value(
        variant_types_query: str, value: int,
    ) -> bool:
        """Check if value satisfies a given variant types query."""
        with duckdb.connect(":memory:") as con:
            query = QueryBuilderBase.build_variant_types_query(
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
        if "frequency_bin" not in self.schema.column_names("summary_table"):
            return []
        assert "frequency_bin" in self.schema.column_names("summary_table")
        assert "frequency_bin" in self.schema.column_names("family_table")

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
        person_ids: Iterable[str] | None,
    ) -> list[str]:
        """Calculate family bins for a query."""
        if self.partition_descriptor is None:
            return []
        if not self.partition_descriptor.has_family_bins():
            return []
        if "family_bin" not in self.schema.column_names("family_table"):
            return []
        if family_ids is None and person_ids is None:
            return []

        family_bins: set[str] = set()
        if family_ids is not None:
            assert family_ids is not None
            family_ids = set(family_ids)

            family_bins.update(
                str(self.partition_descriptor.make_family_bin(family_id))
                for family_id in family_ids)
        if person_ids is not None:
            assert person_ids is not None
            person_ids = {
                pid for pid in person_ids
                if pid in self.families.persons_by_person_id
            }
            family_ids = {
                self.families.persons_by_person_id[person_id][0].family_id
                for person_id in person_ids
            }
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

    def calc_heuristics(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        inheritance: Sequence[str] | None = None,
        roles: str | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
    ) -> QueryHeuristics:
        """Calculate heuristic bins for a query."""
        heuristics_region_bins = []
        if genes is not None:
            regions = self.build_gene_regions(genes, regions)
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
        family_bins = self.calc_family_bins(family_ids, person_ids)
        if family_bins:
            heuristics_family_bins = family_bins

        return QueryHeuristics(
            region_bins=heuristics_region_bins,
            coding_bins=heuristics_coding_bins,
            frequency_bins=heuristics_frequency_bins,
            family_bins=heuristics_family_bins,
        )

    def calc_batched_heuristics(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        inheritance: Sequence[str] | None = None,
        roles: str | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
    ) -> list[QueryHeuristics]:
        """Calculate heuristics baches for a query."""
        heuristics = self.calc_heuristics(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            inheritance=inheritance,
            roles=roles,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            family_ids=family_ids,
            person_ids=person_ids,
        )
        if heuristics.region_bins:
            # single batch if we have region bins in heuristics
            return [heuristics]

        if heuristics.frequency_bins:
            # single batch if we dont search for rare and common variants
            rare_and_common_bins = {"2", "3"}
            if rare_and_common_bins & set(heuristics.frequency_bins):
                return [heuristics]

        if heuristics.coding_bins:
            # single batch if we search for rare coding variants
            noncoding_bin = "0"
            common_bin = "3"
            if noncoding_bin not in heuristics.coding_bins and \
                    common_bin not in heuristics.frequency_bins:
                return [heuristics]

        if self.partition_descriptor and \
                self.partition_descriptor.has_region_bins():
            return [
                QueryHeuristics(
                    region_bins=[f"'{rb}'"],
                    coding_bins=heuristics.coding_bins,
                    frequency_bins=heuristics.frequency_bins,
                    family_bins=heuristics.family_bins,
                )
                for rb in self.all_region_bins()
            ]
        return [heuristics]

    @staticmethod
    def build_schema(
        summary_schema: dict[str, str],
        family_schema: dict[str, str],
        pedigree_schema: dict[str, str],
    ) -> Schema:
        return ensure_schema(
            {
                "summary_table": summary_schema,
                "family_table": family_schema,
                "pedigree_table": pedigree_schema,
            },
        )


class SqlQueryBuilder(QueryBuilderBase):
    """Build SQL queries using sqlglot."""

    def __init__(
        self,
        db_layout: Db2Layout, *,
        schema: Schema,
        partition_descriptor: PartitionDescriptor | None,
        families: FamiliesData,
        gene_models: GeneModels,
        reference_genome: ReferenceGenome,
    ):
        super().__init__(
            schema=schema,
            families=families,
            partition_descriptor=partition_descriptor,
            gene_models=gene_models,
            reference_genome=reference_genome,
        )
        self.db_layout = db_layout

    @staticmethod
    def build(
        db_layout: Db2Layout, *,
        pedigree_schema: dict[str, str],
        summary_schema: dict[str, str],
        family_schema: dict[str, str],
        partition_descriptor: PartitionDescriptor | None,
        families: FamiliesData,
        gene_models: GeneModels,
        reference_genome: ReferenceGenome,
    ) -> SqlQueryBuilder:
        """Return a new instance of the builder."""
        schema = ensure_schema(
            {
                "summary_table": summary_schema,
                "family_table": family_schema,
                "pedigree_table": pedigree_schema,
            },
        )
        return SqlQueryBuilder(
            db_layout=db_layout,
            schema=schema,
            partition_descriptor=partition_descriptor,
            families=families,
            gene_models=gene_models,
            reference_genome=reference_genome,
        )

    @staticmethod
    def genes(genes: list[str]) -> Condition:
        """Create genes condition."""
        if len(genes) == 0:
            return condition("eg.effect_gene_symbols IS NULL")
        if len(genes) == 1:
            return condition(f"eg.effect_gene_symbols = '{genes[0]}'")
        gene_set = ",".join(f"'{g}'" for g in genes)
        return condition(f"eg.effect_gene_symbols in ({gene_set})")

    @staticmethod
    def effect_types(effect_types: list[str]) -> Condition:
        """Create effect types condition."""
        effect_types = [et.replace("'", "''") for et in effect_types]
        if len(effect_types) == 0:
            return condition("eg.effect_types IS NULL")
        effect_set = ",".join(f"'{g}'" for g in effect_types)
        return condition(f"eg.effect_types in ({effect_set})")

    @staticmethod
    def summary_base() -> Select:
        """Create summary base query."""
        return exp.select("*").from_("summary_table as sa")

    @staticmethod
    def family_base() -> Select:
        return exp.select("*").from_("family_table as fa")

    def summary_variants(
        self,
        summary: Select,
    ) -> Select:
        """Construct summary variants query."""
        return self._append_cte(
            target=Select(),
            source=summary,
            alias="summary",
        ).select(
                "sa.bucket_index", "sa.summary_index", "sa.allele_index",
                "sa.summary_variant_data",
            ).from_(
                "summary as sa",
            )

    @staticmethod
    def _append_cte(
        target: Select,
        source: Select,
        alias: str,
    ) -> Select:
        if source.ctes:
            for cte in source.ctes:
                target = target.with_(
                    cte.alias, as_=cte.this,
                )
        else:
            target = target.with_(
                alias, as_=source,
            )
        return target

    def family_variants(
        self,
        summary: Select,
        family: Select,
    ) -> Select:
        """Construct family variants query."""
        query = self._append_cte(
            Select(),
            summary,
            "summary",
        )
        return self._append_cte(
            query,
            family,
            "family",
        ).select(
            "fa.bucket_index", "fa.summary_index", "fa.family_index",
            "sa.allele_index",
            "sa.summary_variant_data",
            "fa.family_variant_data",
        ).from_(
            "summary as sa",
        ).join(
            "family as fa",
            on="sa.sj_index = fa.sj_index",
        )

    @staticmethod
    def _region_to_condition(reg: Region) -> Condition:
        if reg.start is None and reg.stop is None:
            return condition(f":chromosome = '{reg.chrom}'")

        if reg.start is None:
            assert reg.stop is not None
            return condition(
                f":chromosome = '{reg.chrom}'"
                f" AND NOT ( "
                f":position > {reg.stop} )",
            )
        if reg.stop is None:
            assert reg.start is not None
            return condition(
                f":chromosome = '{reg.chrom}'"
                f" AND ( "
                f"COALESCE(:end_position, :position) > {reg.start} )",
            )

        assert reg.stop is not None
        assert reg.start is not None

        return condition(
            f":chromosome = '{reg.chrom}'"
            f" AND NOT ( "
            f"COALESCE(:end_position, :position) < {reg.start} OR "
            f":position > {reg.stop} )",
        )

    @staticmethod
    def regions(regions: list[Region]) -> Condition:
        """Create regions condition."""
        assert len(regions) > 0

        result = SqlQueryBuilder._region_to_condition(regions[0])
        for reg in regions[1:]:
            result = or_(
                result,
                SqlQueryBuilder._region_to_condition(reg),
            )

        return result

    @staticmethod
    def _real_attr_filter(
        attr: str,
        value_range: tuple[float | None, float | None], *,
        is_frequency: bool = False,
    ) -> Condition:
        """Create real attribute condition."""
        left, right = value_range

        if left is None and right is None:
            if is_frequency:
                return condition("1 = 1")
            return condition(f"sa.{attr} IS NOT NULL")

        if left is None:
            assert right is not None
            if is_frequency:
                return condition(
                    f"sa.{attr} <= {right} OR sa.{attr} IS NULL",
                )
            return condition(f"sa.{attr} <= {right}")

        if right is None:
            assert left is not None
            return condition(f"sa.{attr} >= {left}")

        return condition(
            f"sa.{attr} >= {left} AND sa.{attr} <= {right}",
        )

    @staticmethod
    def frequency(
        real_attrs: RealAttrFilterType,
    ) -> Condition:
        """Build frequencies filter where condition."""
        assert len(real_attrs) > 0
        conditions = [
            SqlQueryBuilder._real_attr_filter(
                attr, value_range,
                is_frequency=True,
            )
            for attr, value_range in real_attrs
        ]
        if len(conditions) == 1:
            return conditions[0]
        result = conditions[0]
        for cond in conditions[1:]:
            result = result.and_(cond)
        return result

    @staticmethod
    def _real_attr(
        attr: str,
        value_range: tuple[float | None, float | None],
    ) -> Condition:
        return SqlQueryBuilder._real_attr_filter(
            attr, value_range,
            is_frequency=False,
        )

    @staticmethod
    def real_attr(
        real_attrs: RealAttrFilterType,
    ) -> Condition:
        """Build real attributes filter where condition."""
        assert len(real_attrs) > 0
        conditions = [
            SqlQueryBuilder._real_attr_filter(
                attr, value_range,
                is_frequency=False,
            )
            for attr, value_range in real_attrs
        ]
        if len(conditions) == 1:
            return conditions[0]
        result = conditions[0]
        for cond in conditions[1:]:
            result = result.and_(cond)
        return result

    @staticmethod
    def ultra_rare() -> Condition:
        return SqlQueryBuilder._real_attr_filter(
            "af_allele_count", (None, 1),
            is_frequency=True)

    def summary_query(
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
    ) -> Select:
        """Build a summary variant query."""
        query = self.summary_base()

        if regions is not None:
            clause = self.regions(regions)
            query = query.where(replace_placeholders(
                clause,
                chromosome=exp.to_column("sa.chromosome"),
                position=exp.to_column("sa.position"),
                end_position=exp.to_column("sa.end_position"),
            ))
        if real_attr_filter:
            clause = self.real_attr(real_attr_filter)
            query = query.where(clause)
        if frequency_filter:
            clause = self.frequency(frequency_filter)
            query = query.where(clause)
        if ultra_rare is not None and ultra_rare:
            clause = self.ultra_rare()
            query = query.where(clause)
        if variant_type is not None:
            query = query.where(
                self.build_variant_types_query(
                    variant_type, "sa.variant_type"))
        if not return_reference and not return_unknown:
            query = query.where("sa.allele_index > 0")

        if genes is not None or effect_types is not None:
            summary_effects = parse_one(
                "select *, unnest(sa.effect_gene) as eg "
                "from summary_base as sa",
            )
            summary = exp.select(
                "*",
            ).from_(
                "summary_effects",
            )
            if genes is not None:
                summary = summary.where(
                    SqlQueryBuilder.genes(genes))
            if effect_types is not None:
                summary = summary.where(
                    SqlQueryBuilder.effect_types(effect_types))
            query = Select().with_(
                "summary_base", as_=query,
            ).with_(
                "summary_effects", as_=summary_effects,
            ).with_(
                "summary", as_=summary,
            ).select("*").from_("summary")
        return query

    @staticmethod
    def roles(
        roles_query: str,
    ) -> Condition:
        return condition(
            SqlQueryBuilder.build_roles_query(
                roles_query, "fa.allele_in_roles"))

    @staticmethod
    def sexes(
        sexes_query: str,
    ) -> Condition:
        return condition(
            SqlQueryBuilder.build_sexes_query(
                sexes_query, "fa.allele_in_sexes"))

    @staticmethod
    def inheritance(
        inheritance_query: str | Sequence[str],
    ) -> Condition:
        """Build inheritance filter."""
        if isinstance(inheritance_query, str):
            return condition(
                SqlQueryBuilder.build_inheritance_query(
                    [inheritance_query], "fa.inheritance_in_members"))
        return condition(
            SqlQueryBuilder.build_inheritance_query(
                inheritance_query, "fa.inheritance_in_members"))

    @staticmethod
    def family_ids(
        family_ids: Sequence[str],
    ) -> Condition:
        """Create family IDs filter."""
        if not family_ids:
            return condition("fa.family_id IS NULL")
        if len(family_ids) == 1:
            return condition(f"fa.family_id = '{next(iter(family_ids))}'")
        fids = [f"'{fid}'" for fid in family_ids]
        return condition(f"fa.family_id IN ({', '.join(fids)})")

    @staticmethod
    def person_ids(
        person_ids: Sequence[str],
    ) -> Condition:
        """Create person IDs filter."""
        if not person_ids:
            return condition("fa.aim IS NULL")
        if len(person_ids) == 1:
            return condition(f"fa.aim = '{next(iter(person_ids))}'")
        pids = [f"'{pid}'" for pid in person_ids]
        return condition(f"fa.aim IN ({', '.join(pids)})")

    def family_query(
        self,
        family_ids: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        inheritance: str | Sequence[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
    ) -> Select:
        """Build a family subclause query."""
        query = self.family_base()
        if roles is not None:
            clause = self.roles(roles)
            query = query.where(clause)
        if inheritance is not None:
            clause = self.inheritance(inheritance)
            query = query.where(clause)
        if sexes is not None:
            clause = self.sexes(sexes)
            query = query.where(clause)
        if family_ids is not None or person_ids is not None:
            if person_ids is not None:
                person_ids = [
                    pid for pid in person_ids
                    if pid in self.families.persons_by_person_id
                ]
                fids = {
                    self.families.persons_by_person_id[pid][0].family_id
                    for pid in person_ids
                }
                if family_ids is not None:
                    fids &= set(family_ids)
                family_ids = list(fids)
            assert family_ids is not None
            clause = self.family_ids(family_ids)
            query = query.where(clause)
        if person_ids is not None:

            family_members = parse_one(
                "select *, unnest(fa.allele_in_members) as aim "
                "from family_base as fa",
            )
            family_query = exp.select(
                "*",
            ).from_(
                "family_members as fa",
            ).where(
                SqlQueryBuilder.person_ids(person_ids),
            )

            query = Select().with_(
                "family_base", as_=query,
            ).with_(
                "family_members", as_=family_members,
            ).with_(
                "family", as_=family_query,
            ).select("*").from_("family")

        return query

    @staticmethod
    def _heuristic_bins(
        table: str,
        heuristic: str,
        bins: list[str],
    ) -> Condition:
        assert len(bins) > 0
        if len(bins) == 1:
            return condition(f"{table}.{heuristic} = {bins[0]}")
        return condition(
            f"{table}.{heuristic} IN ({', '.join(bins)})")

    @staticmethod
    def region_bins(table: str, region_bins: list[str]) -> Condition:
        """Create region bins condition."""
        return SqlQueryBuilder._heuristic_bins(
            table, "region_bin", region_bins)

    @staticmethod
    def frequency_bins(table: str, frequency_bins: list[str]) -> Condition:
        """Create frequency bins condition."""
        return SqlQueryBuilder._heuristic_bins(
            table, "frequency_bin", frequency_bins)

    @staticmethod
    def coding_bins(table: str, coding_bins: list[str]) -> Condition:
        """Create coding bins condition."""
        return SqlQueryBuilder._heuristic_bins(
            table, "coding_bin", coding_bins)

    @staticmethod
    def family_bins(table: str, family_bins: list[str]) -> Condition:
        """Create family bins condition."""
        return SqlQueryBuilder._heuristic_bins(
            table, "family_bin", family_bins)

    def apply_summary_heuristics(
        self,
        query: Select,
        heuristics: QueryHeuristics | None,
        table: str = "sa",
    ) -> Select:
        """Apply heuristics to the summary query."""
        if heuristics is None or heuristics.is_empty():
            return query
        base_query = cast(
            Select,
            query.ctes[0].this if query.ctes else query,
        )

        if heuristics.region_bins:
            base_query = base_query.where(
                self.region_bins(table, heuristics.region_bins))

        if heuristics.frequency_bins:
            base_query = base_query.where(
                self.frequency_bins(table, heuristics.frequency_bins))
        if heuristics.coding_bins:
            base_query = base_query.where(
                self.coding_bins(table, heuristics.coding_bins))
        if not query.ctes:
            return base_query

        result = cast(Select, query.copy())
        result.ctes[0].args["this"] = base_query
        return result

    def apply_family_heuristics(
        self,
        query: Select,
        heuristics: QueryHeuristics | None,
    ) -> Select:
        """Apply heuristics to the family query."""
        if heuristics is None or heuristics.is_empty():
            return query

        query = self.apply_summary_heuristics(query, heuristics, table="fa")
        if heuristics.family_bins:
            query = query.where(
                self.family_bins("fa", heuristics.family_bins))
        return query

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
        squery = self.summary_query(
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
        batched_heuristics = self.calc_batched_heuristics(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
        )
        result = []

        for heuristics in batched_heuristics:
            query = self.summary_variants(
                summary=self.apply_summary_heuristics(squery, heuristics),
            )
            if limit is not None:
                query = query.limit(limit)
            query = self.replace_tables(query)
            result.append(query.sql())

        return result

    def replace_tables(self, query: Select) -> Select:
        """Replace table names in the query."""
        if self.db_layout.summary is None:
            assert self.db_layout.family is None
            return exp.replace_tables(
                query,
                {
                    "pedigree_table": self.db_layout.pedigree,
                },
            )
        assert self.db_layout.summary is not None
        assert self.db_layout.family is not None

        return exp.replace_tables(
            query,
            {
                "summary_table": self.db_layout.summary,
                "family_table": self.db_layout.family,
                "pedigree_table": self.db_layout.pedigree,
            },
        )

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
        squery = self.summary_query(
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
        fquery = self.family_query(
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
        )

        batched_heuristics = self.calc_batched_heuristics(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            inheritance=inheritance,
            roles=roles,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            family_ids=family_ids,
        )
        result = []
        for heuristics in batched_heuristics:
            query = self.family_variants(
                summary=self.apply_summary_heuristics(squery, heuristics),
                family=self.apply_family_heuristics(fquery, heuristics),
            )
            if limit is not None:
                query = query.limit(limit)
            query = self.replace_tables(query)

            result.append(query.sql())
        return result
