import pytest

from variants.attributes_query_builder import is_token, and_node, or_node, \
    is_tree, not_node, token, is_and, is_not, eq_node, any_node, all_node, \
    arg_node, simple_arg_node


def test_can_match_simple_query(parser):
    assert parser.parse("some") is not None


def test_can_match_simple_query_with_whitespaces(parser):
    assert parser.parse(" some    ") is not None


def test_can_match_simple_and(parser):
    assert parser.parse("some and other") is not None

@pytest.mark.parametrize("input", [
    "someandother",
    "some and other",
    "some    and          other"
])
def test_and_parses_whitespaces_correctly(parser, input):
    tree = parser.parse(input)
    print tree.pretty()
    print tree
    assert len(tree.children) == 1


@pytest.mark.parametrize("input,expected_missing_node", [
    ["some and other", "logical_and"],
    ["some or other", "logical_or"]
])
def test_ambiguity_with_binary_operations_is_resolved_correctly(
        parser, parser_with_ambiguity, input, expected_missing_node):
    tree_ambiguity = parser_with_ambiguity.parse(input)
    tree = parser.parse(input)

    assert len(tree_ambiguity.children) == 1
    assert len(tree.children) == 1
    assert any(tree_ambiguity.find_pred(
        lambda x: x.data == expected_missing_node))
    assert any(tree.find_pred(lambda x: x.data == expected_missing_node))


@pytest.mark.parametrize("input,expected_missing_node", [
    ["someandother", "logical_and"],
    ["someorother", "logical_or"]
])
def test_ambiguity_with_binary_operations_is_resolved_correctly_negative(
        parser, parser_with_ambiguity, input, expected_missing_node):
    tree_ambiguity = parser_with_ambiguity.parse(input)
    tree = parser.parse(input)

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
    assert len(tree.children[0].children[0].children) == 1
    assert is_token(tree.children[0].children[0].children[0])


@pytest.mark.parametrize("input,expected_tree", [
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
def test_can_match_complex_parentheses(parser, input, expected_tree):
    tree = parser.parse(input)
    assert tree is not None
    assert len(tree.children) == 1
    assert is_tree(tree.children[0])

    assert tree.children[0] == expected_tree


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
def test_can_match_complex_function_with_multiple_whitespaces(parser, function):
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
    assert len(ambiguous_tree.children) == 1

    assert tree_.data != "_ambig"

    expected_tree = and_node([
        not_node([arg_node([simple_arg_node([token("some")])])]),
        not_node([arg_node([simple_arg_node([token("other")])])]),
    ])
    print(tree_.children[0].pretty())
    print(ambiguous_tree.children[0].pretty())
    assert tree_.children[0] == expected_tree
    assert ambiguous_tree.children[0] == expected_tree


def test_predence(parser_with_ambiguity):
    tree = parser_with_ambiguity.parse("A and B and C")
    print tree
    print tree.pretty()

    assert len(tree.children) == 1


def test_can_match_not_and_binary_op(parser):
    tree = parser.parse("not some and not other")
    assert tree is not None
    print(tree)
    assert is_and(tree.children[0])


def test_can_match_not_and_priority_expression(parser):
    tree = parser.parse("not (some and other)")
    assert tree is not None
    print(tree)
    assert is_not(tree.children[0])


def parse_and_transform(
        parser, transformer, query, input, token_converter=None):
    tree = parser.parse(query)
    print tree.pretty()
    assert tree is not None
    matcher = transformer(parser, token_converter).transform(tree)
    assert matcher is not None

    if not input:
        input = []

    if isinstance(input, str):
        input = input.split(",")

    return matcher.match(input)


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["some", True],
    ["", False],
])
def test_can_filter_simple_tokens(parser, transformer, input, output):
    assert parse_and_transform(parser, transformer, "some", input) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", True],
    ["some,two,three", False],
    ["some", False],
    ["", True],
])
def test_can_filter_not(parser, transformer, input, output):
    assert parse_and_transform(parser, transformer, "not some", input) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_and(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "some and other", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_or(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "some or other", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", True],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", False],
    ["", True]
])
def test_can_filter_complex_query(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "not some and not other", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,third", True],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_very_complex_query(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "some or (other and third)", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", False],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_simple_all(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "all(some, other)", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", False],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_complex_all(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "all(some, other) or all(other, two)", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two,three", False],
    ["some,two,three", True],
    ["other,two,three", True],
    ["some,other,three", True],
    ["", False]
])
def test_can_filter_simple_any(parser, transformer, input, output):
    print parser.parse("any(some, other)")
    assert parse_and_transform(
        parser, transformer, "any(some, other)", input
    ) == output


@pytest.mark.parametrize("input,output", [
    ["one,two", False],
    ["some,two", False],
    ["other,two", False],
    ["some,other", True],
    ["some,other,third", False],
    ["", False]
])
def test_can_filter_simple_eq(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "eq(some, other)", input
    ) == output


@pytest.mark.parametrize("input,output", [
    [[1], True],
    [[1, 2, 3, 4], True],
    [[2, 3, 4], False],
    [[], False]
])
def test_token_simple_transformer_works(parser, transformer, input, output):
    assert parse_and_transform(
        parser, transformer, "some", input, token_converter=lambda _: 1
    ) == output


@pytest.mark.parametrize("input,output", [
    [[1], False],
    [[1, 2, 3, 4], True],
    [[2, 3, 4], False],
    [[], False]
])
def test_token_and_transformer(parser, transformer, input, output):
    token_map = {
        "some": 1,
        "other": 2
    }

    assert parse_and_transform(
        parser, transformer, "some and other", input,
        token_converter=lambda x: token_map[x]
    ) == output


@pytest.mark.parametrize("input,output", [
    [[1], False],
    [[1, 2, 3, 4], False],
    [[2, 3, 4], False],
    [[1, 2], True],
    [[], False]
])
def test_token_eq_transformer(parser, transformer, input, output):
    token_map = {
        "some": 1,
        "other": 2
    }

    assert parse_and_transform(
        parser, transformer, "eq(some, other)", input,
        token_converter=lambda x: token_map[x]
    ) == output


@pytest.mark.skip("query_str causes endless loop")
def test_can_reconstruct_single_token(parser, transformer):
    query = "not some and not other"
    tree = parser.parse(query)
    print(tree, tree.data, tree.children)
    matcher = transformer(parser).transform(tree)

    assert matcher.query_str() == query


@pytest.mark.parametrize("node_constructor", [
    or_node, and_node, eq_node, any_node, all_node
])
def test_start_node_is_removed_when_constructing_node(parser, node_constructor):
    query = "some"
    subtree = parser.parse(query)

    assert subtree.data == 'start'

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
    assert subtree.data == 'start'

    tree = not_node(subtree)

    assert is_not(tree)
    assert len(tree.children) == 1
    assert is_token(tree.children[0])


def test_transformer_works_without_start_element(parser, transformer):
    tree = not_node(token("some"))

    matcher = transformer(parser).transform(tree)
    assert matcher is not None

    assert matcher.match(["other"])
    assert not matcher.match(["some"])
    assert not matcher.match(["some", "other"])
    assert matcher.match([])


@pytest.mark.parametrize("input,output", [
    [["some"], True],
    [["some", "other"], True],
    [["other"], True],
    [["third"], False],
    [["third", "fourth"], False],
    [[], False],
])
def test_can_create_subtree_from_parsed(parser, transformer, input, output):
    query = "some"
    subtree = parser.parse(query)

    tree = or_node([subtree, token("other")])

    assert tree is not None

    matcher = transformer(parser).transform(tree)
    assert matcher is not None

    assert matcher.match(input) == output
