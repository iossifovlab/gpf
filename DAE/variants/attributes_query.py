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

    eq: "eq"i "(" _arglist ")"

    ?atom: "(" logical_or ")" | less_than | more_than | eq_value

    less_than: ">" SIGNED_NUMBER

    more_than: "<" SIGNED_NUMBER

    eq_value: arg // For easier transform (adds "column name =")

    ?arg: simple_arg | "'" simple_arg "'" | "\\"" simple_arg "\\""

    simple_arg: STRING
    
    STRING : ("_"|LETTER|DIGIT|"."|"-")+

    _arglist: (arg "," )* arg [","]

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

    # def _get_func(self, name):
    #     print("_get_func " + name)
    #     return super(QueryTransformer, self)._get_func(name)

    def _transform_all_tokens(self, arguments):
        return [self._transform_token(arg) for arg in arguments]

    def _transform_token(self, argument):
        if is_token(argument):
            return lambda l: self.token_transformer(argument.value) in l
        assert callable(argument)
        return argument

    def negation(self, *args):
        args = self._transform_all_tokens(args)
        assert len(args) == 1
        arg = args[0]
        return lambda l: not arg(l)

    def logical_and(self, *args):
        args = self._transform_all_tokens(args)
        return lambda l: all(f(l) for f in args)

    def logical_or(self, *args):
        args = self._transform_all_tokens(args)
        return lambda l: any(f(l) for f in args)

    def start(self, *args):
        assert len(args) == 1
        args = self._transform_all_tokens(args)
        return Matcher(self.tree, self.parser, args[0])

    def eq(self, *args):
        for arg in args:
            assert is_token(arg), "eq expects only elements, not an expression"
        to_match = {self.token_transformer(arg.value) for arg in args}
        return lambda x: x == to_match

    def any(self, *args):
        return self.logical_or(*args)

    def all(self, *args):
        return self.logical_and(*args)


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
