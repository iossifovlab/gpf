from __future__ import print_function, unicode_literals, absolute_import
from builtins import str

import pytest

from ..attributes_query_builder import is_token, and_node, or_node, \
    is_tree, not_node, token, is_and, is_not, eq_node, any_node, all_node, \
    arg_node, simple_arg_node

from ..attributes_query import PARSER as attributes_query_parser, \
    QueryTransformerMatcher
from ..attributes_query import \
    parser_with_ambiguity as attributes_query_parser_with_ambiguity


@pytest.fixture()
def parser():
    return attributes_query_parser


@pytest.fixture()
def parser_with_ambiguity():
    return attributes_query_parser_with_ambiguity


@pytest.fixture()
def transformer_matcher():
    return QueryTransformerMatcher()


@pytest.fixture()
def transformer_matcher_class():
    return QueryTransformerMatcher


def test_can_match_simple_query(parser):
    assert parser.parse("some") is not None


def test_can_match_simple_query_with_whitespaces(parser):
    assert parser.parse(" some    ") is not None


def test_can_match_simple_and(parser):
    assert parser.parse("some and other") is not None


@pytest.mark.parametrize("expr", [
    "someandother",
])
def test_and_parses_no_whitespaces_correctly(parser, expr):
    tree = parser.parse(expr)
    print(tree.pretty())
    print(tree)
    assert len(tree.children) == 1


@pytest.mark.parametrize("expr", [
    "some and other",
    "some    and          other"
])
def test_and_parses_whitespaces_correctly(parser, expr):
    print(expr)
    tree = parser.parse(expr)
    print(tree.pretty())
    print(tree)
    assert len(tree.children) == 2


@pytest.mark.parametrize("expr,expected_missing_node", [
    ["some and other", "logical_and"],
    ["some or other", "logical_or"]
])
def test_ambiguity_with_binary_operations_is_resolved_correctly(
        parser, parser_with_ambiguity, expr, expected_missing_node):
    tree_ambiguity = parser_with_ambiguity.parse(expr)
    tree = parser.parse(expr)

    assert len(tree_ambiguity.children) == 2
    assert len(tree.children) == 2
    assert any(tree_ambiguity.find_pred(
        lambda x: x.data == expected_missing_node))
    assert any(tree.find_pred(lambda x: x.data == expected_missing_node))


@pytest.mark.parametrize("expr,expected_missing_node", [
    ["someandother", "logical_and"],
    ["someorother", "logical_or"]
])
def test_ambiguity_with_binary_operations_is_resolved_correctly_negative(
        parser, parser_with_ambiguity, expr, expected_missing_node):
    tree_ambiguity = parser_with_ambiguity.parse(expr)
    tree = parser.parse(expr)

    assert len(tree_ambiguity.children) == 1
    assert len(tree.children) == 1
    assert not any(tree_ambiguity.find_pred(
        lambda x: x.data == expected_missing_node))
    assert not any(tree.find_pred(lambda x: x.data == expected_missing_node))


def test_can_match_simple_parentheses(parser):
    tree = parser.parse("(some)")
    assert tree is not None
    assert len(tree.children) == 1
    assert len(tree.children[0].children) == 1
    assert is_token(tree.children[0].children[0])


@pytest.mark.parametrize("expr,expected_tree", [
    [
        "(some or other) and third",
        and_node([
            or_node([
                arg_node([simple_arg_node([token("some")])]),
                arg_node([simple_arg_node([token("other")])]),
            ]),

            arg_node([simple_arg_node([token("third")])])
        ])
    ],
    [
        "some or (other and third)",
        or_node([
            arg_node([simple_arg_node([token("some")])]),
            and_node([
                arg_node([simple_arg_node([token("other")])]),
                arg_node([simple_arg_node([token("third")])])
            ]),
        ])
    ]
])
def test_can_match_complex_parentheses(parser, expr, expected_tree):
    tree = parser.parse(expr)
    assert tree is not None
    assert is_tree(tree)

    assert tree == expected_tree


