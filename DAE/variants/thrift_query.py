from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
import collections

from impala.util import as_pandas
from variants.attributes_query import StringQueryToTreeTransformerWrapper,\
    QueryTreeToSQLTransformer, QueryTreeToSQLListTransformer, \
    roles_converter, sex_converter, \
    inheritance_converter, variant_type_converter,\
    StringListQueryToTreeTransformer
from RegionOperations import Region

q = """
    SELECT * FROM parquet.`/data-raw-dev/pspark/family01` AS A
    INNER JOIN parquet.`/data-raw-dev/pspark/summary01` AS B
    ON
    A.chrom = B.chrom AND
    A.position = B.position AND
    A.alternative = B.alternative
    WHERE
"""


stage_one_transformers = {
    'roles': StringQueryToTreeTransformerWrapper(
        token_converter=roles_converter),
    'sexes': StringQueryToTreeTransformerWrapper(
        token_converter=sex_converter),
    'inheritance': StringQueryToTreeTransformerWrapper(
        token_converter=inheritance_converter),
    'variant_type': StringQueryToTreeTransformerWrapper(
        token_converter=variant_type_converter),
    'family_ids': StringListQueryToTreeTransformer(),
    'person_ids': StringQueryToTreeTransformerWrapper(),
}


stage_two_transformers = {
    'effect_types': QueryTreeToSQLListTransformer("S.effect_gene_types"),
    'genes': QueryTreeToSQLListTransformer("S.effect_gene_genes"),
    'person_ids': QueryTreeToSQLListTransformer("F.variant_in_members"),
    'roles': QueryTreeToSQLListTransformer("F.variant_in_roles"),
    'sexes': QueryTreeToSQLListTransformer("F.variant_in_sexes"),
    'inheritance': QueryTreeToSQLListTransformer("inheritance_in_members"),
    'variant_type': QueryTreeToSQLTransformer("variant_type"),
    'position': QueryTreeToSQLTransformer("S.position"),
    'chrom': QueryTreeToSQLTransformer("S.chrom"),
    'alternative': QueryTreeToSQLTransformer("S.alternative"),
    'family_ids': QueryTreeToSQLListTransformer('F.family_id'),
}


Q = """
    SELECT
        S.chrom,
        S.position,
        S.reference,
        S.alternative,
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

    FROM parquet.`{family_variant}` AS F
    LEFT JOIN parquet.`{summary_variant}` AS S
    ON
        S.bucket_index = F.bucket_index AND
        S.summary_variant_index = F.summary_variant_index AND
        S.allele_index = F.allele_index
"""


def region_transformer(r):
    assert isinstance(r, Region)
    return "(S.chrom = {} AND S.position >= {} AND S.position <= {})".format(
        r.chr, r.start, r.stop)


def regions_transformer(rs):
    assert all([isinstance(r, Region) for r in rs])
    return " OR ".join([region_transformer(r) for r in rs])


def query_parts(queries, **kwargs):
    result = []
    for key, arg in list(kwargs.items()):
        if arg is None:
            continue
        if key not in queries:
            continue

        stage_one = stage_one_transformers.get(
            key, StringQueryToTreeTransformerWrapper())
        stage_two = stage_two_transformers.get(
            key, QueryTreeToSQLTransformer(key))

        print("arg", key, type(arg), arg, isinstance(arg, str))

        if isinstance(arg, collections.Iterable) and not isinstance(arg, str):
            arg = 'any({})'.format(','.join(arg))

        if isinstance(arg, str):
            result.append(
                stage_two.transform(stage_one.parse_and_transform(arg))
            )
            # result.append()
        else:
            result.append(stage_two.transform(arg))
    return result


VARIANT_QUERIES = [
    # 'regions',
    'family_ids',
    'effect_types',
    'genes',
    'variant_type',
    'person_ids',
    'roles',
    'sexes',
    'inheritance',
]


def thrift_query(
        thrift_connection,
        summary_variant, family_variant,
        limit=2000, **kwargs):

    final_query = Q.format(
        summary_variant=summary_variant,
        family_variant=family_variant,
    )

    variant_queries = []
    if 'regions' in kwargs and kwargs['regions'] is not None:
        regions = kwargs.pop('regions')
        variant_queries.append(regions_transformer(regions))

    variant_queries.extend(
        query_parts(VARIANT_QUERIES, **kwargs))

    return_reference = kwargs.get("return_reference", False)
    if not return_reference:
        aq = "F.allele_index > 0"
        variant_queries.append(aq)

    if variant_queries:
        print(variant_queries)
        final_query += "\nWHERE\n{}".format(
            ' AND '.join(["({})".format(q) for q in variant_queries])
        )

    if limit is not None:
        final_query += "\nLIMIT {}".format(limit)

    # print()
    # print()
    # print()
    # print()
    print("FINAL QUERY", final_query)
    cursor = thrift_connection.cursor()
    cursor.execute(final_query)
    return as_pandas(cursor)


