from __future__ import print_function, unicode_literals, absolute_import

from builtins import str

# from impala.util import as_pandas

from RegionOperations import Region

from ..attributes_query import \
    QueryTreeToSQLTransformer, \
    QueryTreeToSQLListTransformer, \
    role_query, sex_query, \
    inheritance_query,\
    variant_type_query


# def thrift_query1(thrift_connection, tables, query, db='parquet',
#                   limit=2000):
#     builder = ThriftQueryBuilder(query, tables=tables, db=db)
#     sql_query = builder.build()

#     if 'limit' in query:
#         limit = query['limit']
#     if limit is not None:
#         sql_query += "\n\tLIMIT {}".format(limit)
#     print("FINAL QUERY", sql_query)
#     cursor = thrift_connection.cursor()
#     cursor.execute(sql_query)
#     return as_pandas(cursor)


class ThriftQueryBuilderBase(object):
    QUOTE = "'"
    WHERE = """
        WHERE
            {where}
    """

    def __init__(self, query, summary_schema, tables, db='parquet'):

        self.query = {k: v for k, v in query.items() if v is not None}
        self.summary_schema = summary_schema
        self.query_keys = set(query.keys())
        self.tables = tables
        self.db = 'parquet'

    def has_gene_effects(self):
        return self.query.get('effect_types') is not None \
            or self.query.get('genes') is not None

    def has_members(self):
        members_kw = set(['roles', 'person_ids', 'inheritance'])
        return len(members_kw & self.query_keys()) > 0

    def _build_where(self, where_parts):
        if not where_parts:
            return ""
        return self.WHERE.format(
            where=' AND '.join([
                '( {} )'.format(p) for p in where_parts
            ])
        )

    def _build_iterable_string_attr_where(self, attr_name, column_name):
        assert self.query[attr_name] is not None
        assert isinstance(self.query[attr_name], list) or \
            isinstance(self.query[attr_name], set)

        query = self.query[attr_name]
        if not query:
            where = ' {column_name} IS NULL'.format(
                column_name=column_name
            )
            return where
        else:
            values = [
                ' {q}{val}{q} '.format(
                    q=self.QUOTE,
                    val=val.replace("'", "\\'"))
                for val in query]

            where = ' {column_name} in ( {values} ) '.format(
                column_name=column_name,
                values=','.join(values))
            return where


class SummarySubQueryBuilder(ThriftQueryBuilderBase):
    Q = """
                    SELECT
                        DISTINCT S.bucket_index,
                            S.summary_variant_index,
                            S.allele_index
                    FROM
                        {db}.`{summary_variant}` AS S
                    {join_effect_gene}
                    WHERE
                        {where}
                    DISTRIBUTE BY
                        S.bucket_index, S.summary_variant_index
    """
    EFFECT_GENE_JOIN = """
                    LEFT JOIN
                        {db}.`{effect_gene_variant}` AS E
                    ON
                        E.bucket_index = S.bucket_index
                        AND E.summary_variant_index = S.summary_variant_index
                        AND E.allele_index = S.allele_index
    """

    def __init__(self, query, summary_schema, tables, db='parquet'):
        super(SummarySubQueryBuilder, self).__init__(
            query, summary_schema, tables, db)

    def _build_effect_type_where(self):
        return self._build_iterable_string_attr_where(
            'effect_types', 'E.effect_type'
        )

    def _build_genes_where(self):
        return self._build_iterable_string_attr_where(
            'genes', 'E.effect_gene'
        )

    def _build_gene_effects_where(self):
        assert self.has_gene_effects()
        where = []
        if 'effect_types' in self.query:
            where.append(self._build_effect_type_where())

        if 'genes' in self.query:
            where.append(self._build_genes_where())

        w = ' AND '.join(where)
        return w

    def _build_regions_where(self):
        assert 'regions' in self.query
        assert isinstance(self.query['regions'], list)
        where = []
        for region in self.query['regions']:
            assert isinstance(region, Region)
            where.append(
               "(S.chrom = {q}{chrom}{q} AND S.position >= {start} AND "
               "S.position <= {stop})"
               .format(
                    q=self.QUOTE, chrom=region.chrom, start=region.start,
                    stop=region.stop)
            )
        return ' OR '.join(where)

    def _build_variant_type_where(self):
        assert self.query.get('variant_type')
        parsed = self.query['variant_type']
        if isinstance(self.query['variant_type'], str):
            parsed = variant_type_query.transform_query_string_to_tree(
                        self.query['variant_type'])
        transformer = QueryTreeToSQLTransformer('S.variant_type')
        return transformer.transform(parsed)

    def _build_real_attr_where(self):
        assert self.query.get("real_attr_filter")
        real_attr_filter = self.query['real_attr_filter']
        query = []
        for attr_name, attr_range in real_attr_filter:
            assert attr_name in self.summary_schema
            assert self.summary_schema[attr_name] == 'double'
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

    def _build_summary_where(self):
        where = []
        if self.query.get('regions'):
            where.append(self._build_regions_where())
        if self.has_gene_effects():
            where.append(self._build_gene_effects_where())
        if self.query.get('variant_type'):
            where.append(self._build_variant_type_where())
        if self.query.get('real_attr_filter'):
            where.append(self._build_real_attr_where())
        if not where:
            return None
        return ' \n\tAND '.join(['( {} )'.format(w) for w in where])

    def build(self):
        where = self._build_summary_where()
        if where is None:
            return None
        join_effect_gene = ""
        if self.has_gene_effects():
            join_effect_gene = self.EFFECT_GENE_JOIN.format(
                db=self.db,
                effect_gene_variant=self.tables['effect_gene_variant']
            )

        q = self.Q.format(
            join_effect_gene=join_effect_gene,
            db=self.db,
            summary_variant=self.tables['summary_variant'],
            where=where
        )
        return q


