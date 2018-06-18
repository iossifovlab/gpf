import functools

from lark import Lark, InlineTransformer
from lark.reconstruct import Reconstructor

from variants.attributes import Role, Inheritance, VariantType, Sex
from variants.attributes_query_builder import is_token

QUERY_GRAMMAR = """
    start: expression

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


class QueryTransformer(InlineTransformer):
    
    def __init__(self, parser, token_converter=None):
        super(QueryTransformer, self).__init__()

        if token_converter is None:
            token_converter = lambda x: x

        self.parser = parser
        self.tree = None
        self.token_transformer = token_converter

    def transform(self, tree):
        self.tree = tree
        return super(QueryTransformer, self).transform(tree)

    def less_than(self, *args):
        return lambda l: l > args[0]

    def more_than(self, *args):
        return lambda l: l < args[0]

    def arg(self, *args):
        return lambda l: args[0] in l

    def simple_arg(self, *args):
        return self.token_transformer(args[0])

    def negation(self, *args):
        assert len(args) == 1
        arg = args[0]
        return lambda l: not arg(l)

    def logical_and(self, *args):
        return lambda l: all(f(l) for f in args)

    def logical_or(self, *args):
        return lambda l: any(f(l) for f in args)

    def start(self, *args):
        assert len(args) == 1
        return Matcher(self.tree, self.parser, args[0])

    def eq(self, *args):
        return lambda x: x == set(args)

    def any(self, *args):
        return lambda l: any(f(l) for f in args)

    def all(self, *args):
        return lambda l: all(f(l) for f in args)


def roles_converter(a):
    return Role.from_name(a)


def sex_converter(a):
    return Sex.from_name(a)


def inheritance_converter(a):
    return Inheritance.from_name(a)


def variant_type_converter(a):
    return VariantType.from_name(a)


RoleQuery = functools.partial(QueryTransformer, token_converter=roles_converter)

SexQuery = functools.partial(QueryTransformer, token_converter=sex_converter)

InheritanceQuery = functools.partial(
    QueryTransformer, token_converter=inheritance_converter)

VariantTypeQuery = functools.partial(
    QueryTransformer, token_converter=variant_type_converter)