@pytest.mark.parametrize("expr,expected_tree", [
    [
        "a+", arg_node([simple_arg_node([token("a+")])]),
    ],
    [
        "a'b", arg_node([simple_arg_node([token("a'b")])]),
    ]
])
def test_can_match_plus_and_quote(parser, expr, expected_tree):
    tree = parser.parse(expr)
    assert tree is not None
    assert is_tree(tree)

    assert tree == expected_tree


@pytest.mark.parametrize("equivalents", [
    ["some and other", "some   and    other", "    some   and  other   "],
    ["any(some,other)", "any(some, other)", "any ( some , other )",
     "ANY(some, other)"]
])
def test_are_parsed_equivalently(parser, equivalents):
    parsed = [parser.parse(e) for e in equivalents]

    last = parsed[0]
    for current in parsed[1:]:
        assert current == last
        last = current


def test_can_match_multiple_and(parser):
    assert parser.parse("some and other and third") is not None


def test_can_match_simple_or(parser):
    assert parser.parse("some or other") is not None


def test_can_match_multiple_or(parser):
    assert parser.parse("some or other or third") is not None


FUNCTIONS = ["any", "all", "eq"]


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_simple_function(parser, function):
    query = "{}(some)".format(function)
    assert parser.parse(query) is not None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_complex_function(parser, function):
    query = "{}(some,other)".format(function)
    assert parser.parse(query) is not None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_very_complex_function(parser, function):
    query = "{}(some,other,third)".format(function)
    assert parser.parse(query) is not None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_complex_function_with_whitespaces(parser, function):
    query = "{}(some, other, third)".format(function)
    assert parser.parse(query) is not None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_complex_function_with_multiple_whitespaces(
        parser, function):
    query = "{}(some,    other,   third)".format(function)
    assert parser.parse(query) is not None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_can_match_complex_function_with_multiple_whitespaces_everywhere(
        parser, function):
    query = "   {}  (   some,    other,      third   ) ".format(function)
    assert parser.parse(query) is not None


def test_can_match_simple_not(parser):
    assert parser.parse("not some") is not None


def test_ambiguity_is_resolved_through_priority_correctly(
        parser, parser_with_ambiguity):
    query = "not some and not other"
    ambiguous_tree = parser_with_ambiguity.parse(query)
    tree_ = parser.parse(query)

    assert ambiguous_tree.data != "_ambig"
    assert len(ambiguous_tree.children) == 2

    assert tree_.data != "_ambig"

    expected_tree = and_node([
        not_node([arg_node([simple_arg_node([token("some")])])]),
        not_node([arg_node([simple_arg_node([token("other")])])]),
    ])
    print(tree_.pretty())
    print(ambiguous_tree.pretty())
    print(expected_tree.pretty())
    assert tree_ == expected_tree
    assert ambiguous_tree == expected_tree


def test_predence(parser_with_ambiguity):
    tree = parser_with_ambiguity.parse("A and B and C")
    print(tree)
    print(tree.pretty())

    assert len(tree.children) == 3


def test_can_match_not_and_binary_op(parser):
    tree = parser.parse("not some and not other")
    assert tree is not None
    print(tree)
    assert is_and(tree)


def test_can_match_not_and_priority_expression(parser):
    tree = parser.parse("not (some and other)")
    assert tree is not None
    print(tree)
    assert is_not(tree)


def parse_and_transform(transformer_matcher, query, expr):
    tree = transformer_matcher.parse(query)
    print(tree.pretty())
    assert tree is not None
    matcher = transformer_matcher.transform(tree)
    assert matcher is not None

    if not expr:
        expr = []
    print(isinstance(expr, str))
    if isinstance(expr, str):
        expr = expr.split(",")

    return matcher.match(expr)


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["some", True],
    ["", False],
])
def test_can_filter_simple_tokens(transformer_matcher, expr, output):
    assert parse_and_transform(transformer_matcher, "some", expr) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", True],
    ["some,two,three", False],
    ["some", False],
    ["", True],
])
def test_can_filter_not(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "not some", expr) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_and(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "some and other", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_or(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "some or other", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", True],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", False],
    ["", True]
])
def test_can_filter_complex_query(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "not some and not other", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,third", True],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_very_complex_query(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "some or (other and third)", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_simple_all(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "all(some, other)", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_complex_all(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "all(some, other) or all(other, two)", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_simple_any(transformer_matcher, expr, output):
    print(transformer_matcher.parse("any(some, other)"))
    assert parse_and_transform(
        transformer_matcher, "any(some, other)", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    ["one,two", False],
    ["some,two", False],
    ["other,two", False],
    ["some,other", True],
    ["some,other,third", False],
    ["", False]
])
def test_can_filter_simple_eq(transformer_matcher, expr, output):
    assert parse_and_transform(
        transformer_matcher, "eq(some, other)", expr
    ) == output


