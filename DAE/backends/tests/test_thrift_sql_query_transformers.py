
from ..attributes_query import StringQueryToTreeTransformerWrapper,\
    StringListQueryToTreeTransformer, \
    QueryTreeToSQLListTransformer


def test_simple_sql_string_transformer():
    prepare = StringQueryToTreeTransformerWrapper()
    query_tree = prepare.parse_and_transform("any(a, b)")
    transformer = QueryTreeToSQLListTransformer("E.effect_type")
    result = transformer.transform(query_tree)
    print(result)


def test_simple_sql_string_list_transformer():
    prepare = StringListQueryToTreeTransformer()
    query_tree = prepare.parse_and_transform(['a', 'b'])
    transformer = QueryTreeToSQLListTransformer("E.effect_type")
    result = transformer.transform(query_tree)
    print(result)
