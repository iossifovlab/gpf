"""
Module for attribute queries

Attribute queries are human readable strings which are used to filter variants
based on enum attribute values.

They are applicable only to enum types and this module provides three utilities
to transform an attribute query string into a callable function, an sqlglot
expression or an sqlglot expression tailored to old legacy genotype storages.

Attribute queries have a defined earley grammar, used by lark to create a
parsable tree.

The grammar divides the input string into expressions, which can be different
types:
    - literal:
        The most basic type, a normal string which
        matches to an enumeration.
        For example, for roles "mom" would match variants which are present
        in the mother.
    - compound:
        A special case of literal, used for zygosity.
        A compound consists of 2 literals connected by a tilde ("~")
        with the second one being the complementary.
        For example: prb~homozygous would match variants which
        are present and homozygotic in the proband of the family.
    - neg:
        Match any value that does not match the underlying expression.
        Negation is written by writing "not" before your expression.
        Example: "not sib~heterozygous"
    - and_:
        Match when both expressions are true.
        Example: prb and dad
    - or_:
        Match when one of the expressions is true.
        Example: sib or prb
    - grouping:
        Prioritize an expression to be evaluated first with brackets.
        Example: (sib or prb) and dad
    - any:
        Syntax sugar for doing an or_ between many values.
        Example: "any([dad, prb, sib])" is equivalent to "dad or prb or sib"
    - all:
        Syntax sugar for doing an and_ between many values.
        Example: "all([dad, prb, sib])" is equivalent to "dad and prb and sib"
"""

from collections.abc import Callable
from enum import Enum
from typing import Protocol, cast

from lark import Lark, Token, Transformer, Tree
from sqlglot import not_, parse_one
from sqlglot.expressions import (
    BitwiseAnd,
    Column,
    Expression,
    Paren,
    and_,
    or_,
)

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


class AttributeQueryNotSupported(Exception):
    pass


class SyntaxSugarTransformer(Transformer):
    """Transformer for adapting syntax sugar to regular queries."""
    def all(self, values: list[Tree]) -> Tree | None:
        """Transform all into a sequence of and nodes."""
        list_node = values[0]
        current = None
        for child in list_node.children:
            if current is None:
                current = child
                continue

            current = create_and_node(current, child)

        return current

    def any(self, values: list[Tree]) -> Tree | None:
        """Transform any into a sequence of or nodes."""
        list_node = values[0]
        current = None
        for child in list_node.children:
            if current is None:
                current = child
                continue

            current = create_or_node(current, child)

        return current


class CompoundStripTransformer(Transformer):
    def compound(self, values: list[Token]) -> Tree:
        assert len(values) == 2
        return Tree(
            "literal", children=[Token("__ANON_0", values[0].value)])


