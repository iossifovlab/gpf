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
    'sex': StringQueryToTreeTransformerWrapper(
        token_converter=sex_converter),
    'inheritance': StringQueryToTreeTransformerWrapper(
        token_converter=inheritance_converter),
    'variant_type': StringQueryToTreeTransformerWrapper(
        token_converter=variant_type_converter),
    'family_ids': StringListQueryToTreeTransformer(),
}


stage_two_transformers = {
    'effect_type': QueryTreeToSQLListTransformer("effect_gene_types"),
    'genes': QueryTreeToSQLListTransformer("effect_gene_genes"),
    'personId': QueryTreeToSQLListTransformer("variant_in_members"),
    'roles': QueryTreeToSQLListTransformer("variant_in_roles"),
    'sex': QueryTreeToSQLListTransformer("variant_in_sexes"),
    'position': QueryTreeToSQLTransformer("S.position"),
    'chrom': QueryTreeToSQLTransformer("S.chrom"),
    'alternative': QueryTreeToSQLTransformer("S.alternative"),
    'family_ids': QueryTreeToSQLListTransformer('F.family_id'),
}


Q = """
    SELECT
        F.chrom as chrom_fv,
        F.position as position_fv,
        F.reference as reference_fv,
        F.alternative as alternative_fv,
        F.summary_index as summary_index_fv,
        F.allele_index as allele_index_fv,
        F.split_from_multi_allelic as split_from_multi_allelic_fv,
        F.family_id,
        F.genotype,
        F.inheritance,
        F.variant_in_members,
        F.variant_in_roles,
        F.variant_in_sexes,

        S.chrom,
        S.position,
        S.reference,
        S.alternative,
        S.summary_index,
        S.allele_index,
        S.split_from_multi_allelic,
        S.effect_type,
        S.effect_gene_genes,
        S.effect_gene_types,
        S.effect_details_transcript_ids,
        S.effect_details_details,
        S.af_parents_called_count,
        S.af_parents_called_percent,
        S.af_allele_count,
        S.af_allele_freq

    FROM parquet.`{family}` AS F FULL OUTER JOIN parquet.`{summary}` AS S
    ON S.summary_index = F.summary_index AND S.allele_index = F.allele_index
"""


AQ = """
    S.summary_index IN (SELECT
        S.summary_index
    FROM parquet.`{family}` AS F FULL OUTER JOIN parquet.`{summary}` AS S
    ON S.summary_index = F.summary_index AND S.allele_index = F.allele_index
    WHERE {where})
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
    for key, arg in kwargs.items():
        if arg is None:
            continue
        if key not in queries:
            continue

        stage_one = stage_one_transformers.get(
            key, StringQueryToTreeTransformerWrapper())
        stage_two = stage_two_transformers.get(
            key, QueryTreeToSQLTransformer(key))

        result.append(
            stage_two.transform(stage_one.parse_and_transform(arg))
        )
    return result


VARIANT_QUERIES = [
    'regions',
    'family_ids',
]

ALLELE_QUERIES = [
    'roles',
]


def thrift_query(thrift_connection, summary, family, limit=2000, **kwargs):
    final_query = Q.format(
        summary=summary,
        family=family,
    )

    variant_queries = []
    if 'regions' in kwargs and kwargs['regions'] is not None:
        regions = kwargs['regions']
        del kwargs['regions']
        variant_queries.append(regions_transformer(regions))

    variant_queries.extend(
        query_parts(VARIANT_QUERIES, **kwargs))

    allele_queries = query_parts(ALLELE_QUERIES, **kwargs)
    if allele_queries:
        where = ' AND '.join(["({})".format(q) for q in allele_queries])
        aq = AQ.format(
            summary=summary,
            family=family,
            where=where
        )
        variant_queries.append(aq)

    if variant_queries:
        final_query += "\nWHERE\n{}".format(
            ' AND '.join(["({})".format(q) for q in variant_queries])
        )

    if limit is not None:
        final_query += "\nLIMIT {}".format(limit)
    print(final_query)

    cursor = thrift_connection.cursor()
    cursor.execute(final_query)
    return as_pandas(cursor)
