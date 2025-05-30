from collections.abc import Callable
from enum import Enum
from typing import Protocol

from lark import Lark, Transformer, Tree
from sqlglot import not_, parse_one
from sqlglot.expressions import BitwiseAnd, Column, Expression, Paren, and_, or_

from dae.utils.variant_utils import BitmaskEnumTranslator

QUERY_GRAMMAR = """
?start: expr+

literal: /[\\w+-]+/

compound: /[\\w+-]+/ "~" /[\\w+-]+/

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
    | compound
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


class AttributeQueryTransformer(Transformer):
    """
    Base class for attribute query transformers.

    Supports two enum types, the second being optional.
    The second enum type is intended for compounds.
    """

    def __init__(
        self, enum_type: type[Enum],
        main_aliases: dict[str, str],
        complementary_type: type[Enum] | None = None,
    ):
        super().__init__()
        self._enum_type = enum_type
        self._complementary_type = complementary_type
        self._values = {e.name.lower(): e for e in self._enum_type}
        self._complementary_values = {}
        self._bitmask_transformer = None
        if self._complementary_type is not None:
            self._bitmask_transformer = BitmaskEnumTranslator(
                main_enum_type=self._complementary_type,
                partition_by_enum_type=self._enum_type,
            )
            self._complementary_values = {
                e.name.lower(): e.value for e in self._complementary_type
            }
        for value_name, alias in main_aliases.items():
            self._values[alias.lower()] = self._values[value_name.lower()]


class AttributeQueryTransformerFunction(AttributeQueryTransformer):
    """Class for transforming attribute Lark trees into function calls."""

    def compound(self, values) -> Callable[[int, int | None], bool]:
        """Transform compounds into a function that compares two values."""
        assert len(values) == 2
        if self._bitmask_transformer is None:
            raise ValueError(
                "This transformer cannot handle compounds since it's"
                f"initialized to handle only 1 enum type {self._enum_type}!",
            )
        main_value = values[0].value.lower()
        complementary_value = values[1].value.lower()
        assert main_value in self._values, \
            f"{main_value} not in {self._values.keys()}"
        assert complementary_value in self._complementary_values, \
            f"{complementary_value} not in {self._complementary_values.keys()}"

        bitmask_value = self._bitmask_transformer.apply_mask(
            0,
            self._complementary_values[complementary_value],
            self._values[main_value],
        )

        def compare_compound(x: int, y: int | None = None) -> bool:
            if y is None:
                raise ValueError(
                    "Cannot execute attribute query function "
                    f"for {self._enum_type}~{self._complementary_type} "
                    "without a second value argument!",
                )
            return self._values[main_value].value & x == \
                self._values[main_value].value \
                and bitmask_value & y != 0

        return compare_compound

    def literal(self, values) -> Callable[[int, int | None], bool]:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value = values[0].value.lower()
        assert value in self._values, f"{value} not in {self._values.keys()}"

        def compare_literal(
            x: int, y: int | None = None,  # noqa: ARG001
        ) -> bool:
            return self._values[value].value & x == self._values[value].value
        return compare_literal

    def and_(self, values) -> Callable[[int, int | None], bool]:
        assert len(values) == 2

        def compare_and(x: int, y: int | None = None) -> bool:
            return values[0](x, y) and values[1](x, y)
        return compare_and

    def or_(self, values) -> Callable[[int, int | None], bool]:
        assert len(values) == 2

        def compare_or(x: int, y: int | None = None) -> bool:
            return values[0](x, y) or values[1](x, y)
        return compare_or

    def grouping(self, values) -> Callable[[int, int | None], bool]:
        assert len(values) == 1

        def compare_grouping(x: int, y: int | None = None) -> bool:
            return values[0](x, y)
        return compare_grouping

    def neg(self, values) -> Callable[[int, int | None], bool]:
        assert len(values) == 1

        def compare_neg(x: int, y: int | None = None) -> bool:
            return not values[0](x, y)
        return compare_neg


class AttributeQueryTransformerSQL(AttributeQueryTransformer):
    """Class for transforming attribute queries into an SQLglot expression."""

    def __init__(
        self, main_column: Column, enum_type: type[Enum],
        main_aliases: dict[str, str],
        complementary_column: Column | None = None,
        complementary_type: type[Enum] | None = None,
    ):
        super().__init__(
            enum_type, main_aliases, complementary_type=complementary_type,
        )
        self._column = main_column
        self._complementary_column = complementary_column

    def literal(self, values) -> Expression:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value_name = values[0].value.lower()
        assert value_name in self._values, \
            f"{value_name} not in {self._values.keys()}"

        return BitwiseAnd(
            this=self._column,
            expression=str(self._values[value_name].value),
        ).neq(0)

    def compound(self, values) -> Expression:
        """Convert compounds into a query statement for two enums."""
        assert len(values) == 2
        if self._bitmask_transformer is None:
            raise ValueError(
                "This transformer cannot handle compounds since it's"
                f"initialized to handle only 1 enum type {self._enum_type}!",
            )
        if self._complementary_column is None:
            raise ValueError(
                "No column given for complementary enum in transformer for "
                f"{self._enum_type}, {self._complementary_type}!",
            )
        main_value = values[0].value.lower()
        complementary_value = values[1].value.lower()
        assert main_value in self._values, \
            f"{main_value} not in {self._values.keys()}"
        assert complementary_value in self._complementary_values, \
            f"{complementary_value} not in {self._complementary_values.keys()}"

        bitmask_value = self._bitmask_transformer.apply_mask(
            0,
            self._complementary_values[complementary_value],
            self._values[main_value],
        )

        return BitwiseAnd(
            this=self._column,
            expression=str(self._values[main_value].value),
        ).neq(0).and_(
            BitwiseAnd(
                this=self._complementary_column,
                expression=str(bitmask_value),
            ).neq(0),
        )

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
            f"{self._column.alias_or_name}, {self._values[value_name].value!s}"
            ") != 0",
        )

    def compound(self, values):
        raise NotImplementedError(
            "Compounds are not supported for legacy backends",
        )


class Matcher(Protocol):
    def __call__(self, a: int, b: int | None = None) -> bool:  # noqa: ARG002
        return False


def transform_attribute_query_to_function(
    enum_type: type[Enum],
    query: str,
    aliases: dict[str, str] | None = None,
    complementary_type: type[Enum] | None = None,
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
    transformer = AttributeQueryTransformerFunction(
        enum_type, aliases, complementary_type=complementary_type,
    )
    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def transform_attribute_query_to_sql_expression(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
    complementary_type: type[Enum] | None = None,
    complementary_column: Column | None = None,
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
    transformer = AttributeQueryTransformerSQL(
        column, enum_type, aliases,
        complementary_column=complementary_column,
        complementary_type=complementary_type,
    )

    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def transform_attribute_query_to_sql_expression_schema1(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
    complementary_type: type[Enum] | None = None,
    complementary_column: Column | None = None,
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
        column, enum_type, aliases,
        complementary_column=complementary_column,
        complementary_type=complementary_type,
    )

    tree = syntax_sugar_transformer.transform(tree)
    return transformer.transform(tree)


def create_or_node(left: Tree, right: Tree) -> Tree:
    return Tree("or_", children=[left, right])


def create_and_node(left: Tree, right: Tree) -> Tree:
    return Tree("and_", children=[left, right])