class QueryCompoundAdditionTransformer(Transformer):
    """
    Transformer that adds a compound value to an attribute query's literals.

    Directly returns a new attribute query
    string to be used with other transformers.
    """
    def __init__(self, compound_value: str):
        super().__init__()
        self._compound_value = compound_value

    def literal(self, values: list[Token]) -> str:
        assert len(values) == 1
        str_value = values[0].value

        return f"{str_value}~{self._compound_value}"

    def compound(self) -> str:
        raise AttributeQueryNotSupported(
            "Attribute queries already containing compounds are "
            "not eligible for compound addition transformation!",
        )

    def and_(self, values: list[Token]) -> str:
        assert len(values) == 2

        return f"{values[0]} and {values[1]}"

    def or_(self, values: list[Token]) -> str:
        assert len(values) == 2

        return f"{values[0]} or {values[1]}"

    def grouping(self, values: list[Token]) -> str:
        assert len(values) == 1

        return f"({values[0]})"

    def neg(self, values: list[Token]) -> str:
        assert len(values) == 1

        return f"not {values[0]}"

    def all(self, values: list[Tree]) -> str:
        list_node = values[0]
        res = ", ".join(str(ch) for ch in list_node.children)

        return f"all([{res}])"

    def any(self, values: list[Tree]) -> str:
        list_node = values[0]
        res = ", ".join(str(ch) for ch in list_node.children)

        return f"any([{res}])"


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

    def compound(
        self, values: list[Token],
    ) -> Callable[[int, int | None], bool]:
        """Transform compounds into a function that compares two values."""
        assert len(values) == 2
        if self._bitmask_transformer is None:
            raise AttributeQueryNotSupported(
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

    def literal(
        self, values: list[Token],
    ) -> Callable[[int, int | None], bool]:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value = values[0].value.lower()
        assert value in self._values, f"{value} not in {self._values.keys()}"

        def compare_literal(
            x: int, y: int | None = None,  # noqa: ARG001
        ) -> bool:
            return bool(
                self._values[value].value & x == self._values[value].value)
        return compare_literal

    def and_(
        self, values: list[Callable[[int, int | None], bool]],
    ) -> Callable[[int, int | None], bool]:
        """Transform and_ into a function that combines two comparisons."""
        assert len(values) == 2

        def compare_and(x: int, y: int | None = None) -> bool:
            return values[0](x, y) and values[1](x, y)

        return compare_and

    def or_(
        self, values: list[Callable[[int, int | None], bool]],
    ) -> Callable[[int, int | None], bool]:
        """Transform or_ into a function that combines two comparisons."""
        assert len(values) == 2

        def compare_or(x: int, y: int | None = None) -> bool:
            return values[0](x, y) or values[1](x, y)

        return compare_or

    def grouping(
        self, values: list[Callable[[int, int | None], bool]],
    ) -> Callable[[int, int | None], bool]:
        """Transform grouping into a function that evaluates the expression."""
        assert len(values) == 1

        def compare_grouping(x: int, y: int | None = None) -> bool:
            return values[0](x, y)
        return compare_grouping

    def neg(
        self, values: list[Callable[[int, int | None], bool]],
    ) -> Callable[[int, int | None], bool]:
        """Transform neg into a function that negates the comparison."""
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

    def literal(self, values: list[Token]) -> Expression:
        """Transform literals into a direct comparison function."""
        assert len(values) == 1
        value_name = values[0].value.lower()
        assert value_name in self._values, \
            f"{value_name} not in {self._values.keys()}"

        return BitwiseAnd(
            this=self._column,
            expression=str(self._values[value_name].value),
        ).neq(0)

    def compound(self, values: list[Token]) -> Expression:
        """Convert compounds into a query statement for two enums."""
        assert len(values) == 2
        if self._bitmask_transformer is None:
            raise AttributeQueryNotSupported(
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

    def and_(self, values: list[Expression]) -> Expression:
        assert len(values) == 2

        return and_(*values)

    def or_(self, values: list[Expression]) -> Expression:
        assert len(values) == 2

        return or_(*values)

    def grouping(self, values: list[Expression]) -> Expression:
        assert len(values) == 1

        return Paren(this=values[0])

    def neg(self, values: list[Expression]) -> Expression:
        assert len(values) == 1

        return not_(values[0])


class AttributeQueryTransformerSQLLegacy(AttributeQueryTransformerSQL):
    """
    Class for transforming attribute queries into an SQLglot expression.

    Intended for use with legacy Impala schema1 storage.
    """
    def literal(self, values: list[Token]) -> Expression:
        assert len(values) == 1
        value_name = values[0].value.lower()
        assert value_name in self._values, \
            f"{value_name} not in {self._values.keys()}"

        return parse_one(
            "BITAND("
            f"{self._column.alias_or_name}, {self._values[value_name].value!s}"
            ") != 0",
        )

    def compound(self, values: list[Token]) -> Expression:
        raise NotImplementedError(
            "Compounds are not supported for legacy backends",
        )


class Matcher(Protocol):
    def __call__(self, a: int, b: int | None = None) -> bool:  # noqa: ARG002
        return False


def update_attribute_query_with_compounds(
    query: str,
    compound_value: str,
) -> str:
    """
    Update an attribute query to match by a secondary compound value.

    Used to add zygosity in an already existing attribute query, for example:
    "dad and mom" -> "dad~homozygous and mom~homozygous"
    """

    tree = QUERY_PARSER.parse(query)
    transformer = QueryCompoundAdditionTransformer(compound_value)

    return str(transformer.transform(tree))


def transform_attribute_query_to_function(
    enum_type: type[Enum],
    query: str,
    aliases: dict[str, str] | None = None,
    *,
    complementary_type: type[Enum] | None = None,
    strip_compounds: bool = False,
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

    if strip_compounds:
        strip_transformer = CompoundStripTransformer()
        tree = strip_transformer.transform(tree)

    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerFunction(
        enum_type, aliases, complementary_type=complementary_type,
    )
    tree = syntax_sugar_transformer.transform(tree)
    return cast(Matcher, transformer.transform(tree))


def transform_attribute_query_to_sql_expression(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
    *,
    complementary_type: type[Enum] | None = None,
    complementary_column: Column | None = None,
    strip_compounds: bool = False,
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

    if strip_compounds:
        strip_transformer = CompoundStripTransformer()
        tree = strip_transformer.transform(tree)

    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerSQL(
        column, enum_type, aliases,
        complementary_column=complementary_column,
        complementary_type=complementary_type,
    )

    tree = syntax_sugar_transformer.transform(tree)
    return cast(Expression, transformer.transform(tree))


def transform_attribute_query_to_sql_expression_schema1(
    enum_type: type[Enum],
    query: str,
    column: Column,
    aliases: dict[str, str] | None = None,
    *,
    complementary_type: type[Enum] | None = None,
    complementary_column: Column | None = None,
    strip_compounds: bool = False,
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

    if strip_compounds:
        strip_transformer = CompoundStripTransformer()
        tree = strip_transformer.transform(tree)

    syntax_sugar_transformer = SyntaxSugarTransformer()
    transformer = AttributeQueryTransformerSQLLegacy(
        column, enum_type, aliases,
        complementary_column=complementary_column,
        complementary_type=complementary_type,
    )

    tree = syntax_sugar_transformer.transform(tree)
    return cast(Expression, transformer.transform(tree))


def create_or_node(left: Tree, right: Tree) -> Tree:
    return Tree("or_", children=[left, right])


def create_and_node(left: Tree, right: Tree) -> Tree:
    return Tree("and_", children=[left, right])
