from __future__ import unicode_literals

from builtins import str
from builtins import object
import enum

from lark import Lark, InlineTransformer
from lark.reconstruct import Reconstructor
from functools import reduce

from variants.attributes import Role, Inheritance, VariantType, Sex


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

parser_with_ambiguity = Lark(QUERY_GRAMMAR, ambiguity='explicit')

PARSER = Lark(QUERY_GRAMMAR)


class Matcher(object):
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


class BaseQueryTransformerMatcher(object):
    def __init__(self, parser=PARSER, token_converter=None):
        self.parser = parser
        self.transformer = StringQueryToTreeTransformer(parser,
                                                        token_converter)
        self.transformer2 = None

    def parse(self, expression):
        return self.parser.parse(expression)

    def transform_query_string_to_tree(self, expression):
        parsed = self.parser.parse(expression)
        return self.transformer.transform(parsed)

    def transform(self, tree):
        return self.transform_tree_to_matcher(self.transformer.transform(tree))

    def transform_tree_to_matcher(self, tree):
        return self.transformer2.transform(tree)

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))


class QueryTransformerMatcher(BaseQueryTransformerMatcher):
    def __init__(self, parser=PARSER, token_converter=None):
        super(QueryTransformerMatcher, self).__init__(
            parser, token_converter)
        self.transformer2 = QueryTreeToLambdaTransformer()

    def transform_tree_to_matcher(self, tree):
        matcher = self.transformer2.transform(tree)
        return Matcher(tree, self.parser, matcher)


class StringQueryToTreeTransformer(InlineTransformer):

    def __init__(self, parser=PARSER, token_converter=None):
        super(StringQueryToTreeTransformer, self).__init__()

        if token_converter is None:
            def token_converter(x): return x

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
        return EqualsNode(args)

    def any(self, *args):
        return OrNode(args)

    def all(self, *args):
        return AndNode(args)


class Leaf(object):
    def __init__(self, op, value):
        self.value = value
        self.op = op


class LeafNode(object):
    def __init__(self, arg):
        self.arg = arg


class TreeNode(object):
    def __init__(self, children):
        self.children = children


class AndNode(TreeNode):
    def __init__(self, children):
        super(AndNode, self).__init__(children)


class OrNode(TreeNode):
    def __init__(self, children):
        super(OrNode, self).__init__(children)


class NotNode(TreeNode):
    def __init__(self, children):
        super(NotNode, self).__init__([children])


class EqualsNode(LeafNode):
    def __init__(self, arg):
        super(EqualsNode, self).__init__(arg)


class ContainsNode(LeafNode):
    def __init__(self, arg):
        super(ContainsNode, self).__init__(arg)


class ElementOfNode(LeafNode):
    def __init__(self, arg):
        super(ElementOfNode, self).__init__(arg)


class LessThanNode(LeafNode):
    def __init__(self, arg):
        super(LessThanNode, self).__init__(arg)


class GreaterThanNode(LeafNode):
    def __init__(self, arg):
        super(GreaterThanNode, self).__init__(arg)


class LessThanEqNode(LeafNode):
    def __init__(self, arg):
        super(LessThanEqNode, self).__init__(arg)


class GreaterThanEqNode(LeafNode):
    def __init__(self, arg):
        super(GreaterThanEqNode, self).__init__(arg)


class BaseTreeTransformer(object):
    def transform(self, node):
        if isinstance(node, TreeNode):
            children = [self.transform(c) for c in node.children]
            return getattr(self, type(node).__name__)(children)
        else:
            return getattr(self, type(node).__name__)(node.arg)


class QueryTreeToLambdaTransformer(BaseTreeTransformer):
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


def roles_converter(a):
    if not isinstance(a, Role):
        return Role.from_name(a)
    return a


def sex_converter(a):
    if not isinstance(a, Sex):
        return Sex.from_name(a)
    return a


def inheritance_converter(a):
    if not isinstance(a, Inheritance):
        return Inheritance.from_name(a)
    return a


def variant_type_converter(a):
    if not isinstance(a, VariantType):
        return VariantType.from_name(a)
    return a


role_query = QueryTransformerMatcher(token_converter=roles_converter)

sex_query = QueryTransformerMatcher(token_converter=sex_converter)

inheritance_query = QueryTransformerMatcher(
    token_converter=inheritance_converter)

variant_type_query = QueryTransformerMatcher(
    token_converter=variant_type_converter)


class QueryTreeToSQLTransformer(BaseTreeTransformer):
    def __init__(self, column_name):
        self.column_name = column_name
        super(QueryTreeToSQLTransformer, self).__init__()

    def token_converter(self, arg):
        if isinstance(arg, enum.Enum):
            return str(arg.value)
        else:
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

    def NotNode(self, children):
        assert len(children) == 1
        return "NOT " + children[0]

    def AndNode(self, children):
        return "(" + reduce((lambda x, y: x + " AND " + y), children) + ")"

    def OrNode(self, children):
        return "(" + reduce((lambda x, y: x + " OR " + y), children) + ")"


class QueryTreeToSQLListTransformer(QueryTreeToSQLTransformer):
    def ContainsNode(self, arg):
        return "array_contains(" + self.column_name + ", " + \
            self.token_converter(arg) + ")"

    def ElementOfNode(self, arg):
        if not arg:
            return self.column_name + " IS NULL"
        return self.column_name + " IN (" + \
            ",".join([self.token_converter(a) for a in arg]) + ")"

    def EqualsNode(self, arg):
        arg = [self.token_converter(a) for a in arg]
        return "concat_ws('|'," + self.column_name + ")" + \
            " = concat_ws('|', array(" + \
            reduce((lambda x, y: x + ", " + y), arg) + "))"


# class RegionsQueryToSQLTransformer(object):
#
#     def __init__(self):
#         pass
#
#     def parse(self, regions):
#         assert all([isinstance(r, Region) for r in regions])
#         pass
#
#     def parse_region(self, region):
#         assert isinstance(region, Region)
#         return {
#             'chrom': EqualsNode(region.chr),
#             'position': AndNode([
#                 GreaterThanEqNode(region.start),
#                 LessThanEqNode(region.stop),
#             ])
#         }


class StringQueryToTreeTransformerWrapper(object):
    def __init__(self, parser=PARSER, token_converter=None):
        self.parser = parser
        self.transformer = StringQueryToTreeTransformer(
            parser,
            token_converter)

    def parse(self, expression):
        return self.parser.parse(expression)

    def transform(self, tree):
        return self.transformer.transform(tree)

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))


class StringListQueryToTreeTransformer(object):
    def __init__(self):
        pass

    def parse_and_transform(self, expression):
        assert isinstance(expression, list)
        return ElementOfNode(expression)
