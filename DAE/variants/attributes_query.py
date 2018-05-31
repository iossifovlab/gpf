import functools

from lark import Lark, InlineTransformer, Tree
from lark.reconstruct import Reconstructor
from lark.tree import Discard

from variants.attributes import Role, Inheritance, VariantType, Sex
from variants.attributes_query_builder import is_token, tree as create_tree,\
    is_tree

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

    ?atom: "(" logical_or ")"
        | NAME

    _arglist: (NAME "," )* NAME [","]

    %import common.CNAME -> NAME
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
    
    def __init__(self, parser=parser, token_converter=None):
        super(QueryTransformer, self).__init__()

        if token_converter is None:
            token_converter = lambda x: x

        self.parser = parser
        self.tree = None
        self.token_converter = token_converter

    def _transform(self, tree):
        items = []
        for c in tree.children:
            try:
                items.append(self._transform(c) if isinstance(c, Tree) else c)
            except Discard:
                pass
        try:
            f = self._get_func(tree.data)
        except AttributeError:
            return self.__default__(tree.data, items)
        else:
            return f(items)

    def parse(self, expression):
        return self.parser.parse(expression)

    def parse_and_transform(self, expression):
        return self.transform(self.parse(expression))

    def transform(self, tree):
        if is_token(tree) or tree.data != 'start':
            tree = create_tree('start', [tree])

        self.tree = tree
        print(tree)

        return self._transform(tree)

    def _transform_all_tokens(self, arguments):
        return [self._transform_token(arg) for arg in arguments]

    def _transform_token(self, argument):
        if is_token(argument):
            return lambda l: self.token_converter(argument.value) in l
        if callable(argument):
            return argument
        raise TypeError("unknown type", type(argument), argument)

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
        to_match = {self.token_converter(arg.value) for arg in args}
        return lambda x: x == to_match

    def any(self, *args):
        return self.logical_or(*args)

    def all(self, *args):
        return self.logical_and(*args)


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


role_query = QueryTransformer(token_converter=roles_converter)

sex_query = QueryTransformer(token_converter=sex_converter)

inheritance_query = QueryTransformer(token_converter=inheritance_converter)

variant_type_query = QueryTransformer(token_converter=variant_type_converter)