class MemberSubQueryBuilder(ThriftQueryBuilderBase):

    def __init__(self, query, summary_schema, tables, db='parquet'):
        super(MemberSubQueryBuilder, self).__init__(
            query, summary_schema, tables, db)
        self.summary_query_builder = SummarySubQueryBuilder(
            query, summary_schema, tables, db)

    MEMBER_JOIN = """
        LEFT JOIN {db}.`{member_variant}` AS M
        ON
            F.bucket_index = M.bucket_index
            AND F.summary_variant_index = M.summary_variant_index
            AND F.allele_index = M.allele_index
            AND F.family_variant_index = M.family_variant_index
    """

    def _build_person_ids_where(self):
        return self._build_iterable_string_attr_where(
            'person_ids', 'M.member_variant'
        )

    def build_where(self):
        where_parts = []
        if self.query.get('person_ids'):
            where_parts.append(
                self._build_person_ids_where()
            )

        return where_parts

    def build_join(self):
        return self.MEMBER_JOIN.format(
            db=self.db,
            member_variant=self.tables['member_variant']
        )


class ThriftQueryBuilder(ThriftQueryBuilderBase):

    Q = """
        SELECT
            S.chrom,
            S.position,
            S.reference,
            S.alternative,
            S.bucket_index,
            S.summary_variant_index,
            S.allele_index,
            S.allele_count,
            S.variant_type,
            S.cshl_variant,
            S.cshl_position,
            S.effect_type,
            S.effect_gene_genes,
            S.effect_gene_types,
            S.effect_details_transcript_ids,
            S.effect_details_details,
            S.af_parents_called_count,
            S.af_parents_called_percent,
            S.af_allele_count,
            S.af_allele_freq,

            F.family_variant_index,
            F.family_id,
            F.genotype

        FROM {db}.`{family_variant}` AS F
        {join_member_variant}
        LEFT JOIN {db}.`{summary_variant}` AS S
        ON
            S.bucket_index = F.bucket_index AND
            S.summary_variant_index = F.summary_variant_index AND
            S.allele_index = F.allele_index
        {where}
        DISTRIBUTE BY
            S.bucket_index, S.summary_variant_index
    """

    def __init__(self, query, summary_schema, tables, db='parquet'):
        super(ThriftQueryBuilder, self).__init__(
            query, summary_schema, tables, db)
        self.summary_query_builder = SummarySubQueryBuilder(
            query, summary_schema, tables, db)
        self.member_query_builder = MemberSubQueryBuilder(
            query, summary_schema, tables, db)

    def _build_complex_where_with_array_attr(
            self, attr_name, column_name, attr_transformer):
        assert self.query[attr_name] is not None
        parsed = self.query[attr_name]
        if isinstance(self.query[attr_name], str):
            parsed = attr_transformer.transform_query_string_to_tree(
                    self.query[attr_name])
        transformer = QueryTreeToSQLListTransformer(column_name)
        return transformer.transform(parsed)

    def _build_sexes_where(self):
        return self._build_complex_where_with_array_attr(
            'sexes', 'F.variant_in_sexes', sex_query)

    def _build_roles_where(self):
        return self._build_complex_where_with_array_attr(
            'roles', 'F.variant_in_roles', role_query)

    def _build_inheritance_where(self):
        return self._build_complex_where_with_array_attr(
            'inheritance', 'F.inheritance_in_members', inheritance_query)

    @staticmethod
    def summary_schema_query(tables, db='parquet'):
        query = """
            CREATE TEMPORARY VIEW parquetTable
            USING org.apache.spark.sql.parquet
            OPTIONS (
                path "{summary_variant}"
            )
        """.format(
            db=db,
            summary_variant=tables['summary_variant'],
        )
        return [
            query,
            "DESCRIBE EXTENDED parquetTable"
        ]

    def build(self):

        where_parts = []
        summary_query = self.summary_query_builder.build()
        if summary_query is not None:
            w = """
                (S.bucket_index, S.summary_variant_index, S.allele_index) IN (
                    {summary_query}
                )
            """.format(summary_query=summary_query)
            where_parts.append(w)

        join_member_variant = ""
        member_where = self.member_query_builder.build_where()
        if member_where:
            where_parts.extend(member_where)
            join_member_variant = self.member_query_builder.build_join()

        if self.query.get('sexes'):
            where_parts.append(
                self._build_sexes_where()
            )

        if self.query.get('roles'):
            where_parts.append(
                self._build_roles_where()
            )

        if self.query.get('inheritance'):
            where_parts.append(
                self._build_inheritance_where()
            )

        if not self.query.get('return_reference'):
            where_parts.append("F.allele_index > 0")

        if 'family_ids' in self.query:
            where_parts.append(self._build_iterable_string_attr_where(
                'family_ids', 'F.family_id'
            ))

        query = self.Q.format(
            db=self.db,
            summary_variant=self.tables['summary_variant'],
            family_variant=self.tables['family_variant'],
            join_member_variant=join_member_variant,
            where=self._build_where(where_parts)
        )
        return query
