import logging

from abc import ABC, abstractmethod

from dae.variants.attributes import Inheritance
from dae.backends.attributes_query import inheritance_query

from dae.utils.regions import Region
import dae.utils.regions

from ..attributes_query import QueryTreeToSQLBitwiseTransformer, \
    role_query, sex_query, variant_type_query
from ..attributes_query_inheritance import InheritanceTransformer, \
    inheritance_parser


logger = logging.getLogger(__name__)


class BaseQueryBuilder(ABC):
    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """
    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000

    MAX_CHILD_NUMBER = 9999

    def __init__(
            self, db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=None):
        assert variants_schema is not None

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table
        self.table_properties = table_properties
        self.variants_columns = variants_schema.fields
        self.pedigree_columns = pedigree_schema
        self.ped_df = pedigree_df
        self.has_extra_attributes = \
            "extra_attributes" in self.variants_columns
        self._product = ""
        self.query_columns = self._query_columns()
        self.gene_models = gene_models
        self.where_accessors = self._where_accessors()

    def reset_product(self):
        self._product = ""

    @property
    def product(self):
        return self._product

    def _where_accessors(self):
        cols = list(self.variants_columns)
        accessors = {k: v for k, v in zip(cols, cols)}
        if "effect_types" not in accessors:
            accessors["effect_types"] = "effect_types"

        return accessors

    def build_select(self):
        columns = ", ".join(self.query_columns)
        select_clause = f"SELECT {columns}"
        self._add_to_product(select_clause)

    def build_from(self):
        from_clause = f"FROM {self.db}.{self.variants_table}"
        self._add_to_product(from_clause)

    @abstractmethod
    def build_join(self):
        pass

    def build_where(
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
            **kwargs):

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
            **kwargs):

        where = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["effect_gene_symbols"], genes
                )
            )
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["family_id"], family_ids)
            )
        if person_ids is not None:
            person_ids = set(person_ids) & set(self.families.persons.keys())
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["variant_in_members"], person_ids
                )
            )
        if effect_types is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    self.where_accessors["effect_types"], effect_types
                )
            )
        if inheritance is not None:
            where.extend(
                self._build_inheritance_where(
                    self.where_accessors["inheritance_in_members"], inheritance
                )
            )
        if roles is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["variant_in_roles"], roles, role_query
                )
            )
        if sexes is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["variant_in_sexes"], sexes, sex_query
                )
            )
        if variant_type is not None:
            where.append(
                self._build_bitwise_attr_where(
                    self.where_accessors["variant_type"],
                    variant_type,
                    variant_type_query
                )
            )
        if real_attr_filter is not None:
            where.append(self._build_real_attr_where(real_attr_filter))
        if frequency_filter is not None:
            where.append(
                self._build_real_attr_where(
                    frequency_filter, is_frequency=True))
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
                where=" AND ".join(["( {} )".format(w) for w in where])
            )

        return where_clause

    @abstractmethod
    def build_group_by(self):
        pass

    def build_limit(self, limit):
        if limit is not None:
            self._add_to_product(f"LIMIT {limit}")

    @abstractmethod
    def build_having(self, **kwargs):
        pass

    @abstractmethod
    def create_row_deserializer(self, serializer):
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
            if attr_name not in self.variants_columns:
                query.append("false")
                continue
            assert attr_name in self.variants_columns
            assert (
                self.variants_columns[attr_name].type == float
                or self.variants_columns[attr_name].type == int
            ), self.variants_columns[attr_name]
            left, right = attr_range
            attr_name = self.where_accessors[attr_name]
            if left is None and right is None:
                if not is_frequency:
                    query.append(
                        f"({attr_name} is not null)"
                    )
            elif left is None:
                assert right is not None
                query.append(
                    f"({attr_name} <= {right} or {attr_name} is null)")

            elif right is None:
                assert left is not None
                query.append("({} >= {})".format(attr_name, left))
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
            is_frequency=True
        )

    def _build_regions_where(self, regions):
        assert isinstance(regions, list), regions
        where = []
        for region in regions:
            assert isinstance(region, Region)
            end_position = "COALESCE(end_position, -1)"
            where.append(
                    "(`chromosome` = {q}{chrom}{q} AND "
                    "("
                    "(`position` >= {start} AND `position` <= {stop}) "
                    "OR "
                    "({end_position} >= {start} AND {end_position} <= {stop}) "
                    "OR "
                    "({start} >= `position` AND {stop} <= {end_position})"
                    "))".format(
                        q=self.QUOTE,
                        chrom=region.chrom,
                        start=region.start,
                        stop=region.stop,
                        end_position=end_position
                    )
            )
        return " OR ".join(where)

    def _build_iterable_string_attr_where(self, column_name, query_values):
        assert query_values is not None

        assert isinstance(query_values, list) or isinstance(
            query_values, set
        ), type(query_values)

        if not query_values:
            where = " {column_name} IS NULL".format(column_name=column_name)
            return where
        else:
            values = [
                " {q}{val}{q} ".format(
                    q=self.QUOTE, val=val.replace("'", "\\'")
                )
                for val in query_values
            ]

            where = []
            for i in range(0, len(values), self.MAX_CHILD_NUMBER):
                chunk_values = values[i: i + self.MAX_CHILD_NUMBER]

                w = " {column_name} in ( {values} ) ".format(
                    column_name=column_name, values=",".join(chunk_values)
                )

                where.append(w)

            where_clause = " OR ".join(["( {} )".format(w) for w in where])
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
        transformer = QueryTreeToSQLBitwiseTransformer(column_name)
        return transformer.transform(parsed)

    def _build_inheritance_where(self, column_name, query_value):
        trees = []
        if isinstance(query_value, str):
            tree = inheritance_parser.parse(query_value)
            trees.append(tree)

        elif isinstance(query_value, list):
            for qv in query_value:
                tree = inheritance_parser.parse(qv)
                trees.append(tree)

            # raise ValueError()
        else:
            tree = query_value
            trees.append(tree)

        result = []
        for tree in trees:
            transformer = InheritanceTransformer(column_name)
            res = transformer.transform(tree)
            result.append(res)
        return result

    def _build_gene_regions_heuristic(self, genes, regions):
        assert genes is not None
        if len(genes) > 0 and len(genes) <= self.GENE_REGIONS_HEURISTIC_CUTOFF:
            gene_regions = []
            for gs in genes:
                gene_model = self.gene_models.gene_models_by_gene_name(gs)
                if gene_model is None:
                    logger.warning(f"gene model for {gs} not found")
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
            logger.info(f"gene regions for {genes}: {gene_regions}")
            logger.info(f"input regions: {regions}")
            if not regions:
                regions = gene_regions
            else:
                result = []
                for gr in gene_regions:
                    for r in regions:
                        intersection = gr.intersection(r)
                        if intersection:
                            result.append(intersection)
                result = dae.utils.regions.collapse(result)
                logger.info(f"original regions: {regions}; result: {result}")
                regions = result

        return regions

    def _build_frequency_bin_heuristic(
            self, inheritance, ultra_rare, real_attr_filter):

        if "frequency_bin" not in self.variants_columns:
            return ""

        rare_boundary = self.table_properties["rare_boundary"]

        frequency_bin = set()
        frequency_bin_col = self.where_accessors["frequency_bin"]
        matchers = []
        if inheritance is not None:
            logger.debug(
                f"frequence_bin_heuristic inheritance: {inheritance} "
                f"({type(inheritance)})")
            if isinstance(inheritance, str):
                inheritance = [inheritance]

            matchers = [
                inheritance_query.transform_tree_to_matcher(
                    inheritance_query.transform_query_string_to_tree(inh))
                for inh in inheritance]

            if any([m.match([Inheritance.denovo]) for m in matchers]):
                frequency_bin.add(f"{frequency_bin_col} = 0")

        if inheritance is None or any([m.match(
            [Inheritance.mendelian,
                Inheritance.possible_denovo,
                Inheritance.possible_omission]) for m in matchers]):

            if ultra_rare:
                frequency_bin.update([
                    f"{frequency_bin_col} = 0",
                    f"{frequency_bin_col} = 1",
                ])
            elif real_attr_filter:
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

    def _build_coding_heuristic(self, effect_types):
        if effect_types is None:
            return ""
        if "coding_bin" not in self.variants_columns:
            return ""
        effect_types = set(effect_types)
        intersection = \
            effect_types & \
            set(self.table_properties["coding_effect_types"])

        logger.debug(
            f"coding bin heuristic for {self.variants_table}: "
            f"query effect types: {effect_types}; "
            f"coding_effect_types: "
            f"{self.table_properties['coding_effect_types']}; "
            f"=> {intersection == effect_types}")

        coding_bin_col = self.where_accessors["coding_bin"]

        if intersection == effect_types:
            return f"{coding_bin_col} = 1"
        if not intersection:
            return f"{coding_bin_col} = 0"
        return ""

    def _build_region_bin_heuristic(self, regions):
        if not regions or self.table_properties["region_length"] == 0:
            return ""

        chroms = set(self.table_properties["chromosomes"])

        region_length = self.table_properties["region_length"]
        region_bins = []
        for region in regions:
            if region.chrom in chroms:
                chrom_bin = region.chrom
            else:
                chrom_bin = "other"
            start = region.start // region_length
            stop = region.stop // region_length
            for position_bin in range(start, stop + 1):
                region_bins.append("{}_{}".format(chrom_bin, position_bin))
        if not region_bins:
            return ""
        region_bin_col = self.where_accessors["region_bin"]
        return "{region_bin} IN ({bins})".format(
            region_bin=region_bin_col,
            bins=",".join(["'{}'".format(rb) for rb in region_bins])
        )

    def _build_family_bin_heuristic(self, family_ids, person_ids):
        if "family_bin" not in self.variants_columns:
            return ""
        if "family_bin" not in self.pedigree_columns:
            return ""
        family_bins = set()
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

        family_bin_col = self.where_accessors["family_bin"]

        if 0 < len(family_bins) < self.table_properties["family_bin_size"]:
            w = ", ".join([str(fb) for fb in family_bins])
            return "{family_bin} IN ({w})".format(
                family_bin=family_bin_col, w=w)

        return ""

    def _build_return_reference_and_return_unknown(
        self, return_reference=None, return_unknown=None
    ):
        allele_index_col = self.where_accessors["allele_index"]
        if not return_reference:
            return f"{allele_index_col} > 0"
        elif not return_unknown:
            return f"{allele_index_col} >= 0"
        return ""
