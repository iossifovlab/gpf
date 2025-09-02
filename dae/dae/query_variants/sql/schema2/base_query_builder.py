import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from sqlglot import column

from dae.genomic_resources.gene_models import (
    GeneModels,
    create_regions_from_genes,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
    transform_attribute_query_to_sql_expression,
    transform_attribute_query_to_sql_expression_schema1,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role, Sex, Status, Zygosity
from dae.variants.core import Allele

logger = logging.getLogger(__name__)
RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]
CategoricalAttrFilterType = list[tuple[str, list[str] | list[int] | None]]


class Dialect:
    """Caries info about a SQL dialect."""

    def __init__(self, namespace: str | None = None):
        # namespace,
        self.namespace = namespace

    @staticmethod
    def use_bit_and_function() -> bool:
        return True

    @staticmethod
    def add_unnest_in_join() -> bool:
        return False

    @staticmethod
    def float_type() -> str:
        return "float"

    @staticmethod
    def array_item_suffix() -> str:
        return ".item"

    @staticmethod
    def int_type() -> str:
        return "int"

    @staticmethod
    def string_type() -> str:
        return "string"

    @staticmethod
    def escape_char() -> str:
        return "`"

    @staticmethod
    def escape_quote_char() -> str:
        return "\\"

    def build_table_name(self, table: str, db: str | None) -> str:
        return f"`{self.namespace}`.{db}.{table}" if self.namespace else \
               f"{db}.{table}"

    def build_array_join(self, col: str, alias: str) -> str:
        return f"\n    JOIN\n    {col} AS {alias}"


# A type describing a schema as expected by the query builders
TableSchema = dict[str, str]

# family_variant_table & summary_allele_table are mandatory
# - no reliance on a variants table as in impala


