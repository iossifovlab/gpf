from annotation.tools.file_io_parquet import ParquetSchema
from variants.family import FamiliesBase, Family
from backends.impala.parquet_io import ParquetSerializer

from impala.util import as_pandas

from RegionOperations import Region
import RegionOperations

from ..attributes_query import \
    QueryTreeToSQLBitwiseTransformer, \
    role_query, sex_query, \
    variant_type_query
from ..attributes_query_inheritance import InheritanceTransformer, \
    inheritance_parser

from variants.attributes import Role, Status, Sex


class ImpalaFamilyVariants(FamiliesBase):
    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """

    GENE_REGIONS_HEURISTIC_CUTOFF = 20
    GENE_REGIONS_HEURISTIC_EXTEND = 20000

    def __init__(self, config, impala_connection, gene_models=None):

        super(ImpalaFamilyVariants, self).__init__()

        assert config is not None
        self.config = config

        self.impala = impala_connection
        self.ped_df = self.load_pedigree()
        self.pedigree_schema = self.pedigree_schema()

        self.families_build(self.ped_df, family_class=Family)
        self.schema = self.variant_schema()
        self.serializer = ParquetSerializer(schema=self.schema)
        self.gene_models = gene_models

    def count_variants(self, **kwargs):
        with self.impala.cursor() as cursor:
            query = self.build_count_query(self.config, **kwargs)
            # print("COUNT QUERY:", query)
            cursor.execute(query)
            row = next(cursor)
            return row[0]

    def query_variants(
            self, regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None):

        with self.impala.cursor() as cursor:
            query = self.build_query(
                self.config,
                regions=regions, genes=genes, effect_types=effect_types,
                family_ids=family_ids, person_ids=person_ids,
                inheritance=inheritance, roles=roles, sexes=sexes,
                variant_type=variant_type, real_attr_filter=real_attr_filter,
                ultra_rare=ultra_rare,
                return_reference=return_reference,
                return_unknown=return_unknown,
                limit=limit)

            # print("FINAL QUERY: ", query)
            cursor.execute(query)
            for row in cursor:
                chrom, position, reference, alternatives_data, \
                    effect_data, family_id, genotype_data, \
                    frequency_data, genomic_scores_data, \
                    matched_alleles = row

                family = self.families.get(family_id)
                v = self.serializer.deserialize_variant(
                    family,
                    chrom, position, reference, alternatives_data,
                    effect_data, genotype_data,
                    frequency_data, genomic_scores_data
                )

                matched_alleles = [int(a) for a in matched_alleles.split(',')]
                v.set_matched_alleles(matched_alleles)

                yield v

    def load_pedigree(self):
        with self.impala.cursor() as cursor:
            q = """
                SELECT * FROM {db}.{pedigree}
            """.format(db=self.config.db, pedigree=self.config.tables.pedigree)

            cursor.execute(q)
            ped_df = as_pandas(cursor)

        ped_df = ped_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
            'sex': 'sex',
            'status': 'status',
            'role': 'role',
            'generated': 'generated',
            'layout': 'layout',
            'phenotype': 'phenotype',
        })
        ped_df.role = ped_df.role.apply(lambda v: Role(v))
        ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
        ped_df.status = ped_df.status.apply(lambda v: Status(v))
        if 'layout' in ped_df:
            ped_df.layout = ped_df.layout.apply(
                lambda v: v.split(':')[-1] if v is not None else v)

        return ped_df

    def variant_schema(self):
        with self.impala.cursor() as cursor:
            q = """
                DESCRIBE {db}.{variant}
            """.format(db=self.config.db, variant=self.config.tables.variant)

            cursor.execute(q)
            df = as_pandas(cursor)
            records = df[['name', 'type']].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }

            return ParquetSchema(schema)

    def pedigree_schema(self):
        with self.impala.cursor() as cursor:
            q = """
                DESCRIBE {db}.{pedigree}
            """.format(db=self.config.db, pedigree=self.config.tables.pedigree)

            cursor.execute(q)
            df = as_pandas(cursor)
            records = df[['name', 'type']].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def _build_real_attr_where(self, real_attr_filter):
        query = []
        for attr_name, attr_range in real_attr_filter:

            if attr_name not in self.schema:
                query.append('false')
                continue
            assert attr_name in self.schema
            assert self.schema[attr_name].type_py == float or \
                self.schema[attr_name].type_py == int, \
                self.schema[attr_name]
            left, right = attr_range
            if left is None:
                assert right is not None
                query.append("({} <= {})".format(attr_name, right))
            elif right is None:
                assert left is not None
                query.append("({} >= {})".format(attr_name, left))
            else:
                query.append(
                    "({attr} >= {left} AND {attr} <= {right})".format(
                        attr=attr_name, left=left, right=right))
        return ' AND '.join(query)

    def _build_ultra_rare_where(self, ultra_rare):
        assert ultra_rare
        return self._build_real_attr_where(
            real_attr_filter=[("af_allele_count", (1, 1))])

    def _build_regions_where(self, regions):
        assert isinstance(regions, list), regions
        where = []
        for region in regions:
            assert isinstance(region, Region)
            where.append(
               "(`chrom` = {q}{chrom}{q} AND `position` >= {start} AND "
               "`position` <= {stop})"
               .format(
                    q=self.QUOTE,
                    chrom=region.chrom,
                    start=region.start,
                    stop=region.stop)
            )
        return ' OR '.join(where)

    def _build_iterable_string_attr_where(self, column_name, query_values):
        assert query_values is not None

        assert isinstance(query_values, list) or \
            isinstance(query_values, set), type(query_values)

        if not query_values:
            where = ' {column_name} IS NULL'.format(
                column_name=column_name
            )
            return where
        else:
            values = [
                ' {q}{val}{q} '.format(
                    q=self.QUOTE,
                    val=val.replace("'", "\\'"))
                for val in query_values]

            where = ' {column_name} in ( {values} ) '.format(
                column_name=column_name,
                values=','.join(values))
            return where

    def _build_bitwise_attr_where(
            self, column_name, query_value, query_transformer):
        assert query_value is not None
        parsed = query_value
        if isinstance(query_value, str):
            parsed = query_transformer.transform_query_string_to_tree(
                    query_value)
        transformer = QueryTreeToSQLBitwiseTransformer(column_name)
        return transformer.transform(parsed)

    def _build_inheritance_where(self, column_name, query_value):
        tree = inheritance_parser.parse(query_value)
        transformer = InheritanceTransformer(column_name)
        res = transformer.transform(tree)
        return res

    def get_gene_models(self):
        if self.gene_models is None:
            from DAE import genomesDB
            self.gene_models = genomesDB.get_gene_models()
        return self.gene_models

    def _build_gene_regions_heuristic(self, genes, regions):
        assert genes is not None
        if len(genes) > 0 and len(genes) <= self.GENE_REGIONS_HEURISTIC_CUTOFF:
            if regions is None:
                regions = []
            gene_models = self.get_gene_models()
            for gs in genes:
                for gm in gene_models.gene_models_by_gene_name(gs):
                    regions.append(
                        Region(
                            gm.chr,
                            gm.tx[0] - self.GENE_REGIONS_HEURISTIC_EXTEND,
                            gm.tx[1] + self.GENE_REGIONS_HEURISTIC_EXTEND))
            if regions:
                regions = RegionOperations.collapse(regions)
            return regions

    def _build_rare_heuristic(self, ultra_rare, real_attr_filter):
        if 'rare' not in self.schema:
            return ""
        if ultra_rare:
            return "rare = 1"
        if real_attr_filter:
            for name, (begin, end) in real_attr_filter:
                if name == 'af_allele_freq':
                    if end <= 5.0:
                        return "rare = 1"
                    if begin > 5.0:
                        return "rare = 0"
        return ""

    def _build_ultra_rare_heuristic(self, ultra_rare):
        if 'ultra_rare' not in self.schema:
            return ""
        if ultra_rare:
            return "ultra_rare = 1"
        return ""

    def _build_family_bin_heuristic(self, family_ids, person_ids):
        if 'family_bin' not in self.schema:
            return ""
        if 'family_bin' not in self.pedigree_schema:
            return ""
        family_bins = set()
        if family_ids:
            family_ids = set(family_ids)
            family_bins.union(
                set(self.ped_df[
                        self.ped_df['family_id'].isin(family_ids)
                    ].family_bin.values)
            )
        if person_ids:
            person_ids = set(person_ids)
            family_bins.union(
                set(self.ped_df[
                        self.ped_df['person_id'].isin(person_ids)
                    ].family_bin.values)
            )

        if family_bins:
            w = ", ".join(family_bins)
            return "family_bin IN {w}".format(w=w)

        return ""

    def _build_return_reference_and_return_unknown(
            self, return_reference=None, return_unknown=None):
        if not return_reference:
            return "allele_index > 0"
        elif not return_unknown:
            return "allele_index >= 0"
        return ""

    def _build_where(
            self,
            regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None
            ):
        where = []
        if genes is not None:
            regions = self._build_gene_regions_heuristic(genes, regions)
            where.append(self._build_iterable_string_attr_where(
                'effect_gene', genes
            ))
        if regions is not None:
            where.append(self._build_regions_where(regions))
        if family_ids is not None:
            where.append(self._build_iterable_string_attr_where(
                'family_id', family_ids
            ))
        if person_ids is not None:
            where.append(self._build_iterable_string_attr_where(
                'variant_in_member', person_ids
            ))
        if effect_types is not None:
            where.append(self._build_iterable_string_attr_where(
                'effect_type', effect_types
            ))
        if inheritance is not None:
            where.append(self._build_inheritance_where(
                'variant_inheritance', inheritance
            ))
        if roles is not None:
            where.append(self._build_bitwise_attr_where(
                'variant_roles', roles,
                role_query
            ))
        if sexes is not None:
            where.append(self._build_bitwise_attr_where(
                'variant_sexes', sexes,
                sex_query
            ))
        if variant_type is not None:
            where.append(self._build_bitwise_attr_where(
                'variant_type', variant_type,
                variant_type_query
            ))
        if real_attr_filter is not None:
            where.append(self._build_real_attr_where(real_attr_filter))
        if ultra_rare:
            where.append(self._build_ultra_rare_where(ultra_rare))

        where.append(self._build_return_reference_and_return_unknown(
            return_reference, return_unknown
        ))
        where.append(self._build_rare_heuristic(ultra_rare, real_attr_filter))
        where.append(self._build_ultra_rare_heuristic(ultra_rare))
        where.append(self._build_family_bin_heuristic(family_ids, person_ids))

        where = [w for w in where if w]

        where_clause = ""

        if where:
            where_clause = self.WHERE.format(
                where=" AND ".join([
                    "( {} )".format(w) for w in where])
            )

        return where_clause

    def build_query(
            self, config,
            regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None):

        where_clause = self._build_where(
            regions=regions, genes=genes, effect_types=effect_types,
            family_ids=family_ids, person_ids=person_ids,
            inheritance=inheritance, roles=roles, sexes=sexes,
            variant_type=variant_type, real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            return_reference=return_reference,
            return_unknown=return_unknown)

        limit_clause = ""
        if limit:
            limit_clause = "LIMIT {}".format(limit)
        return """
            SELECT
                chrom,
                `position`,
                reference,
                alternatives_data,
                effect_data,
                family_id,
                genotype_data,
                frequency_data,
                genomic_scores_data,
                GROUP_CONCAT(DISTINCT CAST(allele_index AS string))
            FROM {db}.{variant}
            {where_clause}
            GROUP BY
                bucket_index,
                summary_variant_index,
                family_variant_index,
                chrom,
                `position`,
                reference,
                alternatives_data,
                effect_data,
                family_id,
                genotype_data,
                frequency_data,
                genomic_scores_data
            {limit_clause}
            """.format(
            db=config.db, variant=config.tables.variant,
            where_clause=where_clause,
            limit_clause=limit_clause)

    def build_count_query(
            self, config,
            regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None):

        where_clause = self._build_where(
            regions=regions, genes=genes, effect_types=effect_types,
            family_ids=family_ids, person_ids=person_ids,
            inheritance=inheritance, roles=roles, sexes=sexes,
            variant_type=variant_type, real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            return_reference=return_reference,
            return_unknown=return_unknown)

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
            db=config.db, variant=config.tables.variant,
            where_clause=where_clause)
