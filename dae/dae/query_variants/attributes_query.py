# pylint: disable=too-few-public-methods
import enum
from functools import reduce

from lark import Lark, InlineTransformer
from lark.visitors import Interpreter
from lark.reconstruct import Reconstructor

from dae.variants.core import Allele
from dae.variants.attributes import Role, Inheritance, Sex
from dae.variants.variant import allele_type_from_name


QUERY_GRAMMAR = """
    ?start: expression

    ?expression: logical_or

    ?logical_or: logical_and (" " "or" " " logical_and)*

    ?logical_and: molecule (" " "and" " " molecule)*

    ?molecule: functions
        | negation
        | atom

    negation: "not" " " molecule -> negation

    ?functions: any | all | eq

    any: "any"i "(" _arglist ")"

    all: "all"i "(" _arglist ")"

    eq: "eq"i "(" _simplearglist ")"

    ?atom: "(" logical_or ")" | less_than | more_than | less_than_eq
        | more_than_eq | arg

    less_than: ">" SIGNED_NUMBER

    more_than: "<" SIGNED_NUMBER

    less_than_eq: ">=" SIGNED_NUMBER

    more_than_eq: "<=" SIGNED_NUMBER

    arg: simple_arg

    simple_arg: STRING | "'" STRING "'" | "\\"" STRING "\\""

    STRING : ("_"|LETTER|DIGIT|"."|"-"|"'"|"+")+

    _arglist: (arg "," )* arg [","]

    _simplearglist: (simple_arg "," )* simple_arg [","]

    %import common.SIGNED_NUMBER -> SIGNED_NUMBER
    %import common.LETTER -> LETTER
    %import common.DIGIT -> DIGIT
    %import common.WS_INLINE -> WS

    %ignore WS
"""

parser_with_ambiguity = Lark(QUERY_GRAMMAR, ambiguity="explicit")

PARSER = Lark(QUERY_GRAMMAR)


class Matcher:
    """No idea what this class is supposed to do. If you know please edit."""

    def __init__(self, tree, parser, matcher):
        assert matcher is not None
        assert tree is not None
        assert parser is not None

        self.matcher = matcher
        self.tree = tree
        self.parser = parser
        self._reconstructor = Reconstructor(parser)

    def match(self, array):
        if not isinstance(array, set):
            array = set(array)
        return self.matcher(array)

    def pretty(self):
        return self.tree.pretty()

    def query_str(self):
        self._reconstructor.reconstruct(self.tree)


class BaseQueryTransformerMatcher:
    """Base class for query transformer matchers."""

    def __init__(self, parser=PARSER, token_converter=None):
        self.parser = parser
        self.transformer = StringQueryToTreeTransformer(
            parser, token_converter
        )
        self.transformer2 = None

    def parse(self, expression):
        return self.parser.parse(expression)

    def transform_query_string_to_tree(self, expression):
        parsed = self.parser.parse(expression)
        return self.transformer.transform(parsed)

    def transform(self, tree):
        return self.transform_tree_to_matcher(self.transformer.transform(tree))

    def transform_tree_to_matcher(self, tree):
        return self.transformer2.transform(tree)  # type: ignore

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))


class StringQueryToTreeTransformer(InlineTransformer):
    # pylint: disable=no-self-use
    """Convert tokens using a token converter."""

    def __init__(self, parser=PARSER, token_converter=None):
        # pylint: disable=unused-argument
        super().__init__()

        if token_converter is None:
            self.token_converter = lambda x: x
        else:
            self.token_converter = token_converter

    def less_than(self, *args):
        return LessThanNode(args[0])

    def more_than(self, *args):
        return GreaterThanNode(args[0])

    def less_than_eq(self, *args):
        return LessThanEqNode(args[0])

    def more_than_eq(self, *args):
        return GreaterThanEqNode(args[0])

    def arg(self, *args):
        return ContainsNode(args[0])

    def simple_arg(self, *args):
        return self.token_converter(args[0])

    def negation(self, *args):
        return NotNode(args[0])

    def logical_and(self, *args):
        return AndNode(args)

    def logical_or(self, *args):
        return OrNode(args)

    def start(self, *args):
        assert len(args) == 1
        return args[0]

    def eq(self, *args):
        # pylint: disable=invalid-name
        return EqualsNode(args)

    def any(self, *args):
        return OrNode(args)

    def all(self, *args):
        return AndNode(args)


class Leaf:
    # pylint: disable=invalid-name
    def __init__(self, op, value):
        self.value = value
        self.op = op


class LeafNode:
    def __init__(self, arg):
        self.arg = arg


class TreeNode:
    def __init__(self, children):
        self.children = children


class AndNode(TreeNode):
    pass


