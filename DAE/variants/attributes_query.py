import functools

from lark import Lark, InlineTransformer, Tree
from lark.reconstruct import Reconstructor
from lark.tree import Discard

from variants.attributes import Role, Inheritance, VariantType, Sex
from variants.attributes_query_builder import is_token, tree as create_tree,\
    is_tree

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

    ?atom: "(" logical_or ")" | less_than | more_than | arg

    less_than: ">" SIGNED_NUMBER

    more_than: "<" SIGNED_NUMBER

    arg: simple_arg

    simple_arg: STRING | "'" STRING "'" | "\\"" STRING "\\""
    
    STRING : ("_"|LETTER|DIGIT|"."|"-")+

    _arglist: (arg "," )* arg [","]

    _simplearglist: (simple_arg "," )* simple_arg [","]

    %import common.SIGNED_NUMBER -> SIGNED_NUMBER
    %import common.LETTER -> LETTER
    %import common.DIGIT -> DIGIT
    %import common.WS_INLINE -> WS

    %ignore WS
"""

parser_with_ambiguity = Lark(QUERY_GRAMMAR, ambiguity='explicit')

parser = Lark(QUERY_GRAMMAR)


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


class QueryTransformerMatcher(object):
    def __init__(self, parser=parser, token_converter=None):
        self.parser = parser
        self.transformer = QueryTransformer(parser, token_converter)
        self.transformer2 = QueryTransformerStageTwo()

    def parse(self, expression):
        return self.parser.parse(expression)

    def parse_to_stage2(self, expression):
        parsed = self.parser.parse(expression)
        return self.transformer.transform(parsed)

    def transform(self, tree):
        matcher = self.transformer.transform(tree)
        matcher = self.transformer2.transform(matcher)
        return Matcher(tree, parser, matcher)

    def transform_from_stage2(self, tree):
        matcher = self.transformer2.transform(tree)
        return Matcher(tree, parser, matcher)

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))


class QueryTransformer(InlineTransformer):
    
    def __init__(self, parser=parser, token_converter=None):
        super(QueryTransformer, self).__init__()

        if token_converter is None:
            token_converter = lambda x: x

        self.token_converter = token_converter

    def less_than(self, *args):
        return LessThanNode(args[0])

    def more_than(self, *args):
        return MoreThanNode(args[0])

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


class Node(object):
    def __init__(self, children):
        self.children = children


class AndNode(Node):
    def __init__(self, children):
        super(AndNode, self).__init__(children)


class OrNode(Node):
    def __init__(self, children):
        super(OrNode, self).__init__(children)


class NotNode(Node):
    def __init__(self, children):
        super(NotNode, self).__init__([children])


class EqualsNode(Node):
    def __init__(self, children):
        super(EqualsNode, self).__init__(children)


class ContainsNode(Node):
    def __init__(self, children):
        super(ContainsNode, self).__init__(children)


class LessThanNode(Node):
    def __init__(self, children):
        super(LessThanNode, self).__init__(children)


class MoreThanNode(Node):
    def __init__(self, children):
        super(MoreThanNode, self).__init__(children)


class QueryTransformerStageTwo(object):
    
    def transform(self, node):
        print(node)
        return getattr(self, type(node).__name__)(node)

    def LessThanNode(self, node):
        return lambda l: l > node.children

    def MoreThanNode(self, node):
        return lambda l: l < node.children

    def ContainsNode(self, node):
        return lambda l: node.children in l

    def EqualsNode(self, node):
        return lambda x: x == set(node.children)

    def NotNode(self, node):
        assert len(node.children) == 1
        child = node.children[0]
        return lambda l: not self.transform(child)(l)

    def AndNode(self, node):
        return lambda l: all(self.transform(f)(l) for f in node.children)

    def OrNode(self, node):
        return lambda l: any(self.transform(f)(l) for f in node.children)


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
