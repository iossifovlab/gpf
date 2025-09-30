import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any

import dae.utils.regions
from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
    transform_attribute_query_to_sql_expression_schema1,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role, Sex
from dae.variants.core import Allele
from sqlglot import column

logger = logging.getLogger(__name__)
RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]


class BaseQueryBuilder(ABC):
    """A base class for all query builders."""

    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """
    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000

    MAX_CHILD_NUMBER = 9999

    def __init__(
        self, db: str, variants_table: str, pedigree_table: str,
        variants_schema: list[AttributeInfo],
        table_properties: dict[str, Any],
        pedigree_schema: dict[str, str],
        families: FamiliesData,
        gene_models: GeneModels | None = None,
    ) -> None:
        assert variants_schema is not None

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table
        self.table_properties = table_properties
        self.variants_columns = {
            attr.name: attr for attr in variants_schema
        }
        self.pedigree_columns = pedigree_schema
        self.families = families
        self.has_extra_attributes = \
            "extra_attributes" in self.variants_columns
        self._product = ""
        self.query_columns = self._query_columns()
        self.gene_models = gene_models
        self.where_accessors = self._where_accessors()

    def reset_product(self) -> None:
        self._product = ""

    @property
    def product(self) -> str:
        return self._product

    def _where_accessors(self) -> dict[str, str]:
        cols = list(self.variants_columns)
        accessors = dict(zip(cols, cols, strict=True))
        if "effect_types" not in accessors:
            accessors["effect_types"] = "effect_types"

        return accessors

    def build_select(self) -> None:
        columns = ", ".join(self.query_columns)
        select_clause = f"SELECT {columns}"
        self._add_to_product(select_clause)

    def build_from(self) -> None:
        from_clause = f"FROM {self.db}.{self.variants_table}"
        self._add_to_product(from_clause)

    @abstractmethod
    def build_join(self) -> None:
        pass

    def build_where(
        self, *,
        regions: list[dae.utils.regions.Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: set[str] | list[str] | None = None,
        person_ids: set[str] | None = None,
        inheritance: list[str] | str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **_kwargs: Any,
    ) -> None:
        """Build the where clause of a query."""
        # pylint: disable=too-many-arguments
        where_clause = self._base_build_where(
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
        )
        self._add_to_product(where_clause)

    def _base_build_where(
        self, *,
        regions: list[dae.utils.regions.Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: list[str] | str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **_kwargs: Any,
    ) -> str:
        # pylint: disable=too-many-arguments,too-many-branches
        where = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["effect_gene_symbols"], genes,
                ),
            )
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            # pylint: disable=no-member
            family_ids = set(family_ids) & \
                set(self.families.keys())
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["family_id"], family_ids),
            )
        if person_ids is not None:
            # pylint: disable=no-member
            person_ids = set(person_ids) & \
                set(self.families.persons_by_person_id.keys())
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["variant_in_members"], person_ids,
                ),
            )
        if effect_types is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["effect_types"], effect_types,
                ),
            )
        if inheritance is not None:
            where.extend(
                self._build_inheritance_where(
                    self.where_accessors["inheritance_in_members"], inheritance,
                ),
            )
        if roles is not None:
            roles_query = transform_attribute_query_to_sql_expression_schema1(
                Role, roles, column(self.where_accessors["variant_in_roles"]),
            ).sql()
            where.append(roles_query)
        if sexes is not None:
            sexes_query = transform_attribute_query_to_sql_expression_schema1(
                Sex, sexes, column(self.where_accessors["variant_in_sexes"]),
                aliases=Sex.aliases(),
            ).sql()
            where.append(sexes_query)
        if affected_statuses is not None:
            # we do not have `variant_in_statuses` in the schema1
            raise ValueError("Schema1 does not support affected status queres")

        if variant_type is not None:
            variant_type_query = \
                transform_attribute_query_to_sql_expression_schema1(
                    Allele.Type, variant_type,
                    column(self.where_accessors["variant_type"]),
                    aliases=Allele.TYPE_DISPLAY_NAME,
                ).sql()
            where.append(variant_type_query)
        if real_attr_filter is not None:
            where.append(self._build_real_attr_where(
                real_attr_filter=real_attr_filter))
        if frequency_filter is not None:
            where.append(
                self._build_real_attr_where(
                    real_attr_filter=frequency_filter, is_frequency=True))
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
                real_attr_filter=frequency_filter,
            ),
            self._build_family_bin_heuristic(family_ids, person_ids),
            self._build_coding_heuristic(effect_types),
            self._build_region_bin_heuristic(regions),
        ])

        where = [w for w in where if w]

        where_clause = ""

        if where:
            where_clause = self.WHERE.format(
                where=" AND ".join([f"( {w} )" for w in where]),
            )

        return where_clause

    @abstractmethod
    def build_group_by(self) -> None:
        pass

    def build_limit(self, limit: int | None = None) -> None:
        if limit is not None:
            self._add_to_product(f"LIMIT {limit}")

    @abstractmethod
    def create_row_deserializer(self, serializer: Any) -> Callable:
        pass

    def _add_to_product(self, string: str) -> None:
        if string is None or string == "":
            return
        if self._product == "":
            self._product += string
        else:
            self._product += f" {string}"

    @abstractmethod
    def _query_columns(self) -> list[str]:
        pass

    def _build_real_attr_where(
        self, *,
        real_attr_filter: list[Any],
        is_frequency: bool = False,
    ) -> str:
        query = []
        for attr_name, attr_range in real_attr_filter:
            if attr_name not in self.variants_columns:
                query.append("false")
                continue
            assert attr_name in self.variants_columns
            assert (
                self.variants_columns[attr_name].type in ("float", "int")
            ), self.variants_columns[attr_name]
            left, right = attr_range
            attr_name = self.where_accessors[attr_name]
            if left is None and right is None:
                if not is_frequency:
                    query.append(
                        f"({attr_name} is not null)",
                    )
            elif left is None:
                assert right is not None
                query.append(
                    f"({attr_name} <= {right} or {attr_name} is null)")

            elif right is None:
                assert left is not None
                query.append(f"({attr_name} >= {left})")
            else:
                query.append(
                    f"({attr_name} >= {left} AND {attr_name} <= {right})",
                )
        return " AND ".join(query)

    def _build_ultra_rare_where(self, *, ultra_rare: bool) -> str:
        assert ultra_rare
        return self._build_real_attr_where(
            real_attr_filter=[("af_allele_count", (None, 1))],
            is_frequency=True,
        )

    @classmethod
    def _build_regions_where(
        cls, regions: list[dae.utils.regions.Region | Any],
    ) -> str:
        assert isinstance(regions, list), regions
        where = []
        for region in regions:
            assert isinstance(region, Region)
            end_position = "COALESCE(end_position, -1)"
            query = "(`chromosome` = {q}{chrom}{q}"
            if region.start is None and region.end is None:
                query += ")"
                query = query.format(
                    q=cls.QUOTE,
                    chrom=region.chrom,
                )
            else:
                query += (
                    " AND "
                    "("
                    "(`position` >= {start} AND `position` <= {stop}) "
                    "OR "
                    "({end_position} >= {start} AND {end_position} <= {stop}) "
                    "OR "
                    "({start} >= `position` AND {stop} <= {end_position})"
                    "))"
                )
                query = query.format(
                    q=cls.QUOTE,
                    chrom=region.chrom,
                    start=region.start,
                    stop=region.stop,
                    end_position=end_position,
                )
            where.append(query)
        return " OR ".join(where)

    def _build_iterable_string_attr_where(
        self, column_name: str,
        query_values: set[str] | list[str],
    ) -> str:
        assert query_values is not None

        assert isinstance(query_values, (list, set)), type(query_values)

        if not query_values:
            return f" {column_name} IS NULL"

        values = [
            " {q}{val}{q} ".format(
                q=self.QUOTE, val=val.replace("'", "\\'"),
            )
            for val in query_values
        ]

        where_list: list[str] = []
        for i in range(0, len(values), self.MAX_CHILD_NUMBER):
            chunk_values = ",".join(values[i: i + self.MAX_CHILD_NUMBER])
            where_str = f" {column_name} in ( {chunk_values} ) "

            where_list.append(where_str)

        return " OR ".join([f"( {w} )" for w in where_list])

    @staticmethod
    def _build_inheritance_where(
        column_name: str, query_value: str | list[str],
    ) -> list[str]:
        if isinstance(query_value, str):
            query_value = [query_value]

        assert len(query_value) > 0
        result = []
        for query in query_value:
            subquery = transform_attribute_query_to_sql_expression_schema1(
                Inheritance, query, column(column_name),
            )
            result.append(subquery.sql())
        return result

    def _build_gene_regions_heuristic(
        self, genes: list[str | Any],
        regions: list[dae.utils.regions.Region] | None,
    ) -> list[dae.utils.regions.Region] | None:
        assert genes is not None
        assert self.gene_models is not None
        if len(genes) > 0 and len(genes) <= self.GENE_REGIONS_HEURISTIC_CUTOFF:
            gene_regions = []
            for gene in genes:
                gene_model = self.gene_models.gene_models_by_gene_name(gene)
                if gene_model is None:
                    logger.warning("gene model for %s not found", gene)
                    continue
                gene_regions.extend([
                    Region(
                        gm.chrom,
                        max(
                            1,
                            gm.tx[0] - self.GENE_REGIONS_HEURISTIC_EXTEND),
                        gm.tx[1] + self.GENE_REGIONS_HEURISTIC_EXTEND,
                    ) for gm in gene_model
                ])

            gene_regions = dae.utils.regions.collapse(gene_regions)
            logger.info("gene regions for %s: %s", genes, gene_regions)
            logger.info("input regions: %s", regions)
            if not regions:
                regions = gene_regions
            else:
                result = []
                for gene_region in gene_regions:
                    for region in regions:
                        intersection = gene_region.intersection(region)
                        if intersection:
                            result.append(intersection)
                result = dae.utils.regions.collapse(result)
                logger.info("original regions: %s; result: %s",
                            regions, result)
                regions = result

        return regions

    def _build_frequency_bin_heuristic(
        self, *, inheritance: str | list[str] | None,
        ultra_rare: bool | None,
        real_attr_filter: RealAttrFilterType | None,
    ) -> str:
        # pylint: disable=too-many-branches
        if "frequency_bin" not in self.variants_columns:
            return ""

        rare_boundary = self.table_properties["rare_boundary"]

        frequency_bin = set()
        frequency_bin_col = self.where_accessors["frequency_bin"]

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
                for inh in inheritance]

            if any(matcher(Inheritance.denovo.value) for matcher in matchers):
                frequency_bin.add(f"{frequency_bin_col} = 0")

        has_transmitted_query_1 = [
            any(
                matcher(inh) for inh in [
                    Inheritance.mendelian.value,
                    Inheritance.possible_denovo.value,
                    Inheritance.possible_omission.value,
                    Inheritance.unknown.value,
                    Inheritance.missing.value,
                ]
            ) for matcher in matchers
        ]
        has_transmitted_query = all(has_transmitted_query_1)

        has_frequency_query = False
        if real_attr_filter:
            for name, (_begin, _end) in real_attr_filter:
                if name == "af_allele_freq":
                    has_frequency_query = True
                    break

        if inheritance is None or has_transmitted_query:
            if ultra_rare:
                frequency_bin.update([
                    f"{frequency_bin_col} = 0",
                    f"{frequency_bin_col} = 1",
                ])
            elif has_frequency_query:
                assert real_attr_filter is not None
                for name, (begin, end) in real_attr_filter:
                    if name == "af_allele_freq":

                        if end and end < rare_boundary:
                            frequency_bin.update([
                                f"{frequency_bin_col} = 0",
                                f"{frequency_bin_col} = 1",
                                f"{frequency_bin_col} = 2"])
                        elif begin and begin >= rare_boundary:
                            frequency_bin.add(f"{frequency_bin_col} = 3")
                        elif end is not None and end >= rare_boundary:
                            frequency_bin.update([
                                f"{frequency_bin_col} = 0",
                                f"{frequency_bin_col} = 1",
                                f"{frequency_bin_col} = 2",
                                f"{frequency_bin_col} = 3",
                            ])

            elif inheritance is not None:
                frequency_bin.update([
                    f"{frequency_bin_col} = 1",
                    f"{frequency_bin_col} = 2",
                    f"{frequency_bin_col} = 3"])

        if len(frequency_bin) == 4:
            return ""

        return " OR ".join(frequency_bin)

    def _build_coding_heuristic(
        self, effect_types: list[str] | None,
    ) -> str:
        if effect_types is None:
            return ""
        if "coding_bin" not in self.variants_columns:
            return ""
        effect_types_set = set(effect_types)
        intersection = \
            effect_types_set & \
            set(self.table_properties["coding_effect_types"])

        logger.debug(
            "coding bin heuristic for %s: query effect types: %s; "
            "coding_effect_types: %s; => %s",
            self.variants_table, effect_types,
            self.table_properties["coding_effect_types"],
            intersection == effect_types_set,
        )

        coding_bin_col = self.where_accessors["coding_bin"]

        if intersection == effect_types_set:
            return f"{coding_bin_col} = 1"
        if not intersection:
            return f"{coding_bin_col} = 0"
        return ""

    def _build_region_bin_heuristic(
        self, regions: list[dae.utils.regions.Region] | None,
    ) -> str:
        if not regions or self.table_properties["region_length"] == 0:
            return ""

        chroms = set(self.table_properties["chromosomes"])
        region_length = self.table_properties["region_length"]
        region_bins = []
        for region in regions:
            chrom_bin = region.chrom if region.chrom in chroms else "other"
            if region.start is None and region.end is None:
                continue
            start = region.start // region_length
            stop = region.stop // region_length
            region_bins.extend([
                f"{chrom_bin}_{position_bin}"
                for position_bin in range(start, stop + 1)
            ])
        if not region_bins:
            return ""
        region_bin_col = self.where_accessors["region_bin"]
        bins_str = ",".join([f"'{rb}'" for rb in region_bins])
        return f"{region_bin_col} IN ({bins_str})"

    def _build_family_bin_heuristic(
        self, family_ids: set[str] | None,
        person_ids: set[str] | None,
    ) -> str:
        if "family_bin" not in self.variants_columns:
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

        family_bin_col = self.where_accessors["family_bin"]

        if 0 < len(family_bins) < self.table_properties["family_bin_size"]:
            family_bin_list = ", ".join([str(fb) for fb in family_bins])
            return f"{family_bin_col} IN ({family_bin_list})"

        return ""

    def _build_return_reference_and_return_unknown(
        self, *, return_reference: bool | None = None,
        return_unknown: bool | None = None,
    ) -> str:
        allele_index_col = self.where_accessors["allele_index"]
        if not return_reference:
            return f"{allele_index_col} > 0"
        if not return_unknown:
            return f"{allele_index_col} >= 0"
        return ""
