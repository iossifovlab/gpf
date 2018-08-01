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
    'effect_types': QueryTreeToSQLListTransformer("effect_gene_types"),
    'genes': QueryTreeToSQLListTransformer("effect_gene_genes"),
    'person_ids': QueryTreeToSQLListTransformer("variant_in_members"),
    'roles': QueryTreeToSQLListTransformer("variant_in_roles"),
    'sexes': QueryTreeToSQLListTransformer("variant_in_sexes"),
    'inheritance': QueryTreeToSQLListTransformer("inheritance_in_members"),
    'variant_type': QueryTreeToSQLTransformer("variant_type"),
    'position': QueryTreeToSQLTransformer("S.position"),
    'chrom': QueryTreeToSQLTransformer("S.chrom"),
    'alternative': QueryTreeToSQLTransformer("S.alternative"),
    'family_ids': QueryTreeToSQLListTransformer('F.family_id'),
}


Q = """
    SELECT
        F.family_variant_index,
        F.family_id,
        F.genotype,

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
        S.af_allele_freq

    FROM parquet.`{family_alleles}` AS F
    LEFT JOIN parquet.`{summary_variants}` AS S
    ON
        S.chrom = F.chrom AND
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
        summary_variants, family_alleles,
        limit=2000, **kwargs):
    final_query = Q.format(
        summary_variants=summary_variants,
        family_alleles=family_alleles,
    )

    variant_queries = []
    if 'regions' in kwargs and kwargs['regions'] is not None:
        regions = kwargs['regions']
        del kwargs['regions']
        variant_queries.append(regions_transformer(regions))

    variant_queries.extend(
        query_parts(VARIANT_QUERIES, **kwargs))

    return_reference = kwargs.get("return_reference", False)
    if not return_reference:
        aq = "F.allele_index > 0"
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