@pytest.mark.parametrize("expr,output", [
    [[1], True],
    [[1, 2, 3, 4], True],
    [[2, 3, 4], False],
    [[], False]
])
def test_token_simple_transformer_works(
        transformer_matcher_class, expr, output):
    matcher = transformer_matcher_class(token_converter=lambda _: 1)
    assert parse_and_transform(
        matcher, "some", expr) == output


@pytest.mark.parametrize("expr,output", [
    [[1], False],
    [[1, 2, 3, 4], True],
    [[2, 3, 4], False],
    [[], False]
])
def test_token_and_transformer(transformer_matcher_class, expr, output):
    token_map = {
        "some": 1,
        "other": 2
    }

    matcher = transformer_matcher_class(token_converter=lambda x: token_map[x])

    assert parse_and_transform(
        matcher, "some and other", expr,
    ) == output


@pytest.mark.parametrize("expr,output", [
    [[1], False],
    [[1, 2, 3, 4], False],
    [[2, 3, 4], False],
    [[1, 2], True],
    [[], False]
])
def test_token_eq_transformer(transformer_matcher_class, expr, output):
    token_map = {
        "some": 1,
        "other": 2
    }

    matcher = transformer_matcher_class(token_converter=lambda x: token_map[x])

    assert parse_and_transform(
        matcher, "eq(some, other)", expr,
    ) == output


@pytest.mark.skip("query_str causes endless loop")
def test_can_reconstruct_single_token(parser, transformer):
    query = "not some and not other"
    tree = parser.parse(query)
    print((tree, tree.data, tree.children))
    matcher = transformer(parser).transform(tree)

    assert matcher.query_str() == query


@pytest.mark.parametrize("node_constructor", [
    or_node, and_node, eq_node, any_node, all_node
])
def test_start_node_is_removed_when_constructing_node(
        parser, node_constructor):
    query = "some"
    subtree = parser.parse(query)

    assert subtree.data != 'start'

    tree = node_constructor([subtree, token("other")])
    print(tree)

    assert tree.data != 'start'
    operation_children = tree.children

    assert len(operation_children) > 0
    for child in operation_children:
        assert is_token(child) or (is_tree(child) and child.data != 'start')


def test_start_node_is_removed_when_constructing_not(parser):
    query = "some"
    subtree = parser.parse(query)
    assert subtree.data != 'start'

    tree = not_node([subtree])

    assert is_not(tree)
    assert len(tree.children) == 1
    assert len(tree.children[0].children) == 1
    assert len(tree.children[0].children[0].children) == 1
    assert is_token(tree.children[0].children[0].children[0])


def test_transformer_works_without_start_element(transformer_matcher):
    tree = not_node([arg_node([simple_arg_node([token("some")])])])

    matcher = transformer_matcher.transform(tree)
    assert matcher is not None

    assert matcher.match(["other"])
    assert not matcher.match(["some"])
    assert not matcher.match(["some", "other"])
    assert matcher.match([])


@pytest.mark.parametrize("expr,output", [
    [["some"], True],
    [["some", "other"], True],
    [["other"], True],
    [["third"], False],
    [["third", "fourth"], False],
    [[], False],
])
def test_can_create_subtree_from_parsed(transformer_matcher, expr, output):
    query = "some"
    subtree = transformer_matcher.parse(query)

    tree = or_node([subtree, arg_node([simple_arg_node([token("other")])])])

    assert tree is not None

    matcher = transformer_matcher.transform(tree)
    assert matcher is not None

    assert matcher.match(expr) == output