def thrift_query1(thrift_connection, tables, query, db='parquet', limit=2000):
    builder = ThriftQueryBuilder(query, tables=tables, db=db)
    sql_query = builder.build()

    if limit is not None:
        sql_query += "\n\tLIMIT {}".format(limit)
    print("FINAL QUERY", sql_query)
    cursor = thrift_connection.cursor()
    cursor.execute(sql_query)
    return as_pandas(cursor) 


class ThriftQueryBuilder(object):
    QUOTE = "'"

    def __init__(self, query, tables, db='parquet'):

        self.query = {k: v for k, v in query.items() if v is not None}
        self.query_keys = set(query.keys())
        self.tables = tables
        self.db = 'parquet'

    def has_gene_effects(self):
        return self.query.get('effect_types') or self.query.get('genes')

    def has_members(self):
        members_kw = set(['roles', 'sexes', 'person_ids', 'inheritance'])
        return len(members_kw & self.query_keys()) > 0

    def _build_effect_type_where(self):
        assert self.query['effect_types']
        assert isinstance(self.query['effect_types'], list)
        where = [
            ' {q}{ef}{q} '.format(q=self.QUOTE, ef=ef)
            for ef in self.query['effect_types']]
        where = ' E.effect_type in ( {} ) '.format(','.join(where))
        return where

    def _build_genes_where(self):
        assert self.query['genes']
        assert isinstance(self.query['genes'], list) or \
            isinstance(self.query['genes'], set)
        where = [
            ' {q}{sym}{q} '.format(q=self.QUOTE, sym=sym.upper())
            for sym in self.query['genes']]
        where = ' E.effect_gene in ( {} ) '.format(','.join(where))
        return where

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

    def _build_summary_where(self):
        where = []
        if self.query.get('regions'):
            where.append(self._build_regions_where())
        if self.has_gene_effects():
            where.append(self._build_gene_effects_where())

        if not where:
            return None
        return ' \n\tAND '.join(['( {} )'.format(w) for w in where])

    def query_summary_subquery(self):
        where = self._build_summary_where()
        if where is None:
            return None
        join_effect_gene = ""
        if self.has_gene_effects():
            join_effect_gene = """
        LEFT JOIN
            {db}.`{effect_gene_variant}` AS E
        ON
            E.bucket_index = S.bucket_index
            AND E.summary_variant_index = S.summary_variant_index
            AND E.allele_index = S.allele_index
            """.format(
                db=self.db,
                effect_gene_variant=self.tables['effect_gene_variant']
            )

        q = """
        SELECT
            DISTINCT S.bucket_index, S.summary_variant_index, S.allele_index
        FROM
            {db}.`{summary_variant}` AS S
        {join_effect_gene}
        WHERE
            {where}
        DISTRIBUTE BY
            S.bucket_index, S.summary_variant_index
        """.format(
            join_effect_gene=join_effect_gene,
            db=self.db,
            summary_variant=self.tables['summary_variant'],
            where=where
        )
        return q

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
    W = """
        WHERE
            {where}
    """

    def _build_where(self, where_parts):
        if not where_parts:
            return ""
        return self.W.format(
            where=' AND '.join([
                '( {} )'.format(p) for p in where_parts
            ])
        )

    JOIN_MEMBER = """
        LEFT JOIN {db}.`{member_variant}` AS M
        ON
            F.bucket_index = M.bucket_index AND
            F.summary_variant_index = M.summary_variant_index AND
            F.allele_index = M.allele_index AND
            F.family_variant_index = M.family_variant_index
    """

    def build(self):
        where_parts = []
        summary_query = self.query_summary_subquery()
        if summary_query is not None:
            w = """
            (S.bucket_index, S.summary_variant_index, S.allele_index) IN (
                {summary_query}
            )
            """.format(summary_query=summary_query)
            where_parts.append(w)

        join_member_variant = ""
        member_query = self.query_member_subquery()
        if member_query is not None:
            where_parts.append(member_query)
            join_member_variant = self.JOIN_MEMBER.format(
                db=self.db,
                member_variant=self.tables['member_variant']
            )

        query = self.Q.format(
            db=self.db,
            summary_variant=self.tables['summary_variant'],
            family_variant=self.tables['family_variant'],
            join_member_variant=join_member_variant,
            where=self._build_where(where_parts)
        )
        return query

    def query_member_subquery(self):
        pass
