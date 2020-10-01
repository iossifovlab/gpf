import logging
from contextlib import closing

from deprecation import deprecated
from impala.util import as_pandas

from dae.variants.attributes import Inheritance
from dae.backends.attributes_query import inheritance_query
from dae.backends.raw.raw_variants import RawVariantsIterator

from dae.annotation.tools.file_io_parquet import ParquetSchema
from dae.pedigrees.family import FamiliesData
from dae.backends.impala.serializers import AlleleParquetSerializer


from dae.utils.regions import Region
import dae.utils.regions

from ..attributes_query import QueryTreeToSQLBitwiseTransformer, \
    role_query, sex_query, variant_type_query
from ..attributes_query_inheritance import InheritanceTransformer, \
    inheritance_parser

from dae.variants.attributes import Role, Status, Sex


LOGGER = logging.getLogger(__name__)


class ImpalaFamilyVariants:
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
            impala_helpers,
            db,
            variants_table,
            pedigree_table,
            gene_models=None):

        super(ImpalaFamilyVariants, self).__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table

        self._impala_helpers = impala_helpers
        self.pedigree_schema = self._fetch_pedigree_schema()
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)

        self.schema = self._fetch_variant_schema()
        self.has_extra_attributes = "extra_attributes" in self.schema.columns
        if self.variants_table:
            self.serializer = AlleleParquetSerializer(self.schema)

        assert gene_models is not None
        self.gene_models = gene_models

        self.region_length = 0
        self.chromosomes = []
        self.family_bin_size = 0
        self.coding_effect_types = []
        self.rare_boundary = 0
        self._fetch_tblproperties()

    def count_variants(self, **kwargs):
        if not self.variants_table:
            return 0
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = self.build_count_query(**kwargs)
                cursor.execute(query)
                row = next(cursor)
                return row[0]

    def connection(self):
        return self._impala_helpers.connection()

    def _summary_variants_iterator(
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
            limit=None):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:

            with conn.cursor() as cursor:
                query = self.build_query(
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
                    limit=None,
                )
                LOGGER.debug(f"FINAL QUERY: {query}")

                seen = set()

                cursor.execute(query)
                for row in cursor:
                    if self.has_extra_attributes:
                        (
                            bucket_index,
                            summary_index,
                            # family_index,
                            chrom,
                            position,
                            end_position,
                            variant_type,
                            reference,
                            family_id,
                            variant_data,
                            extra_attributes,
                        ) = row
                    else:
                        (
                            bucket_index,
                            summary_index,
                            # family_index,
                            chrom,
                            position,
                            end_position,
                            variant_type,
                            reference,
                            family_id,
                            variant_data,
                        ) = row

                        extra_attributes = None

                    # FIXME:
                    # fvuid = f"{bucket_index}:{summary_index}:{family_index}"
                    fvuid = f"{bucket_index}:{summary_index}:{family_id}"
                    if fvuid in seen:
                        continue
                    seen.add(fvuid)

                    if type(variant_data) == str:
                        LOGGER.debug(
                            f"variant_data is string!!!! "
                            f"{family_id}, {chrom}, "
                            f"{position}, {end_position}, {reference}")
                        variant_data = bytes(variant_data, "utf8")
                    if type(extra_attributes) == str:
                        LOGGER.debug(
                            f"extra_attributes is string!!!! "
                            f"{family_id}, {chrom}, "
                            f"{position}, {end_position}, {reference}")
                        extra_attributes = bytes(extra_attributes, "utf8")

                    v = self.serializer.deserialize_summary_variant(
                        variant_data, extra_attributes
                    )

                    if v is None:
                        continue

                    yield v

    def _family_variants_iterator(
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
            limit=None):

        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:

            with conn.cursor() as cursor:
                query = self.build_query(
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
                    limit=None,
                )
                LOGGER.debug(f"FINAL QUERY: {query}")

                seen = set()

                cursor.execute(query)
                for row in cursor:
                    if self.has_extra_attributes:
                        (
                            bucket_index,
                            summary_index,
                            # family_index,
                            chrom,
                            position,
                            end_position,
                            variant_type,
                            reference,
                            family_id,
                            variant_data,
                            extra_attributes,
                        ) = row
                    else:
                        (
                            bucket_index,
                            summary_index,
                            # family_index,
                            chrom,
                            position,
                            end_position,
                            variant_type,
                            reference,
                            family_id,
                            variant_data,
                        ) = row

                        extra_attributes = None

                    # FIXME:
                    # fvuid = f"{bucket_index}:{summary_index}:{family_index}"
                    fvuid = f"{bucket_index}:{summary_index}:{family_id}"
                    if fvuid in seen:
                        continue
                    seen.add(fvuid)

                    if type(variant_data) == str:
                        LOGGER.debug(
                            f"variant_data is string!!!! "
                            f"{family_id}, {chrom}, "
                            f"{position}, {end_position}, {reference}")
                        variant_data = bytes(variant_data, "utf8")
                    if type(extra_attributes) == str:
                        LOGGER.debug(
                            f"extra_attributes is string!!!! "
                            f"{family_id}, {chrom}, "
                            f"{position}, {end_position}, {reference}")
                        extra_attributes = bytes(extra_attributes, "utf8")

                    family = self.families[family_id]
                    v = self.serializer.deserialize_family_variant(
                        variant_data, family, extra_attributes
                    )

                    if v is None:
                        continue

                    yield v

    def query_summary_variants(
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
            limit=None):
        if not self.variants_table:
            return None

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        summary_variants_iterator = self._summary_variants_iterator(
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
                    limit=limit)

        raw_variants_iterator = RawVariantsIterator(
            summary_variants_iterator, self.families)

        result = raw_variants_iterator.query_variants(
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
            limit=count)

        for v in result:
            if v is None:
                continue
            yield v
            count -= 1
            if count == 0:
                break

    def query_variants(
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
            limit=None):

        if not self.variants_table:
            return None

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        family_variants_iterator = self._family_variants_iterator(
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
                    limit=limit)

        raw_variants_iterator = RawVariantsIterator(
            family_variants_iterator, self.families)

        result = raw_variants_iterator.query_variants(
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
            limit=count)

        for v in result:
            if v is None:
                continue
            yield v
            count -= 1
            if count == 0:
                break

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    SELECT * FROM {db}.{pedigree}
                """.format(
                    db=self.db, pedigree=self.pedigree_table
                )

                cursor.execute(q)
                ped_df = as_pandas(cursor)

        ped_df = ped_df.rename(
            columns={
                "personId": "person_id",
                "familyId": "family_id",
                "momId": "mom_id",
                "dadId": "dad_id",
                "sampleId": "sample_id",
                "sex": "sex",
                "status": "status",
                "role": "role",
                "generated": "generated",
                "layout": "layout",
                "phenotype": "phenotype",
            }
        )
        ped_df.role = ped_df.role.apply(lambda v: Role(v))
        ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
        ped_df.status = ped_df.status.apply(lambda v: Status(v))

        return ped_df

    def _fetch_variant_schema(self):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    DESCRIBE {db}.{variant}
                """.format(
                    db=self.db, variant=self.variants_table
                )

                cursor.execute(q)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return ParquetSchema(schema)

    def _fetch_pedigree_schema(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    DESCRIBE {db}.{pedigree}
                """.format(
                    db=self.db, pedigree=self.pedigree_table
                )

                cursor.execute(q)
                df = as_pandas(cursor)
                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema

    def _fetch_tblproperties(self):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DESCRIBE EXTENDED {self.db}.{self.variants_table}")
                rows = list(cursor)
                properties_start, properties_end = -1, -1
                for row_index, row in enumerate(rows):
                    if row[0].strip() == "Table Parameters:":
                        properties_start = row_index + 1

                    if (
                        properties_start != -1
                        and row[0] == ""
                        and row[1] is None
                        and row[2] is None
                    ):
                        properties_end = row_index + 1

                if properties_start == -1:
                    LOGGER.debug("No partitioning found")
                    return

                for index in range(properties_start, properties_end):
                    prop_name = rows[index][1]
                    prop_value = rows[index][2]
                    if prop_name == \
                            "gpf_partitioning_region_bin_region_length":
                        self.region_length = int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_region_bin_chromosomes":
                        self.chromosomes = prop_value.split(",")
                        self.chromosomes = \
                            list(map(str.strip, self.chromosomes))
                    elif prop_name == \
                            "gpf_partitioning_family_bin_family_bin_size":
                        self.family_bin_size = int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_coding_bin_coding_effect_types":
                        self.coding_effect_types = prop_value.split(",")
                        self.coding_effect_types = list(
                            map(str.strip, self.coding_effect_types))
                    elif prop_name == \
                            "gpf_partitioning_frequency_bin_rare_boundary":
                        self.rare_boundary = int(prop_value)

    def _build_real_attr_where(self, real_attr_filter, is_frequency=False):
        query = []
        for attr_name, attr_range in real_attr_filter:
            if attr_name not in self.schema:
                query.append("false")
                continue
            assert attr_name in self.schema
            assert (
                self.schema[attr_name].type_py == float
                or self.schema[attr_name].type_py == int
            ), self.schema[attr_name]
            left, right = attr_range
            if left is None and right is None:
                if not is_frequency:
                    query.append(
                        f"({attr_name} is not null)"
                    )
            elif left is None:
                assert right is not None
                if is_frequency:
                    query.append(
                        f"({attr_name} <= {right} or {attr_name} is null)")
                else:
                    query.append(
                        f"({attr_name} <= {right})")

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
            where.append(
                "(`chromosome` = {q}{chrom}{q} AND `position` >= {start} AND "
                "`position` <= {stop})".format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    start=region.start,
                    stop=region.stop,
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
        if isinstance(query_value, str):
            tree = inheritance_parser.parse(query_value)
        else:
            tree = query_value

        # if query_value == "denovo":
        #     pass

        transformer = InheritanceTransformer(column_name)
        res = transformer.transform(tree)
        return res

    def _build_gene_regions_heuristic(self, genes, regions):
        assert genes is not None
        if len(genes) > 0 and len(genes) <= self.GENE_REGIONS_HEURISTIC_CUTOFF:
            if regions is None:
                regions = []
            for gs in genes:
                for gm in self.gene_models.gene_models_by_gene_name(gs):
                    regions.append(
                        Region(
                            gm.chrom,
                            gm.tx[0] - self.GENE_REGIONS_HEURISTIC_EXTEND,
                            gm.tx[1] + self.GENE_REGIONS_HEURISTIC_EXTEND,
                        )
                    )
            if regions:
                regions = dae.utils.regions.collapse(regions)
            return regions

    @deprecated(
        details="'rare' heuristic is deprecated in favor of 'frequency_bin'"
        " heuristic"
    )
    def _build_rare_heuristic(self, ultra_rare, real_attr_filter):
        if "rare" not in self.schema:
            return ""
        if ultra_rare:
            return "rare = 1"
        if real_attr_filter:
            for name, (begin, end) in real_attr_filter:
                if name == "af_allele_freq":
                    if end <= 5.0:
                        return "rare = 1"
                    if begin > 5.0:
                        return "rare = 0"
        return ""

    def _build_frequency_bin_heuristic(
            self, inheritance, ultra_rare, real_attr_filter):

        if "frequency_bin" not in self.schema:
            return ""

        frequency_bin = set()
        if inheritance is not None:
            matcher = inheritance_query.transform_tree_to_matcher(
                inheritance_query.transform_query_string_to_tree(inheritance))

            if matcher.match([Inheritance.denovo]):
                frequency_bin.add("frequency_bin = 0")

        if inheritance is None or matcher.match(
            [Inheritance.mendelian,
                Inheritance.possible_denovo,
                Inheritance.possible_omission]):

            if ultra_rare:
                frequency_bin.update([
                    # "frequency_bin = 0",
                    "frequency_bin = 1"
                ])
            elif real_attr_filter:
                for name, (begin, end) in real_attr_filter:
                    if name == "af_allele_freq":

                        if end and end < self.rare_boundary:
                            frequency_bin.update([
                                "frequency_bin = 1",
                                "frequency_bin = 2"])
                        elif begin >= self.rare_boundary:
                            frequency_bin.add("frequency_bin = 3")
                        elif end is not None and end >= self.rare_boundary:
                            frequency_bin.update([
                                "frequency_bin = 1",
                                "frequency_bin = 2",
                                "frequency_bin = 3",
                            ])

            elif inheritance is not None:
                frequency_bin.update([
                    "frequency_bin = 1",
                    "frequency_bin = 2",
                    "frequency_bin = 3"])

        if len(frequency_bin) == 4:
            return ""
        return " OR ".join(frequency_bin)

    def _build_coding_heuristic(self, effect_types):
        if effect_types is None:
            return ""
        if "coding_bin" not in self.schema:
            return ""
        effect_types = set(effect_types)
        intersection = effect_types & set(self.coding_effect_types)
        if intersection == effect_types:
            return "coding_bin = 1"
        if not intersection:
            return "coding_bin = 0"
        return ""

    @deprecated(
        details="'chorm_bin' heuristic is deprecated in favor of 'region_bin' "
        "heuristic"
    )
    def _build_chrom_bin_heuristic(self, regions):
        if not regions:
            return ""
        if "chrom_bin" not in self.schema:
            return ""
        chroms = ["chr{}".format(c) for c in range(1, 23)]
        chroms.append("chrX")
        chroms = set(chroms)
        region_chroms = set(
            [r.chrom if r.chrom in chroms else "other" for r in regions]
        )

        chrom_bins = ",".join(region_chroms)
        return "chrom_bin IN ({chrom_bins})".format(chrom_bins=chrom_bins)

    def _build_region_bin_heuristic(self, regions):
        if not regions or self.region_length == 0:
            return ""

        chroms = set(self.chromosomes)

        region_length = self.region_length
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
        return "region_bin IN ({})".format(
            ",".join(["'{}'".format(rb) for rb in region_bins])
        )

    def _build_family_bin_heuristic(self, family_ids, person_ids):
        if "family_bin" not in self.schema:
            return ""
        if "family_bin" not in self.pedigree_schema:
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

        if 0 < len(family_bins) < self.family_bin_size:
            w = ", ".join([str(fb) for fb in family_bins])
            return "family_bin IN ({w})".format(w=w)

        return ""

    def _build_return_reference_and_return_unknown(
        self, return_reference=None, return_unknown=None
    ):
        if not return_reference:
            return "allele_index > 0"
        elif not return_unknown:
            return "allele_index >= 0"
        return ""

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
    ):
        where = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            where.append(
                self._build_iterable_string_attr_where(
                    "effect_gene_symbols", genes
                )
            )
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            where.append(
                self._build_iterable_string_attr_where("family_id", family_ids)
            )
        if person_ids is not None:
            person_ids = set(person_ids) & set(self.families.persons.keys())
            where.append(
                self._build_iterable_string_attr_where(
                    "variant_in_members", person_ids
                )
            )
        if effect_types is not None:
            where.append(
                self._build_iterable_string_attr_where(
                    "effect_types", effect_types
                )
            )
        if inheritance is not None:
            where.append(
                self._build_inheritance_where(
                    "inheritance_in_members", inheritance
                )
            )
        if roles is not None:
            where.append(
                self._build_bitwise_attr_where(
                    "variant_in_roles", roles, role_query
                )
            )
        if sexes is not None:
            where.append(
                self._build_bitwise_attr_where(
                    "variant_in_sexes", sexes, sex_query
                )
            )
        if variant_type is not None:
            where.append(
                self._build_bitwise_attr_where(
                    "variant_type", variant_type, variant_type_query
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

    def build_query(
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
            limit=None):

        where_clause = self._build_where(
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

        limit_clause = ""
        if limit:
            limit_clause = "LIMIT {}".format(limit)
        if self.has_extra_attributes:
            return """
                SELECT
                    bucket_index,
                    summary_index,
                    chromosome,
                    `position`,
                    end_position,
                    variant_type,
                    reference,
                    family_id,
                    variant_data,
                    extra_attributes
                FROM {db}.{variant}
                {where_clause}
                {limit_clause}
                """.format(
                db=self.db,
                variant=self.variants_table,
                where_clause=where_clause,
                limit_clause=limit_clause,
            )
        else:
            return """
                SELECT
                    bucket_index,
                    summary_index,
                    chromosome,
                    `position`,
                    end_position,
                    variant_type,
                    reference,
                    family_id,
                    variant_data
                FROM {db}.{variant}
                {where_clause}
                {limit_clause}
                """.format(
                db=self.db,
                variant=self.variants_table,
                where_clause=where_clause,
                limit_clause=limit_clause,
            )

    def build_count_query(
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
        return_reference=None,
        return_unknown=None,
        limit=None,
    ):

        where_clause = self._build_where(
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
            return_reference=return_reference,
            return_unknown=return_unknown,
        )

        return """
            SELECT
                COUNT(
                    DISTINCT
                        bucket_index,
                        summary_variant_index,
                        family_variant_index
                )
            FROM {db}.{variant}
            {where_clause}
            """.format(
            db=self.db, variant=self.variants_table, where_clause=where_clause
        )
