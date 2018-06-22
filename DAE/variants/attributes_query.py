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


class BaseQueryTransformerMatcher(object):
    def __init__(self, parser=parser, token_converter=None):
        self.parser = parser
        self.transformer = StringQueryToTreeTransformer(parser,
                                                        token_converter)

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
    def __init__(self, parser=parser, token_converter=None):
        super(QueryTransformerMatcher, self).__init__(parser, token_converter)
        self.transformer2 = QueryTreeToLambdaTransformer()

    def transform_tree_to_matcher(self, tree):
        matcher = self.transformer2.transform(tree)
        return Matcher(tree, parser, matcher)


class StringQueryToTreeTransformer(InlineTransformer):
    
    def __init__(self, parser=parser, token_converter=None):
        super(StringQueryToTreeTransformer, self).__init__()

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


class LessThanNode(LeafNode):
    def __init__(self, arg):
        super(LessThanNode, self).__init__(arg)


class MoreThanNode(LeafNode):
    def __init__(self, arg):
        super(MoreThanNode, self).__init__(arg)


class BaseTreeTransformer(object):
    def transform(self, node):
        if isinstance(node, TreeNode):
            children = [self.transform(c) for c in node.children]
            return getattr(self, type(node).__name__)(children)
        else:
            return getattr(self, type(node).__name__)(node.arg)


class QueryTreeToLambdaTransformer(BaseTreeTransformer):
    def LessThanNode(self, arg):
        return lambda l: l > arg

    def MoreThanNode(self, arg):
        return lambda l: l < arg

    def ContainsNode(self, arg):
        return lambda l: arg in l

    def EqualsNode(self, arg):
        return lambda x: x == set(arg)

    def NotNode(self, children):
        assert len(children) == 1
        child = children[0]
        return lambda l: not child(l)

    def AndNode(self, children):
        return lambda l: all(f(l) for f in children)

    def OrNode(self, children):
        return lambda l: any(f(l) for f in children)


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

    def LessThanNode(self, arg):
        return self.column_name + " > " + arg

    def MoreThanNode(self, arg):
        return self.column_name + " < " + arg

    def ContainsNode(self, arg):
        return self.column_name + " = " + arg

    def EqualsNode(self, arg):
        return self.column_name + " = " + arg

    def NotNode(self, children):
        assert len(children) == 1
        return "NOT " + children[0]

    def AndNode(self, children):
        return "(" + reduce((lambda x, y: x + " AND " + y), children) + ")"

    def OrNode(self, children):
        return "(" + reduce((lambda x, y: x + " OR " + y), children) + ")"


class QueryTreeToSQLListTransformer(QueryTreeToSQLTransformer):
    def ContainsNode(self, arg):
        return "array_contains(" + self.column_name + ", " + str(arg) + ")"

    def EqualsNode(self, arg):
        return "concat_ws('|'," + self.column_name + ")" + \
            " = concat_ws('|', array(" + \
            reduce((lambda x, y: x + ", " + y), arg) + "))"


class QuerySQLTransformerMatcher(BaseQueryTransformerMatcher):
    def __init__(self, column_name, parser=parser,
                 token_converter=lambda x: "'" + str(x) + "'"):
        super(QuerySQLTransformerMatcher, self).__init__(parser,
                                                         token_converter)
        self.transformer2 = QueryTreeToSQLTransformer(column_name)


class QuerySQLListTransformerMatcher(BaseQueryTransformerMatcher):
    def __init__(self, column_name, parser=parser, 
                 token_converter=lambda x: "'" + str(x) + "'"):
        super(QuerySQLListTransformerMatcher, self).__init__(parser,
                                                             token_converter)
        self.transformer2 = QueryTreeToSQLListTransformer(column_name)