from impala.util import as_pandas
from impala.dbapi import connect
from variants.attributes_query import StringQueryToTreeTransformerWrapper,\
    QueryTreeToSQLTransformer, QueryTreeToSQLListTransformer, \
    roles_converter, sex_converter, \
    inheritance_converter, variant_type_converter
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
}


stage_two_transformers = {
    'effect_type': QueryTreeToSQLListTransformer("`effect_gene.types`"),
    'genes': QueryTreeToSQLListTransformer("`effect_gene.genes`"),
    'personId': QueryTreeToSQLListTransformer("variant_in_members"),
    'role': QueryTreeToSQLListTransformer("variant_in_roles"),
    'sex': QueryTreeToSQLListTransformer("variant_in_sexes"),
    'position': QueryTreeToSQLTransformer("A.position"),
    'chrom': QueryTreeToSQLTransformer("A.chrom"),
    'alternative': QueryTreeToSQLTransformer("A.alternative"),
}


def query(**kwargs):
    first = True
    conn = connect(host='wigclust24.cshl.edu', port=10000,
                   auth_mechanism='PLAIN')
    final_query = q
    for k in kwargs:
        if k in stage_one_transformers:
            stage_one_transformer = stage_one_transformers[k]
        else:
            stage_one_transformer = StringQueryToTreeTransformerWrapper()

        if k in stage_two_transformers:
            stage_two_transformer = stage_two_transformers[k]
        else:
            stage_two_transformer = QueryTreeToSQLTransformer(k)

        if not first:
            final_query += " AND\n"
        stage_one_result = stage_one_transformer.parse_and_transform(kwargs[k])
        final_query += stage_two_transformer.transform(stage_one_result)
        first = False
        
    final_query += "\nLIMIT 1000"
    print(final_query)

    cursor = conn.cursor()
    cursor.execute(final_query)
    return as_pandas(cursor)
