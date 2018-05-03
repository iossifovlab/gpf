from lark import Lark, Tree
from lark.lexer import Token

QUERY_GRAMMAR = """
    start: expression

    ?expression: test

    ?test: or

    ?or: and (" " "or" " " and)*

    ?and: molecule (" " "and" " " molecule)*

    ?molecule: functions
        | not
        | atom

    not: "not" " " molecule

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