class OrNode(TreeNode):
    pass


class NotNode(TreeNode):
    def __init__(self, children):
        super().__init__([children])


class EqualsNode(LeafNode):
    pass


class ContainsNode(LeafNode):
    pass


class ElementOfNode(LeafNode):
    pass


class LessThanNode(LeafNode):
    pass


class GreaterThanNode(LeafNode):
    pass


class LessThanEqNode(LeafNode):
    pass


class GreaterThanEqNode(LeafNode):
    pass


class BaseTreeTransformer:
    def transform(self, node):
        if isinstance(node, TreeNode):
            children = [self.transform(c) for c in node.children]
            return getattr(self, type(node).__name__)(children)
        return getattr(self, type(node).__name__)(node.arg)


class QueryTreeToLambdaTransformer(BaseTreeTransformer):
    # pylint: disable=no-self-use,invalid-name
    """Transforma all nodes to python lambda functions."""

    def LessThanNode(self, arg):
        return lambda x: x > arg

    def GreaterThanNode(self, arg):
        return lambda x: x < arg

    def LessThanEqNode(self, arg):
        return lambda x: x >= arg

    def GreaterThanEqNode(self, arg):
        return lambda x: x <= arg

    def ContainsNode(self, arg):
        return lambda x: arg in x

    def ElementOfNode(self, arg):
        return lambda x: x in arg

    def EqualsNode(self, arg):
        return lambda x: x == set(arg)

    def NotNode(self, children):
        assert len(children) == 1
        child = children[0]
        return lambda x: not child(x)

    def AndNode(self, children):
        return lambda x: all(f(x) for f in children)

    def OrNode(self, children):
        return lambda x: any(f(x) for f in children)


class QueryTreeToBitwiseLambdaTransformer(BaseTreeTransformer):
    # pylint: disable=no-self-use,invalid-name
    """No idea what this is supposed to do. Please edit."""

    def ContainsNode(self, arg):
        return lambda vals: any(arg & v for v in vals if v is not None)

    def LessThanNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def GreaterThanNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def LessThanEqNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def GreaterThanEqNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def ElementOfNode(self, arg):
        return lambda x: any(x & a for a in arg)

    def EqualsNode(self, arg):
        return lambda val: all(val & a for a in arg)

    def NotNode(self, children):
        assert len(children) == 1
        child = children[0]
        return lambda x: not child(x)

    def AndNode(self, children):
        return lambda x: all(child(x) for child in children)

    def OrNode(self, children):
        return lambda x: any(child(x) for child in children)


def roles_converter(arg):
    if not isinstance(arg, Role):
        return Role.from_name(arg)
    return arg


def sex_converter(arg):
    if not isinstance(arg, Sex):
        return Sex.from_name(arg)
    return arg


def inheritance_converter(arg):
    if not isinstance(arg, Inheritance):
        return Inheritance.from_name(arg)
    return arg


def variant_type_converter(arg):
    if not isinstance(arg, Allele.Type):
        return allele_type_from_name(arg)
    return arg


class QueryTreeToSQLTransformer(BaseTreeTransformer):
    # pylint: disable=invalid-name
    """I don't know what this class does. Please edit if you do."""

    def __init__(self, column_name):
        self.column_name = column_name
        super().__init__()

    @staticmethod
    def token_converter(arg):
        if isinstance(arg, enum.Enum):
            return str(arg.value)
        return str(arg)

    def LessThanNode(self, arg):
        return self.column_name + " > " + self.token_converter(arg)

    def GreaterThanNode(self, arg):
        return self.column_name + " < " + self.token_converter(arg)

    def LessThanEqNode(self, arg):
        return self.column_name + " >= " + self.token_converter(arg)

    def GreaterThanEqNode(self, arg):
        return self.column_name + " <= " + self.token_converter(arg)

    def ContainsNode(self, arg):
        return self.column_name + " = " + self.token_converter(arg)

    def ElementOfNode(self, arg):
        return self.column_name + " IN " + self.token_converter(arg)

    def EqualsNode(self, arg):
        return self.column_name + " = " + self.token_converter(arg)

    @staticmethod
    def NotNode(children):
        assert len(children) == 1
        return "NOT (" + children[0] + ")"

    @staticmethod
    def AndNode(children):
        return "(" + reduce((lambda x, y: x + " AND " + y), children) + ")"

    @staticmethod
    def OrNode(children):
        return "(" + reduce((lambda x, y: x + " OR " + y), children) + ")"


