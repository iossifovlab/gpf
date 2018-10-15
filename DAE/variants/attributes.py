'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from builtins import object
import enum
import ast


class Role(enum.Enum):

    maternal_grandmother = 1
    maternal_grandfather = 2
    paternal_grandmother = 3
    paternal_grandfather = 4

    mom = 10
    dad = 11
    parent = 12

    prb = 20
    sib = 21
    child = 22

    maternal_half_sibling = 30
    paternal_half_sibling = 31

    maternal_aunt = 50
    maternal_uncle = 51
    paternal_aunt = 52
    paternal_uncle = 53

    maternal_cousin = 60
    paternal_cousin = 61

    step_mom = 70
    step_dad = 71
    spouse = 72

    unknown = 100

    def __repr__(self):
        return self.name
        # return "{}: {:023b}".format(self.name, self.value)

    def __str__(self):
        return self.name

    @staticmethod
    def from_name(name):
        if name in Role.__members__:
            return Role[name]
        else:
            return Role.unknown


class Sex(enum.Enum):
    male = 1
    female = 2
    unspecified = 4

    @staticmethod
    def from_name(name):
        if name == 'male' or name == 'M' or name == '1':
            return Sex.male
        elif name == 'female' or name == 'F' or name == '2':
            return Sex.female
        elif name == 'unspecified' or name == 'U':
            return Sex.unspecified
        raise ValueError("unexpected sex type: " + name)

    @staticmethod
    def from_value(val):
        return Sex(int(val))

    @classmethod
    def from_name_or_value(cls, name_or_value):
        try:
            return cls.from_name(name_or_value)
        except ValueError:
            return cls.from_value(name_or_value)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def short(self):
        return self.name[0].upper()


class Inheritance(enum.Enum):
    reference = 1
    mendelian = 2
    denovo = 3
    omission = 4
    other = 5
    missing = 6
    unknown = 100

    @staticmethod
    def from_name(name):
        assert name in Inheritance.__members__
        return Inheritance[name]

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class VariantType(enum.Enum):
    invalid = 0
    substitution = 1
    insertion = 2
    deletion = 3
    complex = 4
    CNV = 5

    @staticmethod
    def from_name(name):
        if name == 'sub' or name == 'substitution':
            return VariantType.substitution
        elif name == 'ins' or name == 'insertion':
            return VariantType.insertion
        elif name == 'del' or name == 'deletion':
            return VariantType.deletion
        elif name == 'complex':
            return VariantType.complex
        elif name == 'CNV':
            return VariantType.CNV
        raise ValueError("unexpected variant type: {}".format(name))

    @staticmethod
    def from_cshl_variant(variant):
        if variant is None:
            return VariantType.none

        vt = variant[0]
        if vt == 's':
            return VariantType.substitution
        elif vt == 'i':
            return VariantType.insertion
        elif vt == 'd':
            return VariantType.deletion
        elif vt == 'c':
            return VariantType.complex
        elif vt == 'C':
            return VariantType.CNV
        else:
            raise ValueError("unexpected variant type: {}".format(variant))

    def __repr__(self):
        return self.name[:3]

    def __str__(self):
        return self.name[:3]


class QNode(object):
    def __init__(self, vals=None, children=None):
        self.vals = vals
        self.children = children

    def match(self, vals):
        raise NotImplemented()


class QComposite(QNode):

    def __init__(self, children):
        assert isinstance(children, list)
        assert all([isinstance(ch, QNode) for ch in children])
        super(QComposite, self).__init__(children=children)


class QLeaf(QNode):

    def __init__(self, vals):
        assert isinstance(vals, set)
        assert all([isinstance(v, enum.Enum) for v in vals]) or \
            all([isinstance(v, str) for v in vals]) or \
            all([isinstance(v, str) for v in vals])
        super(QLeaf, self).__init__(vals=vals)


class QAnd(QComposite):
    def __init__(self, children):
        super(QAnd, self).__init__(children=children)

    def match(self, vals):
        return all([q.match(vals) for q in self.children])


class QOr(QComposite):
    def __init__(self, children):
        super(QOr, self).__init__(children=children)

    def match(self, vals):
        return any([q.match(vals) for q in self.children])


class QNot(QComposite):
    def __init__(self, children):
        assert len(children) == 1
        super(QNot, self).__init__(children=children)

    def match(self, vals):
        q = self.children[0]
        return not q.match(vals)


