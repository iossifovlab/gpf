from variants.family import FamiliesBase, Family
from backends.impala.parquet_io import ParquetSerializer

from impala.util import as_pandas

from RegionOperations import Region

from ..attributes_query import \
    QueryTreeToSQLBitwiseTransformer, \
    role_query, sex_query, \
    inheritance_query,\
    variant_type_query

from variants.attributes import Role, Status, Sex


class ImpalaFamilyVariants(FamiliesBase):
    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """

    def __init__(self, config, impala_connection):

        super(ImpalaFamilyVariants, self).__init__()

        assert config is not None
        self.config = config

        self.impala = impala_connection
        self.ped_df = self.load_pedigree()
        self.families_build(self.ped_df, family_class=Family)
        self.schema = self.variants_schema()
        self.serializer = ParquetSerializer(self.families)

    def query_variants(self, **kwargs):
        with self.impala.cursor() as cursor:
            query = self.build_query(self.config, **kwargs)
            # print("FINAL QUERY: ", query)
            cursor.execute(query)
            for row in cursor:

                chrom, position, reference, alternatives_data, \
                    effect_data, family_id, genotype_data, frequency_data, \
                    matched_alleles = row

                family = self.families.get(family_id)
                v = self.serializer.deserialize_variant(
                    family,
                    chrom, position, reference, alternatives_data,
                    effect_data, genotype_data, frequency_data
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
            ped_df.layout = ped_df.layout.apply(lambda v: v.split(':')[-1])

        return ped_df

    def variants_schema(self):
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
            return schema

    def _build_real_attr_where(self, query):
            assert query.get("real_attr_filter")
            real_attr_filter = query['real_attr_filter']
            query = []
            for attr_name, attr_range in real_attr_filter:
                if attr_name not in self.schema:
                    query.append('false')
                    continue
                assert attr_name in self.schema
                assert self.schema[attr_name] == 'double'
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

    def _build_regions_where(self, query_values):
        assert isinstance(query_values, list)
        where = []
        for region in query_values:
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
            isinstance(query_values, set)

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

    def _build_where(self, query):
        where = []
        if query.get('regions'):
            where.append(self._build_regions_where(query['regions']))
        if query.get('family_ids') is not None:
            where.append(self._build_iterable_string_attr_where(
                'family_id', query['family_ids']
            ))
        if query.get('person_ids') is not None:
            where.append(self._build_iterable_string_attr_where(
                'variant_in_member', query['person_ids']
            ))
        if query.get('effect_types') is not None:
            where.append(self._build_iterable_string_attr_where(
                'effect_type', query['effect_types']
            ))
        if query.get('genes') is not None:
            where.append(self._build_iterable_string_attr_where(
                'effect_gene', query['genes']
            ))
        if query.get("inheritance"):
            where.append(self._build_bitwise_attr_where(
                'variant_inheritance', query['inheritance'],
                inheritance_query
            ))
        if query.get("roles"):
            where.append(self._build_bitwise_attr_where(
                'variant_roles', query['roles'],
                role_query
            ))
        if query.get("sexes"):
            where.append(self._build_bitwise_attr_where(
                'variant_sexes', query['sexes'],
                sex_query
            ))
        if query.get("variant_type"):
            where.append(self._build_bitwise_attr_where(
                'variant_type', query['variant_type'],
                variant_type_query
            ))
        if query.get('real_attr_filter'):
            where.append(self._build_real_attr_where(query))
            
        return where

    def build_query(self, config, **kwargs):

        where = self._build_where(kwargs)
        where_clause = ""
        if where:
            where_clause = self.WHERE.format(
                where=" AND ".join([
                    "( {} )".format(w) for w in where])
            )
        limit_clause = ""
        if kwargs.get("limit"):
            limit_clause = "LIMIT {}".format(kwargs.get("limit"))

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
                frequency_data
            {limit_clause}
            """.format(
            db=config.db, variant=config.tables.variant,
            where_clause=where_clause,
            limit_clause=limit_clause)
