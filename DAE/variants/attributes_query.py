from lark import Lark, Tree, InlineTransformer
from lark.lexer import Token

QUERY_GRAMMAR = """
    start: expression

    ?expression: test

    ?test: logical_or

    ?logical_or: logical_and (" " "or" " " logical_and)*

    ?logical_and: molecule (" " "and" " " molecule)*

    ?molecule: functions
        | negation
        | atom

    negation: "not" " " molecule -> negation

    ?functions: any | all | eq

    any: "any"i "(" arglist ")"

    all: "all"i "(" arglist ")"

    eq: "eq"i "(" arglist ")"

    ?atom: "(" test ")"
        | NAME

    arglist: (arg "," )* arg [","]

    arg: NAME

    %import common.CNAME -> NAME
    %import common.WS_INLINE -> WS

    %ignore WS
"""

parser_with_ambiguity = Lark(QUERY_GRAMMAR, ambiguity='explicit')

parser = Lark(QUERY_GRAMMAR)


def token(value):
    return Token("NAME", value)


def tree(operation, children):
    return Tree(operation, children)


def is_tree(object):
    return isinstance(object, Tree)


def is_token(object):
    return isinstance(object, Token)


def is_and(object):
    return is_tree(object) and object.data == "logical_and"


def is_or(object):
    return is_tree(object) and object.data == "logical_or"


def is_not(object):
    return is_tree(object) and object.data == "negation"


def is_all(object):
    return is_tree(object) and object.data == "all"


def is_any(object):
    return is_tree(object) and object.data == "any"


def is_eq(object):
    return is_tree(object) and object.data == "eq"


class Matcher(object):

    def __init__(self, matcher):
        assert matcher is not None
        self.matcher = matcher

    def match(self, array):
        if not isinstance(array, set):
            array = set(array)
        return self.matcher(array)


class QueryMatchTransformer(InlineTransformer):

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
        return Matcher(args[0])

