from impala.util import as_pandas
from impala.dbapi import connect
from variants.attributes_query import QuerySQLTransformerMatcher, \
    QuerySQLListTransformerMatcher, roles_converter, sex_converter, \
    inheritance_converter, variant_type_converter
from variants.attributes import Role, Sex, Inheritance, VariantType

q = """
    SELECT * FROM parquet.`/data-raw-dev/pspark/family01` AS A
    INNER JOIN parquet.`/data-raw-dev/pspark/summary01` AS B
    ON
    A.chrom = B.chrom AND
    A.position = B.position AND
    A.alternative = B.alternative
    WHERE
"""

transformers = {
    'effect_type': QuerySQLListTransformerMatcher("`effect_gene.types`"),
    'genes': QuerySQLListTransformerMatcher("`effect_gene.genes`"),
    'personId': QuerySQLListTransformerMatcher("variant_in_members"),
    'role': QuerySQLListTransformerMatcher(
        "variant_in_roles",
        token_converter=lambda x: str(Role.from_name(x).value)),
    'sex': QuerySQLListTransformerMatcher(
        "variant_in_sexes",
        token_converter=lambda x: str(Sex.from_name(x).value)),
    'inheritance': QuerySQLTransformerMatcher(
        "inheritance",
        token_converter=lambda x: str(Inheritance.from_name(x).value)),
    'variant_type': QuerySQLTransformerMatcher(
        "variant_type",
        token_converter=lambda x: str(VariantType.from_name(x).value)),
    'position': QuerySQLTransformerMatcher("A.position"),
    'chrom': QuerySQLTransformerMatcher("A.chrom"),
    'alternative': QuerySQLTransformerMatcher("A.alternative"),
}


def query(**kwargs):
    first = True
    conn = connect(host='wigclust24.cshl.edu', port=10000,
                   auth_mechanism='PLAIN')
    final_query = q
    for k in kwargs:
        if k in transformers:
            transformer = transformers[k]
        else:
            transformer = QuerySQLTransformerMatcher(k)
        if not first:
            final_query += " AND\n"
        final_query += transformer.parse_and_transform(kwargs[k])
        first = False
        
    final_query += "\nLIMIT 1000"
    print(final_query)

    cursor = conn.cursor()
    cursor.execute(final_query)
    return as_pandas(cursor)