class QAll(QLeaf):
    def __init__(self, vals):
        super(QAll, self).__init__(vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return not bool(self.vals - vals)


class QAny(QLeaf):
    def __init__(self, vals):
        super(QAny, self).__init__(vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return bool(self.vals & vals)


class QEq(QLeaf):
    def __init__(self, vals):
        super(QEq, self).__init__(vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return self.vals == vals


class AQVisitor(ast.NodeVisitor):

    def __init__(self, attr_converter, *args, **kwargs):
        ast.NodeVisitor.__init__(self, *args, **kwargs)
        self.attr_converter = attr_converter

    def visit(self, node):
        return ast.NodeVisitor.visit(self, node)

    def visit_Call(self, node):
        assert isinstance(node, ast.Call)
        assert node.func.id in set(['eq', 'any', 'all'])

        vals = set([self.attr_converter(a.id) for a in node.args])
        pred = node.func.id
        if pred == 'eq':
            return QEq(vals)
        elif pred == 'any':
            return QAny(vals)
        elif pred == 'all':
            return QAll(vals)

    def visit_Expression(self, node):
        assert isinstance(node, ast.Expression)
        return self.visit(node.body)

    def visit_BoolOp(self, node):
        assert isinstance(node, ast.BoolOp)
        assert len(node.values) >= 2

        leafs = [self.visit(n) for n in node.values]

        if isinstance(node.op, ast.And):
            return QAnd(leafs)
        elif isinstance(node.op, ast.Or):
            return QOr(leafs)

    def visit_Name(self, node):
        assert isinstance(node.ctx, ast.Load)
        attr = self.attr_converter(node.id)
        return QAny(set([attr]))

    def visit_UnaryOp(self, node):
        assert isinstance(node, ast.UnaryOp)

        assert isinstance(node.op, ast.Not)
        operand = self.visit(node.operand)
        return QNot([operand])

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.BitAnd):
            return QAnd([left, right])
        elif isinstance(node.op, ast.BitOr):
            return QOr([left, right])
        else:
            assert False, "unexpected binary operation"


class AQuery(object):

    @staticmethod
    def attr_converter(a):
        return str(a)

    def __init__(self, qnode):
        self.qnode = qnode

    def and_(self, rq):
        self.qnode = QAnd([self.qnode, rq.qnode])
        return self

    def or_(self, rq):
        self.qnode = QOr([self.qnode, rq.qnode])
        return self

    def and_not_(self, rq):
        self.qnode = QAnd([self.qnode, QNot([rq.qnode])])
        return self

    def or_not_(self, rq):
        self.qnode = QOr([self.qnode, QNot([rq.qnode])])
        return self

    def not_(self):
        self.qnode = QNot([self.qnode])
        return self

    @classmethod
    def any_of(cls, *vals):
        qnode = QAny(set(vals))
        return cls(qnode)

    @classmethod
    def all_of(cls, *vals):
        qnode = QAll(set(vals))
        return cls(qnode)

    @classmethod
    def eq_of(cls, *vals):
        qnode = QEq(set(vals))
        return cls(qnode)

    def match(self, vals):
        return self.qnode.match(set(vals))

    @classmethod
    def parse(cls, query):
        tree = ast.parse(query, mode='eval')
        visitor = AQVisitor(cls.attr_converter)
        return cls(visitor.visit(tree))


class RoleQuery(AQuery):
    @staticmethod
    def attr_converter(a):
        return Role.from_name(a)


class SexQuery(AQuery):
    @staticmethod
    def attr_converter(a):
        return Sex.from_name(a)


class InheritanceQuery(AQuery):
    @staticmethod
    def attr_converter(a):
        return Inheritance.from_name(a)


class VariantTypeQuery(AQuery):
    @staticmethod
    def attr_converter(a):
        return VariantType.from_name(a)

    @classmethod
    def parse(cls, query):
        query = query.replace("del", "deletion")
        return super(VariantTypeQuery, cls).parse(query)


# class RoleQuery(object):
#
#     def __init__(self, value, complement=Role.all.value):
#         self.value = value
#         self.complement = complement
#
#     def and_(self, role):
#         self.value &= role.value
#         return self
#
#     def and_not_(self, role):
#         print(self)
#         self.value &= (~role.value) & Role.all.value
#         print(self)
#         return self
#
#     def or_(self, role):
#         self.value |= role.value
#         return self
#
#     def or_not_(self, role):
#         self.value |= (~role.value & Role.all.value)
#         return self
#
#     @classmethod
#     def any_(cls, roles):
#         rqs = map(lambda r: cls(r.value), roles)
#         res = reduce(lambda r1, r2: r1.or_(r2), rqs)
#         return res
#
#     @classmethod
#     def all_(cls, roles):
#         rqs = map(lambda r: cls(r.value), roles)
#         res = reduce(lambda r1, r2: r1.or_(r2), rqs)
#         res.complement = ~res.value & Role.all.value
#         return res
#
#     def mask(self):
#         return (self.value & ~self.complement) & Role.all.value
#
#     def match(self, roles):
#         rq = roles
#         if isinstance(roles, list) or isinstance(roles, set):
#             rq = RoleQuery.any_(roles)
#         print("match: roles=", roles)
#
#         assert isinstance(rq, RoleQuery)
#
#         v1 = self.value ^ rq.complement
#         v2 = self.complement ^ rq.value
#         print("v1:", bv(v1))
#         print("v2:", bv(v2))
#
#         r = v1 & v2
#         print("r :", bv(r))
#         print(bv((r & ~self.complement) & Role.all.value))
#
#         return not bool((r & ~self.complement) & Role.all.value)
#
#     def __repr__(self):
#         return "\nq: {:023b}\nc: {:023b}".format(
#             self.value, self.complement)