class QueryTreeToSQLListTransformer(QueryTreeToSQLTransformer):
    """I don't know what this class does. Please edit if you do."""

    def ContainsNode(self, arg):
        return (
            "array_contains("
            + self.column_name
            + ", "
            + self.token_converter(arg)
            + ")"
        )

    def ElementOfNode(self, arg):
        if not arg:
            return self.column_name + " IS NULL"
        return (
            self.column_name
            + " IN ("
            + ",".join([self.token_converter(a) for a in arg])
            + ")"
        )

    def EqualsNode(self, arg):
        arg = [self.token_converter(a) for a in arg]
        return (
            "concat_ws('|',"
            + self.column_name
            + ")"
            + " = concat_ws('|', array("
            + reduce((lambda x, y: x + ", " + y), arg)
            + "))"
        )


def get_bit_and_str(arg1, arg2, use_bit_and_function):
    if use_bit_and_function:
        return f"BITAND({arg1}, {arg2})"
    else:
        return f"({arg1} & {arg2})"


class QueryTreeToSQLBitwiseTransformer(QueryTreeToSQLTransformer):
    """I don't know what this class does. Please edit if you do."""

    def __init__(self, column_name, use_bit_and_function=True):
        super().__init__(column_name)
        self.use_bit_and_function = use_bit_and_function

    def ContainsNode(self, arg):
        converted_token = self.token_converter(arg)
        bit_op = get_bit_and_str(self.column_name, converted_token,
                                 self.use_bit_and_function)
        return f"{bit_op} != 0"

    def LessThanNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def GreaterThanNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def LessThanEqNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def GreaterThanEqNode(self, arg):
        raise NotImplementedError("unexpected bitwise query")

    def ElementOfNode(self, arg):
        converted_token = self.token_converter(arg)
        bit_op = get_bit_and_str(self.column_name, converted_token,
                                 self.use_bit_and_function)
        return f"{bit_op} != 0"

    def EqualsNode(self, arg):
        return self.column_name + " = " + self.token_converter(arg)

    @staticmethod
    def NotNode(children):
        assert len(children) == 1
        return f"(NOT ({children[0]}))"

    @staticmethod
    def AndNode(children):
        res = reduce(lambda x, y: f"({x}) AND ({y})", children)
        return res

    @staticmethod
    def OrNode(children):
        res = reduce(lambda x, y: f"({x}) OR ({y})", children)
        return res


class StringQueryToTreeTransformerWrapper:
    """No idea what this is supposed to do. Please edit."""

    def __init__(self, parser=PARSER, token_converter=None):
        self.parser = parser
        self.transformer = StringQueryToTreeTransformer(
            parser, token_converter
        )

    def parse(self, expression):
        return self.parser.parse(expression)

    def transform(self, tree):
        return self.transformer.transform(tree)

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))


class StringListQueryToTreeTransformer:
    """No idea what this is supposed to do. Please edit."""

    @staticmethod
    def parse_and_transform(expression):
        assert isinstance(expression, list)
        return ElementOfNode(expression)


class BitwiseTreeTransformer(Interpreter):
    # pylint: disable=invalid-name,no-self-use
    """Transform bitwise expressions."""

    def __init__(self, token_converter):
        super().__init__()
        self.parser = PARSER
        self.token_converter = token_converter

    def less_than(self, *args):
        raise NotImplementedError()

    def more_than(self, *args):
        raise NotImplementedError()

    def less_than_eq(self, *args):
        raise NotImplementedError()

    def more_than_eq(self, *args):
        raise NotImplementedError()

    def eq(self, *args):
        raise NotImplementedError()

    def arg(self, *args):
        return ContainsNode(args[0])

    def simple_arg(self, *args):
        return self.token_converter(args[0])

    def negation(self, *args):
        return NotNode(args[0])

    def logical_and(self, *args):
        return AndNode(args)

    def logical_or(self, *args):
        return OrNode(args)

    def start(self, *args):
        assert len(args) == 1
        return args[0]

    def any(self, *args):
        return OrNode(args)

    def all(self, *args):
        return AndNode(args)


class QueryTransformerMatcher(BaseQueryTransformerMatcher):
    """No idea what this is supposed to do. Please edit."""

    def __init__(
            self, parser=PARSER, token_converter=None,
            transformer2=QueryTreeToLambdaTransformer()):

        super().__init__(parser, token_converter)
        self.transformer2 = transformer2

    def transform_tree_to_matcher(self, tree):
        matcher = self.transformer2.transform(tree)  # type: ignore
        return Matcher(tree, self.parser, matcher)


role_query = QueryTransformerMatcher(token_converter=roles_converter)

sex_query = QueryTransformerMatcher(token_converter=sex_converter)

inheritance_query = QueryTransformerMatcher(
    token_converter=inheritance_converter
)

variant_type_query = QueryTransformerMatcher(
    token_converter=variant_type_converter,
    transformer2=QueryTreeToBitwiseLambdaTransformer()
)
