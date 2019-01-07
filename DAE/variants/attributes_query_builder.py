from __future__ import unicode_literals
from lark import Tree, Transformer
from lark.lexer import Token

AND_NODE = "logical_and"
OR_NODE = "logical_or"
NOT_NODE = "negation"
ALL_NODE = "all"
ANY_NODE = "any"
EQ_NODE = "eq"
ARG_NODE = "arg"
SIMPLE_ARG_NODE = "simple_arg"

ALL_NODES = (AND_NODE, OR_NODE, NOT_NODE, ALL_NODE, ANY_NODE, EQ_NODE)


def token(value):
    return Token("STRING", value)


def arg(value):
    return arg_node([simple_arg_node([token(value)])])


def tree(operation, children):
    return Tree(operation, children)


def is_tree(object):
    return isinstance(object, Tree)


def is_token(object):
    return isinstance(object, Token)


def is_transformer(value):
    return isinstance(value, Transformer)


def is_and(object):
    return is_tree(object) and object.data == AND_NODE


def is_or(object):
    return is_tree(object) and object.data == OR_NODE


def is_not(object):
    return is_tree(object) and object.data == NOT_NODE


def is_all(object):
    return is_tree(object) and object.data == ALL_NODE


def is_any(object):
    return is_tree(object) and object.data == ANY_NODE


def is_eq(object):
    return is_tree(object) and object.data == EQ_NODE


def and_node(children):
    return tree(AND_NODE, children)


def or_node(children):
    return tree(OR_NODE, children)


def not_node(children):
    # assert len(children) == 1
    return tree(NOT_NODE, children)


def all_node(children):
    return tree(ALL_NODE, children)


def any_node(children):
    return tree(ANY_NODE, children)


def eq_node(children):
    return tree(EQ_NODE, children)


def arg_node(children):
    return tree(ARG_NODE, children)


def simple_arg_node(children):
    return tree(SIMPLE_ARG_NODE, children)
