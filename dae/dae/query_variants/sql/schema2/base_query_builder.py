import logging
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from dae.genomic_resources.gene_models import GeneModels
from dae.variants.attributes import Inheritance
from dae.utils.regions import Region
import dae.utils.regions

from dae.query_variants.attributes_query import inheritance_query
from dae.query_variants.attributes_query import \
    QueryTreeToSQLBitwiseTransformer, \
    role_query, \
    sex_query, \
    variant_type_query

from dae.query_variants.attributes_query_inheritance import \
    InheritanceTransformer, \
    inheritance_parser


logger = logging.getLogger(__name__)


class Dialect(ABC):
    """Caries info about a SQL dialect."""

    def __init__(self, namespace: Optional[str] = None):
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

    def build_table_name(self, table: str, db: str) -> str:
        return f"`{self.namespace}`.{db}.{table}" if self.namespace else \
               f"{db}.{table}"


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
        db: str,
        family_variant_table: Optional[str],
        summary_allele_table: str,
        pedigree_table: str,
        family_variant_schema: Optional[TableSchema],
        summary_allele_schema: TableSchema,
        partition_descriptor: Optional[dict],
        pedigree_schema: TableSchema,
        pedigree_df: pd.DataFrame,
        gene_models: Optional[GeneModels] = None,
    ):
        # pylint: disable=too-many-arguments

        assert summary_allele_table is not None

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.partition_descriptor = partition_descriptor

        if not family_variant_schema:
            family_variant_schema = {}

        self.family_columns = family_variant_schema.keys()
        self.summary_columns = summary_allele_schema.keys()
        self.combined_columns = {
            **family_variant_schema,
            **summary_allele_schema,
        }

        self.pedigree_columns = pedigree_schema
        self.ped_df = pedigree_df
        self.has_extra_attributes = "extra_attributes" in self.combined_columns
        self._product = ""
        self.gene_models = gene_models
        self.query_columns = self._query_columns()
        self.where_accessors = self._where_accessors()

    def _where_accessors(self):
        cols = list(self.family_columns) + list(self.summary_columns)
        accessors = dict(zip(cols, cols))

        family_keys = set(self.family_columns)
        summary_keys = set(self.summary_columns)

        for key, value in accessors.items():
            if value in summary_keys:
                accessors[key] = f"sa.{value}"
            elif value in family_keys:
                accessors[key] = f"fa.{value}"

        return accessors

    def build_query(
        self,
        regions: Optional[list[Region]] = None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        frequency_filter=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
        pedigree_fields=None,  # pylint: disable=unused-argument
    ):
        # pylint: disable=too-many-arguments,too-many-locals
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
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
        )

        self._build_group_by()
        self._build_having()
        self._build_limit(limit)

        return self._product

    def _build_select(self):
        columns = ", ".join(self.query_columns)
        select_clause = f"SELECT {columns}"
        self._add_to_product(select_clause)

    def _build_from(self):
        pass

    def _build_join(self, genes, effect_types):
        pass

    def _build_where(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        frequency_filter=None,
        return_reference=None,
        return_unknown=None,
        **_kwargs,
    ):
        # pylint: disable=too-many-arguments,too-many-locals
        where_clause = self._build_where_string(
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

    def _build_where_string(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        frequency_filter=None,
        return_reference=None,
        return_unknown=None,
        **_kwargs,
    ):
        # pylint: disable=too-many-arguments,too-many-locals,too-many-branches
        where = []

        if genes is not None and effect_types is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            clause = self._build_iterable_struct_string_attr_where(
                ["eg.effect_gene_symbols", "eg.effect_types"],
                [genes, effect_types]
            )
            where.append(f"({clause})")

        if genes is not None and effect_types is None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            # effect gene is a struct under affect gene in V2 schema
            where.append(
                self._build_iterable_struct_string_attr_where(
                    ["eg.effect_gene_symbols"], [genes]
                )
            )
        if effect_types is not None and genes is None:
            # effect gene is a struct under affect gene in V2 schema
            where.append(
                self._build_iterable_struct_string_attr_where(
                    ["eg.effect_types"], [effect_types]
                )
            )
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["family_id"], family_ids
                )
            )
        if person_ids is not None:
            person_ids = set(person_ids)
            where.append(
                self._build_iterable_string_attr_where(
                    "pi" + self.dialect.array_item_suffix(), person_ids)
            )

        if inheritance is not None:
            where.extend(
                self._build_inheritance_where(
                    self.where_accessors["inheritance_in_members"],
                    inheritance, self.dialect.use_bit_and_function()
                )
            )
        if roles is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["allele_in_roles"], roles, role_query
                )
            )
        if sexes is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["allele_in_sexes"], sexes, sex_query
                )
            )
        if variant_type is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["variant_type"],
                    variant_type,
                    variant_type_query,
                )
            )
        if real_attr_filter is not None:
            where.append(self._build_real_attr_where(real_attr_filter))
        if frequency_filter is not None:
            where.append(
                self._build_real_attr_where(
                    frequency_filter, is_frequency=True
                )
            )

        if ultra_rare:
            where.append(self._build_ultra_rare_where(ultra_rare))

        where.append(
            self._build_return_reference_and_return_unknown(
                return_reference, return_unknown
            )
        )
        where.append(
            self._build_frequency_bin_heuristic(
                inheritance, ultra_rare, frequency_filter
            )
        )
        where.append(self._build_family_bin_heuristic(family_ids, person_ids))
        where.append(self._build_coding_heuristic(effect_types))
        where.append(self._build_region_bin_heuristic(regions))

        where = [w for w in where if w]

        where_clause = ""

        if where:
            where_clause = self.WHERE.format(
                where=(" AND \n" + " " * 4).join(
                    [f"( {w} )" for w in where]
                )
            )

        return where_clause

    @abstractmethod
    def _build_group_by(self):
        pass

    def _build_limit(self, limit):
        if limit is not None:
            self._add_to_product(f"LIMIT {limit}")

    @abstractmethod
    def _build_having(self, **kwargs):
        pass

    def _add_to_product(self, string):
        if string is None or string == "":
            return
        if self._product == "":
            self._product += string
        else:
            self._product += f" {string}"

    @abstractmethod
    def _query_columns(self):
        pass

    def _build_real_attr_where(self, real_attr_filter, is_frequency=False):

        query = []
        for attr_name, attr_range in real_attr_filter:
            if attr_name not in self.combined_columns:
                query.append("false")
                continue
            assert attr_name in self.combined_columns
            assert (
                self.combined_columns[attr_name] == self.dialect.float_type()
                or self.combined_columns[attr_name] == self.dialect.int_type()
            ), f"{attr_name} - {self.combined_columns}"

            left, right = attr_range
            attr_name = self.where_accessors[attr_name]

            if left is None and right is None:
                if not is_frequency:
                    query.append(f"({attr_name} is not null)")
            elif left is None:
                assert right is not None
                query.append(
                    f"({attr_name} <= {right} or {attr_name} is null)"
                )

            elif right is None:
                assert left is not None
                query.append(f"({attr_name} >= {left})")
            else:
                query.append(
                    "({attr} >= {left} AND {attr} <= {right})".format(
                        attr=attr_name, left=left, right=right
                    )
                )
        return " AND ".join(query)

    def _build_ultra_rare_where(self, ultra_rare):
        assert ultra_rare
        return self._build_real_attr_where(
            real_attr_filter=[("af_allele_count", (None, 1))],
            is_frequency=True,
        )

    def _build_regions_where(self, regions):
        assert isinstance(regions, list), regions
        where = []
        for region in regions:
            assert isinstance(region, Region)
            end_position = "COALESCE(`end_position`, `position`)"
            query = "(`chromosome` = {q}{chrom}{q}"
            if region.start is None and region.end is None:
                query += ")"
                query = query.format(
                    q=self.QUOTE,
                    chrom=region.chrom
                )
            else:
                query += (
                    " AND "
                    "({start} <= `position`) AND "
                    "({stop} >= {end_position}))"
                )
                query = query.format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    start=region.start,
                    stop=region.stop,
                    end_position=end_position,
                )
            where.append(query)

        return " OR ".join(where)

    def _build_iterable_struct_string_attr_where(
        self, key_names=None, query_values=None
    ):
        key_names = key_names if key_names else []
        query_values = query_values if query_values else []

        inner_clauses = [
            self._build_iterable_string_attr_where(tup[0], tup[1])
            for tup in zip(key_names, query_values)
        ]

        where_clause = " AND ".join(inner_clauses)
        return where_clause

    def _build_iterable_string_attr_where(self, column_name, query_values):
        assert query_values is not None
        assert isinstance(query_values, (list, set)), type(query_values)

        if not query_values:
            return f" {column_name} IS NULL"

        values = [
            " {q}{val}{q} ".format(
                q=self.QUOTE, val=val.replace("'", "\\'")
            )
            for val in query_values
        ]

        where: list[str] = []
        for i in range(0, len(values), self.MAX_CHILD_NUMBER):
            chunk_values = values[i: i + self.MAX_CHILD_NUMBER]
            in_expr = f" {column_name} in ( {','.join(chunk_values)} ) "
            where.append(in_expr)

        where_clause = " OR ".join([f"( {w} )" for w in where])
        return where_clause

    def _build_bitwise_attr_where(
        self, column_name, query_value, query_transformer
    ):
        assert query_value is not None
        parsed = query_value
        if isinstance(query_value, str):
            parsed = query_transformer.transform_query_string_to_tree(
                query_value
            )

        transformer = QueryTreeToSQLBitwiseTransformer(
            column_name, self.dialect.use_bit_and_function()
        )
        return transformer.transform(parsed)

    @staticmethod
    def _build_inheritance_where(column_name, query_value,
                                 use_bit_and_function):
        trees = []
        if isinstance(query_value, str):
            tree = inheritance_parser.parse(query_value)
            trees.append(tree)

        elif isinstance(query_value, list):
            for qval in query_value:
                tree = inheritance_parser.parse(qval)
                trees.append(tree)

            # raise ValueError()
        else:
            tree = query_value
            trees.append(tree)

        result = []
        for tree in trees:
            transformer = InheritanceTransformer(column_name,
                                                 use_bit_and_function)
            res = transformer.transform(tree)
            result.append(res)
        return result

    def _build_gene_regions_heuristic(self, genes, regions):
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
                        gm.tx[0] - self.GENE_REGIONS_HEURISTIC_EXTEND,
                        gm.tx[1] + self.GENE_REGIONS_HEURISTIC_EXTEND,
                    )
                )
        gene_regions = dae.utils.regions.collapse(gene_regions)
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
            logger.info("original regions: %s; result: %s", regions, result)
            regions = result

        return regions

    def _build_partition_bin_heuristic_where(self, bin_column, bins,
                                             number_of_possible_bins=None,
                                             str_bins=False):
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
        self, inheritance, ultra_rare, real_attr_filter, rare_boundary
    ):
        frequency_bins: set[int] = set([])

        matchers = []
        if inheritance is not None:
            logger.debug(
                "frequence_bin_heuristic inheritance: %s (%s)",
                inheritance, type(inheritance)
            )
            if isinstance(inheritance, str):
                inheritance = [inheritance]

            matchers = [
                inheritance_query.transform_tree_to_matcher(
                    inheritance_query.transform_query_string_to_tree(inh)
                )
                for inh in inheritance
            ]

            if any(m.match([Inheritance.denovo]) for m in matchers):
                frequency_bins.add(0)

        if inheritance is None or any(
            m.match(
                [
                    Inheritance.mendelian,
                    Inheritance.possible_denovo,
                    Inheritance.possible_omission,
                ]
            )
            for m in matchers
        ):
            if ultra_rare:
                frequency_bins |= set([0, 1])
            elif real_attr_filter:
                for name, (begin, end) in real_attr_filter:
                    if name == "af_allele_freq":

                        if end and end < rare_boundary:
                            frequency_bins |= set([0, 1, 2])
                        elif begin and begin >= rare_boundary:
                            frequency_bins.add(3)
                        elif end is not None and end >= rare_boundary:
                            frequency_bins |= set([0, 1, 2, 3])
            elif inheritance is not None:
                frequency_bins |= set([1, 2, 3])
        return frequency_bins

    def _build_frequency_bin_heuristic(
        self, inheritance, ultra_rare, real_attr_filter
    ):
        # pylint: disable=too-many-branches
        assert self.partition_descriptor is not None
        if "frequency_bin" not in self.combined_columns:
            return ""

        rare_boundary = self.partition_descriptor["rare_boundary"]

        frequency_bins = self._build_frequency_bin_heuristic_compute_bins(
            inheritance, ultra_rare, real_attr_filter, rare_boundary)

        return self._build_partition_bin_heuristic_where(
            "frequency_bin", frequency_bins, 4)

        # cols = []
        # if "frequency_bin" in self.family_columns:
        #     cols.append("fa.frequency_bin")
        # if "frequency_bin" in self.summary_columns:
        #     cols.append("sa.frequency_bin")
        # bins_str = ",".join([f"{rb}" for rb in frequency_bins])
        # parts = [f"{col} IN ({bins_str})" for col in cols]
        # return " AND ".join(parts)

    def _build_coding_heuristic(self, effect_types):
        assert self.partition_descriptor is not None
        if effect_types is None:
            return ""
        if "coding_bin" not in self.combined_columns:
            return ""
        effect_types = set(effect_types)
        intersection = effect_types & set(
            self.partition_descriptor["coding_effect_types"]
        )

        logger.debug(
            "coding bin heuristic: query effect types: %s; "
            "coding_effect_types: %s; => %s",
            effect_types, self.partition_descriptor["coding_effect_types"],
            intersection == effect_types
        )

        coding_bins = set([])

        if intersection == effect_types:
            coding_bins.add(1)
        elif not intersection:
            coding_bins.add(0)

        return self._build_partition_bin_heuristic_where(
            "coding_bin", coding_bins, 2)

    def _build_region_bin_heuristic(self, regions):
        assert self.partition_descriptor is not None
        if not regions or self.partition_descriptor["region_length"] == 0:
            return ""

        chroms = set(self.partition_descriptor["chromosomes"])
        region_length = self.partition_descriptor["region_length"]
        region_bins = []
        for region in regions:
            if region.chrom in chroms:
                chrom_bin = region.chrom
            else:
                chrom_bin = "other"
            if region.start is None and region.end is None:
                continue
            start = region.start // region_length
            stop = region.stop // region_length
            for position_bin in range(start, stop + 1):
                region_bins.append(f"{chrom_bin}_{position_bin}")

        return self._build_partition_bin_heuristic_where(
            "region_bin", region_bins, str_bins=True)

        # region_bin_col = self.where_accessors["region_bin"]
        # cols = []
        # if "region_bin" in self.family_columns:
        #     cols.append("fa.region_bin")
        # if "region_bin" in self.summary_columns:
        #     cols.append("sa.region_bin")
        # bins_str = ",".join([f"'{rb}'" for rb in region_bins])
        # parts = [f"{col} IN ({bins_str})" for col in cols]
        # return " AND ".join(parts)

        # return f"{region_bin_col} IN ({bins_str})"

    def _build_family_bin_heuristic(self, family_ids, person_ids):
        assert self.partition_descriptor is not None
        if "family_bin" not in self.combined_columns:
            return ""
        if "family_bin" not in self.pedigree_columns:
            return ""
        family_bins: set[str] = set()
        if family_ids:
            family_ids = set(family_ids)
            family_bins = family_bins.union(
                set(
                    self.ped_df[
                        self.ped_df["family_id"].isin(family_ids)
                    ].family_bin.values
                )
            )

        if person_ids:
            person_ids = set(person_ids)
            family_bins = family_bins.union(
                set(
                    self.ped_df[
                        self.ped_df["person_id"].isin(person_ids)
                    ].family_bin.values
                )
            )

        return self._build_partition_bin_heuristic_where(
            "family_bin", family_bins,
            self.partition_descriptor["family_bin_size"])

    def _build_return_reference_and_return_unknown(
        self, return_reference=None, _return_unknown=None
    ):
        allele_index_col = self.where_accessors["allele_index"]
        if not return_reference:
            return f"{allele_index_col} > 0"
        # return_unknown basically means return all so no specific where
        # expression is required
        return ""
