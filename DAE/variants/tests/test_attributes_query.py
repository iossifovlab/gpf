import pytest
from variants.attributes_query import token, tree, is_tree, is_token, \
    is_and, is_not


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


@pytest.mark.parametrize("input,expected_function", [
    ["someandother", is_token],
    ["someorother", is_token]
])
def test_ambiguity_with_binary_operations_is_resolved_correctly(
        parser, parser_with_ambiguity, input, expected_function):
    tree_ambiguity = parser_with_ambiguity.parse(input)
    tree = parser.parse(input)

    assert len(tree_ambiguity.children) == 1
    assert len(tree.children) == 1
    assert expected_function(tree.children[0])
    assert expected_function(tree_ambiguity.children[0])


def test_can_match_simple_parentheses(parser):
    tree = parser.parse("(some)")
    assert tree is not None
    assert len(tree.children) == 1
    assert is_token(tree.children[0])


@pytest.mark.parametrize("input,expected_tree", [
    [
        "(some or other) and third",
        tree("logical_and", [
            tree("logical_or", [
                token("some"),
                token("other")
            ]),
            token("third")
        ])
    ],
    [
        "some or (other and third)",
        tree("logical_or", [
            token("some"),
            tree("logical_and", [
                token("other"),
                token("third")
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

    expected_tree = tree("logical_and", [
        tree("negation", [token("some")]),
        tree("negation", [token("other")]),
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


def parse_and_transform(parser, transformer, query, input):
    tree = parser.parse(query)
    print tree.pretty()
    assert tree is not None
    matcher = transformer.transform(tree)
    assert matcher is not None

    input_list = []
    if input:
        input_list = input.split(",")

    return matcher.match(input_list)


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