class BaseQueryBuilder(ABC):
    """Class that abstracts away the process of building a query."""

    # pylint: disable=too-many-instance-attributes

    QUOTE = "'"
    WHERE = """
  WHERE
    {where}
    """
    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000

    MAX_CHILD_NUMBER = 9999

    def __init__(
        self,
        dialect: Dialect,
        db: str | None,
        family_variant_table: str | None,
        summary_allele_table: str,
        pedigree_table: str, *,
        family_variant_schema: TableSchema | None,
        summary_allele_schema: TableSchema,
        partition_config: dict[str, Any] | None,
        pedigree_schema: TableSchema,
        families: FamiliesData,
        gene_models: GeneModels | None = None,
        reference_genome: ReferenceGenome | None = None,
    ):
        # pylint: disable=too-many-arguments

        assert summary_allele_table is not None

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.partition_config = partition_config or {}
        self.partition_descriptor = PartitionDescriptor.parse_dict(
            self.partition_config)
        if not family_variant_schema:
            family_variant_schema = {}

        self.family_columns = family_variant_schema.keys()
        self.summary_columns = summary_allele_schema.keys()
        self.combined_columns = {
            **family_variant_schema,
            **summary_allele_schema,
        }

        self.pedigree_columns = pedigree_schema
        self.families = families
        self.has_extra_attributes = "extra_attributes" in self.combined_columns
        self._product = ""
        self.gene_models = gene_models
        self.reference_genome = reference_genome
        self.query_columns = self._query_columns()
        self.where_accessors = self._where_accessors()

        if self.dialect.use_bit_and_function():
            self._transform_attribute_query = \
                transform_attribute_query_to_sql_expression_schema1
        else:
            self._transform_attribute_query = \
                transform_attribute_query_to_sql_expression

    def _where_accessors(self) -> dict[str, str]:
        cols = list(self.family_columns) + list(self.summary_columns)
        accessors = dict(zip(cols, cols, strict=True))

        family_keys = set(self.family_columns)
        summary_keys = set(self.summary_columns)

        for key, value in accessors.items():
            if value in summary_keys:
                accessors[key] = f"sa.{value}"
            elif value in family_keys:
                accessors[key] = f"fa.{value}"

        return accessors

    def build_query(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        categorical_attr_filter: CategoricalAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
    ) -> str:
        # pylint: disable=too-many-arguments,too-many-locals,unused-argument
        """Build an SQL query in the correct order."""
        self._product = ""
        self._build_select()
        self._build_from()
        self._build_join(genes=genes, effect_types=effect_types)

        self._build_where(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            affected_statuses=affected_statuses,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            categorical_attr_filter=categorical_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
        )

        self._build_group_by()
        self._build_having()
        self._build_limit(limit)

        return self._product

    def _build_select(self) -> None:
        columns = ", ".join(self.query_columns)
        select_clause = f"SELECT {columns}"
        self._add_to_product(select_clause)

    @abstractmethod
    def _build_from(self) -> None:
        """Build from clause."""

    @abstractmethod
    def _build_join(
        self, genes: list[str] | None,
        effect_types: list[str] | None,
    ) -> None:
        """Build join clause."""

    def _build_where(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        categorical_attr_filter: CategoricalAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        # pylint: disable=too-many-arguments,too-many-locals,unused-argument
        where_clause = self._build_where_string(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            affected_statuses=affected_statuses,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            categorical_attr_filter=categorical_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
        )
        self._add_to_product(where_clause)

    def _build_where_string(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        categorical_attr_filter: CategoricalAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> str:
        # pylint: disable=too-many-arguments,too-many-branches,unused-argument
        where = []

        if genes is not None and effect_types is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            clause = self._build_iterable_struct_string_attr_where(
                ["eg.effect_gene_symbols", "eg.effect_types"],
                [genes, effect_types],
            )
            where.append(f"({clause})")

        if genes is not None and effect_types is None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            # effect gene is a struct under affect gene in V2 schema
            where.append(
                self._build_iterable_struct_string_attr_where(
                    ["eg.effect_gene_symbols"], [genes],
                ),
            )
        if effect_types is not None and genes is None:
            # effect gene is a struct under affect gene in V2 schema
            where.append(
                self._build_iterable_struct_string_attr_where(
                    ["eg.effect_types"], [effect_types],
                ),
            )
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["family_id"], family_ids,
                ),
            )
        if person_ids is not None:
            person_ids = set(person_ids)
            where.append(
                self._build_iterable_string_attr_where(
                    "pi" + self.dialect.array_item_suffix(), person_ids),
            )

        if inheritance is not None:
            where.extend(
                self._build_inheritance_where(
                    "inheritance_in_members",
                    inheritance,
                ),
            )
        if roles is not None:
            roles_query = self._transform_attribute_query(
                Role, roles, column("allele_in_roles"),
                complementary_type=Zygosity,
                complementary_column=column("zygosity_in_roles"),
            ).sql()
            where.append(roles_query)
        if sexes is not None:
            sexes_query = self._transform_attribute_query(
                Sex, sexes, column("allele_in_sexes"),
                aliases=Sex.aliases(),
                complementary_type=Zygosity,
                complementary_column=column("zygosity_in_sexes"),
            ).sql()
            where.append(sexes_query)
        if affected_statuses is not None:
            statuses_query = \
                self._transform_attribute_query(
                    Status, affected_statuses,
                    column("allele_in_statuses"),
                    complementary_type=Zygosity,
                    complementary_column=column("zygosity_in_status"),
                ).sql()
            where.append(statuses_query)
        if variant_type is not None:
            variant_type_query = \
                self._transform_attribute_query(
                    Allele.Type, variant_type,
                    column("variant_type"),
                    aliases=Allele.TYPE_DISPLAY_NAME,
                ).sql()
            where.append(variant_type_query)
        if real_attr_filter is not None:
            where.append(self._build_real_attr_where(real_attr_filter))

        if categorical_attr_filter is not None:
            where.append(self._build_categorical_attr_where(
                categorical_attr_filter))

        if frequency_filter is not None:
            where.append(
                self._build_real_attr_where(
                    frequency_filter, is_frequency=True,
                ),
            )

        if ultra_rare:
            where.append(self._build_ultra_rare_where(ultra_rare=ultra_rare))

        where.extend([
            self._build_return_reference_and_return_unknown(
                return_reference=return_reference,
                return_unknown=return_unknown,
            ),
            self._build_frequency_bin_heuristic(
                inheritance=inheritance,
                ultra_rare=ultra_rare,
                frequency_filter=frequency_filter,
            ),
            self._build_family_bin_heuristic(family_ids, person_ids),
            self._build_coding_heuristic(effect_types),
            self._build_region_bin_heuristic(regions),
        ])

        where = [w for w in where if w]

        where_clause = ""

        if where:
            where_clause = self.WHERE.format(
                where=(" AND \n" + " " * 4).join(
                    [f"( {w} )" for w in where],
                ),
            )

        return where_clause

    @abstractmethod
    def _build_group_by(self) -> None:
        pass

    def _build_limit(self, limit: int | None) -> None:
        if limit is not None:
            self._add_to_product(f"LIMIT {limit}")

    @abstractmethod
    def _build_having(self, **kwargs: Any) -> None:
        pass

    def _add_to_product(self, query_part: str | None) -> None:
        if query_part is None or query_part == "":
            return
        if self._product == "":
            self._product += query_part
        else:
            self._product += f" {query_part}"

    @abstractmethod
    def _query_columns(self) -> list[str]:
        pass

    def _build_real_attr_where(
        self, real_attr_filter: RealAttrFilterType, *,
        is_frequency: bool = False,
    ) -> str:

        query = []
        for attr_name, attr_range in real_attr_filter:
            if attr_name not in self.combined_columns:
                query.append("false")
                continue
            assert attr_name in self.combined_columns
            assert (
                self.combined_columns[attr_name] == self.dialect.float_type()
                or self.combined_columns[attr_name].startswith(
                    self.dialect.int_type())
            ), f"{attr_name} - {self.combined_columns}"

            left, right = attr_range
            attr_name = self.where_accessors[attr_name]

            if left is None and right is None:
                if not is_frequency:
                    query.append(f"({attr_name} is not null)")
            elif left is None:
                assert right is not None
                if is_frequency:
                    query.append(
                        f"({attr_name} <= {right} or {attr_name} is null)",
                    )
                else:
                    query.append(
                        f"({attr_name} <= {right})",
                    )

            elif right is None:
                assert left is not None
                query.append(f"({attr_name} >= {left})")
            else:
                query.append(
                    f"({attr_name} >= {left} AND {attr_name} <= {right})",
                )
        return " AND ".join(query)

    def _build_categorical_attr_where(
        self, categorical_attr_filter: CategoricalAttrFilterType,
    ) -> str:
        query = []
        for attr_name, values in categorical_attr_filter:
            if attr_name not in self.combined_columns:
                query.append("false")
                continue
            assert attr_name in self.combined_columns
            assert (
                self.combined_columns[attr_name] == self.dialect.string_type()
                or self.combined_columns[attr_name].startswith(
                    self.dialect.int_type())
            ), f"{attr_name} - {self.combined_columns}"

            attr_name = self.where_accessors[attr_name]

            if values is None:
                query.append(f"({attr_name} is null)")
            elif len(values) == 0:
                query.append(f"({attr_name} is not null)")
            elif all(isinstance(v, str) for v in values):
                conditions = [
                    f"{attr_name} = {self.QUOTE}{v}{self.QUOTE}"
                    for v in values
                ]
                query.append(
                    " OR ".join(conditions),
                )
            elif all(isinstance(v, int) for v in values):
                conditions = [
                    f"{attr_name} = {v}"
                    for v in values
                ]
                query.append(
                    " OR ".join(conditions),
                )
            else:
                raise TypeError(
                    f"unexpected type in categorical filter: {values}")
        return " AND ".join(query)

    def _build_ultra_rare_where(self, *, ultra_rare: bool) -> str:
        assert ultra_rare
        return self._build_real_attr_where(
            real_attr_filter=[("af_allele_count", (None, 1))],
            is_frequency=True,
        )

    def _build_regions_where(self, regions: list[Region]) -> str:
        assert isinstance(regions, list), regions
        where = []
        for region in regions:
            assert isinstance(region, Region)
            esc = self.dialect.escape_char()
            end_position = f"COALESCE(sa.{esc}end_position{esc}, -1)"
            query = "( sa.{esc}chromosome{esc} = {q}{chrom}{q}"
            if region.start is None and region.end is None:
                query += " )"
                query = query.format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    esc=esc,
                )
            else:
                region_start = region.start or 1
                region_stop = region.stop or 3_000_000_000
                query += (
                    " AND "
                    "("
                    "(sa.{esc}position{esc} >= {start} AND "
                    "sa.{esc}position{esc} <= {stop}) "
                    "OR "
                    "({end_position} >= {start} AND "
                    "{end_position} <= {stop}) "
                    "OR "
                    "({start} >= sa.{esc}position{esc} AND "
                    "{stop} <= {end_position})"
                    "))"
                )

                query = query.format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    start=region_start,
                    stop=region_stop,
                    end_position=end_position,
                    esc=esc,
                )
            where.append(query)

        return " OR ".join(where)

    def _build_iterable_struct_string_attr_where(
        self, key_names: Iterable[str] | None = None,
        query_values: Iterable[Iterable[str]] | None = None,
    ) -> str:
        key_names = key_names or []
        query_values = query_values or []

        inner_clauses = [
            self._build_iterable_string_attr_where(tup[0], tup[1])
            for tup in zip(key_names, query_values, strict=True)
        ]

        return " AND ".join(inner_clauses)

    def _build_iterable_string_attr_where(
        self, column_name: str, query_values: Iterable[str],
    ) -> str:
        assert query_values is not None
        assert isinstance(query_values, (list, set)), type(query_values)

        if not query_values:
            return f" {column_name} IS NULL"

        values = [
            " {q}{val}{q} ".format(
                q=self.QUOTE,
                val=val.replace("'", self.dialect.escape_quote_char() + "'"),
            )
            for val in query_values
        ]

        where: list[str] = []
        for i in range(0, len(values), self.MAX_CHILD_NUMBER):
            chunk_values = values[i: i + self.MAX_CHILD_NUMBER]
            in_expr = f" {column_name} in ( {','.join(chunk_values)} ) "
            where.append(in_expr)

        return " OR ".join([f"( {w} )" for w in where])

    def _build_inheritance_where(
        self, column_name: str, query_value: str | list[str],
    ) -> list[str]:
        if isinstance(query_value, str):
            query_value = [query_value]

        assert len(query_value) > 0
        result = []
        for query in query_value:
            subquery = self._transform_attribute_query(
                Inheritance, query, column(column_name),
            )
            result.append(subquery.sql())
        return result

    def _build_gene_regions_heuristic(
        self, genes: list[str], regions: list[Region] | None,
    ) -> list[Region] | None:
        assert self.gene_models is not None
        return create_regions_from_genes(
            self.gene_models, genes, regions,
            self.GENE_REGIONS_HEURISTIC_CUTOFF,
            self.GENE_REGIONS_HEURISTIC_EXTEND,
        )

    def _build_partition_bin_heuristic_where(
        self, bin_column: str, bins: list[str] | set[str],
        number_of_possible_bins: int | None = None, *,
        str_bins: bool = False,
    ) -> str:
        if len(bins) == 0:
            return ""
        if number_of_possible_bins is not None and \
                len(bins) == number_of_possible_bins:
            return ""
        cols = []
        if bin_column in self.family_columns:
            cols.append("fa." + bin_column)
        if bin_column in self.summary_columns:
            cols.append("sa." + bin_column)
        if str_bins:
            bins_str = ",".join([f"'{rb}'" for rb in bins])
        else:
            bins_str = ",".join([f"{rb}" for rb in bins])
        parts = [f"{col} IN ({bins_str})" for col in cols]
        return " AND ".join(parts)

    def _build_frequency_bin_heuristic_compute_bins(
        self, *,
        inheritance: str | list[str] | None,
        ultra_rare: bool | None,
        frequency_filter: RealAttrFilterType | None,
        rare_boundary: float,
    ) -> set[str]:
        frequency_bins: set[str] = set()

        matchers = []
        if inheritance is not None:
            logger.debug(
                "frequence_bin_heuristic inheritance: %s (%s)",
                inheritance, type(inheritance),
            )
            if isinstance(inheritance, str):
                inheritance = [inheritance]

            matchers = [
                transform_attribute_query_to_function(Inheritance, inh)
                for inh in inheritance
            ]

            if any(m(Inheritance.denovo.value) for m in matchers):
                frequency_bins.add("0")

        has_frequency_filter = False
        if frequency_filter:
            for name, _ in frequency_filter:
                if name == "af_allele_freq":
                    has_frequency_filter = True
                    break

        if inheritance is None or any(
            m(
                Inheritance.mendelian.value &
                Inheritance.possible_denovo.value &
                Inheritance.possible_omission.value,
            )
            for m in matchers
        ):
            if ultra_rare:
                frequency_bins |= {"0", "1"}
            elif has_frequency_filter:
                assert frequency_filter is not None
                for name, (begin, end) in frequency_filter:
                    if name == "af_allele_freq":

                        if end and end < rare_boundary:
                            frequency_bins |= {"0", "1", "2"}
                        elif (begin and begin >= rare_boundary) or \
                                (end is not None and end >= rare_boundary):
                            frequency_bins |= {"0", "1", "2", "3"}
            elif inheritance is not None:
                frequency_bins |= {"0", "1", "2", "3"}
        return frequency_bins

    def _build_frequency_bin_heuristic(
        self, *,
        inheritance: str | list[str] | None,
        ultra_rare: bool | None,
        frequency_filter: RealAttrFilterType | None,
    ) -> str:
        # pylint: disable=too-many-branches
        assert self.partition_config is not None
        if "frequency_bin" not in self.combined_columns:
            return ""

        rare_boundary = self.partition_config["rare_boundary"]

        frequency_bins = self._build_frequency_bin_heuristic_compute_bins(
            inheritance=inheritance,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            rare_boundary=rare_boundary)

        return self._build_partition_bin_heuristic_where(
            "frequency_bin", frequency_bins, 4)

    def _build_coding_heuristic(
        self, effect_types: set[str] | list[str] | None,
    ) -> str:
        assert self.partition_config is not None
        if effect_types is None:
            return ""
        if "coding_bin" not in self.combined_columns:
            return ""
        effect_types = set(effect_types)
        intersection = effect_types & set(
            self.partition_config["coding_effect_types"],
        )

        logger.debug(
            "coding bin heuristic: query effect types: %s; "
            "coding_effect_types: %s; => %s",
            effect_types, self.partition_config["coding_effect_types"],
            intersection == effect_types,
        )

        coding_bins = set()

        if intersection == effect_types:
            coding_bins.add("1")
        elif not intersection:
            coding_bins.add("0")

        return self._build_partition_bin_heuristic_where(
            "coding_bin", coding_bins, 2)

    def _build_region_bin_heuristic(
        self, regions: list[Region] | None,
    ) -> str:
        if not regions or not self.partition_descriptor.has_region_bins():
            return ""
        assert self.partition_descriptor.has_region_bins()
        assert self.reference_genome is not None
        chromsome_lengths = self.reference_genome.get_all_chrom_lengths()
        region_bins = set()
        for region in regions:
            region_bins.update(
                self.partition_descriptor.region_to_region_bins(
                    region, chromsome_lengths,
                ))

        return self._build_partition_bin_heuristic_where(
            "region_bin", region_bins,
            str_bins=not self.partition_descriptor.integer_region_bins)

    def _build_family_bin_heuristic(
        self, family_ids: Iterable[str] | None,
        person_ids: Iterable[str] | None,
    ) -> str:
        assert self.partition_config is not None
        if "family_bin" not in self.combined_columns:
            return ""
        if "family_bin" not in self.pedigree_columns:
            return ""
        family_bins: set[str] = set()
        if family_ids:
            family_ids = set(family_ids)
            family_bins = family_bins.union(
                {
                    p.family_bin  # type: ignore
                    for p in self.families.persons.values()
                    if p.family_id in family_ids
                },
            )

        if person_ids:
            person_ids = set(person_ids)
            family_bins = family_bins.union(
                {
                    p.family_bin  # type: ignore
                    for p in self.families.persons.values()
                    if p.person_id in person_ids
                },
            )

        return self._build_partition_bin_heuristic_where(
            "family_bin", family_bins,
            self.partition_config["family_bin_size"])

    def _build_return_reference_and_return_unknown(
        self, *,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,  # noqa: ARG002
    ) -> str:
        # pylint: disable=unused-argument
        allele_index_col = self.where_accessors["allele_index"]
        if not return_reference:
            return f"{allele_index_col} > 0"
        # return_unknown basically means return all so no specific where
        # expression is required
        return ""
