from lark import Tree
from lark.lexer import Token

AND_NODE = "logical_and"
OR_NODE = "logical_or"
NOT_NODE = "negation"
ALL_NODE = "all"
ANY_NODE = "any"
EQ_NODE = "eq"

ALL_NODES = (AND_NODE, OR_NODE, NOT_NODE, ALL_NODE, ANY_NODE, EQ_NODE)


def token(value):
    return Token("NAME", value)


def tree(operation, children):
    return Tree(operation, children)


def is_tree(object):
    return isinstance(object, Tree)


def is_token(object):
    return isinstance(object, Token)


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


def expand_children(child):
    if not is_tree(child) or is_token(child) or child.data != 'start':
        return [child]
    result = []
    for child in child.children:
        result.extend(expand_children(child))
    return result


def substitute_beginning(children):
    result = []

    for child in children:
        result.extend(expand_children(child))

    return result


def and_node(children):
    if len(children) == 1:
        return children[0]
    children = substitute_beginning(children)
    return tree(AND_NODE, children)


def or_node(children):
    if len(children) == 1:
        return children[0]

    children = substitute_beginning(children)
    return tree(OR_NODE, children)


def not_node(child):
    children = expand_children(child)
    assert len(children) == 1
    return tree(NOT_NODE, children)


def all_node(children):
    return tree(ALL_NODE, children)


def any_node(children):
    return tree(ANY_NODE, children)


def eq_node(children):
    return tree(EQ_NODE, children)
