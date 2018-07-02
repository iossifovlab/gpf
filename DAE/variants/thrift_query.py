from impala.util import as_pandas
from variants.attributes_query import StringQueryToTreeTransformerWrapper,\
    QueryTreeToSQLTransformer, QueryTreeToSQLListTransformer, \
    roles_converter, sex_converter, \
    inheritance_converter, variant_type_converter
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
    'role': StringQueryToTreeTransformerWrapper(
        token_converter=roles_converter),
    'sex': StringQueryToTreeTransformerWrapper(
        token_converter=sex_converter),
    'inheritance': StringQueryToTreeTransformerWrapper(
        token_converter=inheritance_converter),
    'variant_type': StringQueryToTreeTransformerWrapper(
        token_converter=variant_type_converter),
    # 'regions': regions_converter,
}


stage_two_transformers = {
    'effect_type': QueryTreeToSQLListTransformer("`effect_gene_types`"),
    'genes': QueryTreeToSQLListTransformer("`effect_gene_genes`"),
    'personId': QueryTreeToSQLListTransformer("variant_in_members"),
    'role': QueryTreeToSQLListTransformer("variant_in_roles"),
    'sex': QueryTreeToSQLListTransformer("variant_in_sexes"),
    'position': QueryTreeToSQLTransformer("A.position"),
    'chrom': QueryTreeToSQLTransformer("A.chrom"),
    'alternative': QueryTreeToSQLTransformer("A.alternative"),
}

q = """
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


def region_transformer(r):
    assert isinstance(r, Region)
    return "(S.chrom = {} AND S.position >= {} AND S.position <= {})".format(
        r.chr, r.start, r.stop)


def regions_transformer(rs):
    assert all([isinstance(r, Region) for r in rs])
    return " OR ".join([region_transformer(r) for r in rs])


def thrift_query(thrift_connection, summary, family, limit=2000, **kwargs):
    first = True
    final_query = q.format(
        summary=summary,
        family=family,
    )

    if 'regions' in kwargs:
        regions = kwargs['regions']
        del kwargs['regions']
        final_query += "\nWHERE ({})".format(regions_transformer(regions))
        first = False

    for k in kwargs:
        if k in stage_one_transformers:
            stage_one_transformer = stage_one_transformers[k]
        else:
            stage_one_transformer = StringQueryToTreeTransformerWrapper()

        if k in stage_two_transformers:
            stage_two_transformer = stage_two_transformers[k]
        else:
            stage_two_transformer = QueryTreeToSQLTransformer(k)

        if first:
            final_query += "\nWHERE"
        if not first:
            final_query += " AND\n"
        stage_one_result = stage_one_transformer.parse_and_transform(kwargs[k])
        final_query += stage_two_transformer.transform(stage_one_result)
        first = False

    if limit is not None:
        final_query += "\nLIMIT {}".format(limit)
    print(final_query)

    cursor = thrift_connection.cursor()
    cursor.execute(final_query)
    return as_pandas(cursor)
