from collections.abc import Callable
from enum import Enum

from lark import Lark, Transformer, Tree
from sqlglot import not_, parse_one
from sqlglot.expressions import BitwiseAnd, Column, Expression, Paren, and_, or_

QUERY_GRAMMAR = """
?start: expr+

literal: /[\\w+-]+/
neg: "not" expr

and_: expr "and" expr
or_: expr "or" expr


grouping: "(" expr ")"
list: "[" expr ("," expr)* "]"
all: "all" "(" list ")"
any: "any" "(" list ")"

?expr: all
    | any
    | grouping
    | or_
    | and_
    | neg
    | literal
%import common.WS
%ignore WS

"""

QUERY_PARSER = Lark(QUERY_GRAMMAR)


class SyntaxSugarTransformer(Transformer):
    """Transformer for adapting syntax sugar to regular queries."""
    def all(self, values):
        """Transform all into a sequence of and nodes."""
        list_node = values[0]
        current = None
        for child in list_node.children:
            if current is None:
                current = child
                continue

            current = create_and_node(current, child)

        return current

    def any(self, values):
        """Transform any into a sequence of or nodes."""
        list_node = values[0]
        current = None
        for child in list_node.children:
            if current is None:
                current = child
                continue

            current = create_or_node(current, child)

        return current


class AttributeQueryTransformerFunction(Transformer):
    """Class for transforming attribute Lark trees into function calls."""

    def __init__(self, enum_type: type[Enum], aliases: dict[str, str]):
        super().__init__()
        self._enum_type = enum_type
        self._values = {e.name.lower(): e.value for e in self._enum_type}
        for value_name, alias in aliases.items():
            self._values[alias.lower()] = self._values[value_name.lower()]

    def literal(self, values) -> Callable[[int], bool]:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value = values[0].value.lower()
        assert value in self._values, f"{value} not in {self._values.keys()}"

        def compare_literal(x: int) -> bool:
            return self._values[value] & x == self._values[value]
        return compare_literal

    def and_(self, values) -> Callable[[int], bool]:
        assert len(values) == 2

        def compare_and(x: int) -> bool:
            return values[0](x) and values[1](x)
        return compare_and

    def or_(self, values) -> Callable[[int], bool]:
        assert len(values) == 2

        def compare_or(x: int) -> bool:
            return values[0](x) or values[1](x)
        return compare_or

    def grouping(self, values) -> Callable[[int], bool]:
        assert len(values) == 1

        def compare_grouping(x: int):
            return values[0](x)
        return compare_grouping

    def neg(self, values) -> Callable[[int], bool]:
        assert len(values) == 1

        def compare_neg(x: int) -> bool:
            return not values[0](x)
        return compare_neg


class AttributeQueryTransformerSQL(Transformer):
    """Class for transforming attribute queries into an SQLglot expression."""

    def __init__(
        self, column: Column, enum_type: type[Enum], aliases: dict[str, str],
    ):
        super().__init__()
        self._column = column
        self._enum_type = enum_type
        self._values = {e.name.lower(): e.value for e in self._enum_type}
        for value_name, alias in aliases.items():
            self._values[alias.lower()] = self._values[value_name.lower()]

    def literal(self, values) -> Expression:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value_name = values[0].value.lower()
        assert value_name in self._values, \
            f"{value_name} not in {self._values.keys()}"

        return BitwiseAnd(
            this=self._column,
            expression=str(self._values[value_name]),
        ).neq(0)

    def and_(self, values) -> Expression:
        assert len(values) == 2

        return and_(*values)

    def or_(self, values) -> Expression:
        assert len(values) == 2

        return or_(*values)

    def grouping(self, values) -> Expression:
        assert len(values) == 1

        return Paren(this=values[0])

    def neg(self, values) -> Expression:
        assert len(values) == 1

        return not_(values[0])


class AttributeQueryTransformerSQLLegacy(AttributeQueryTransformerSQL):
    """
    Class for transforming attribute queries into an SQLglot expression.

    Intended for use with legacy Impala schema1 storage.
    """
    def literal(self, values):
        assert len(values) == 1
        value_name = values[0].value.lower()
        assert value_name in self._values, \
            f"{value_name} not in {self._values.keys()}"

        return parse_one(
            "BITAND("
            f"{self._column.alias_or_name}, {self._values[value_name]!s}"
            ") != 0",
        )


Matcher = Callable[[int], bool]


def transform_attribute_query_to_function(
    enum_type: type[Enum],
    query: str,
    aliases: dict[str, str] | None = None,
) -> Matcher:
    """
    Transform attribute query to a callable function.

    Can evaluate a query for multiple enum types.
    Queries need to use proper enum names in order to be valid.
    A dictionary of aliases can be provided,
    where the keys are the original values.
    """
    if aliases is None:
        aliases = {}
    tree = QUERY_PARSER.parse(query)

    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerFunction(enum_type, aliases)
    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def transform_attribute_query_to_sql_expression(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
) -> Expression:
    """
    Transform attribute query to an SQLglot expression.

    Can evaluate a query for multiple enum types.
    Queries need to use proper enum names in order to be valid.
    A dictionary of aliases can be provided,
    where the keys are the original values.
    """
    if aliases is None:
        aliases = {}

    tree = QUERY_PARSER.parse(query)
    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerSQL(column, enum_type, aliases)

    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def transform_attribute_query_to_sql_expression_schema1(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
) -> Expression:
    """
    Transform attribute query to an SQLglot expression.

    Can evaluate a query for multiple enum types.
    Queries need to use proper enum names in order to be valid.
    A dictionary of aliases can be provided,
    where the keys are the original values.
    """
    if aliases is None:
        aliases = {}

    tree = QUERY_PARSER.parse(query)
    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerSQLLegacy(
        column, enum_type, aliases)

    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def create_or_node(left: Tree, right: Tree) -> Tree:
    return Tree("or_", children=[left, right])


def create_and_node(left: Tree, right: Tree) -> Tree:
    return Tree("and_", children=[left, right])
