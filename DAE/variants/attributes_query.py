from lark import Lark, InlineTransformer
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

    def match(self, array):
        if not isinstance(array, set):
            array = set(array)
        return self.matcher(array)

    def pretty(self):
        return self.tree.pretty()


class QueryMatchTransformer(InlineTransformer):
    
    def __init__(self, parser):
        super(QueryMatchTransformer, self).__init__()
        self.parser = parser
        self.tree = None

    def transform(self, tree):
        self.tree = tree
        return super(QueryMatchTransformer, self).transform(tree)

    def _get_func(self, name):
        print("_get_func " + name)
        return super(QueryMatchTransformer, self)._get_func(name)

    def _transform_all_tokens(self, arguments):
        return [self._transform_token(arg) for arg in arguments]

    def _transform_token(self, argument):
        if is_token(argument):
            return lambda l: argument.value in l
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
            assert is_token(arg)
        to_match = {arg.value for arg in args}
        return lambda x: x == to_match

    def any(self, *args):
        return self.logical_or(*args)

    def all(self, *args):
        return self.logical_and(*args)
