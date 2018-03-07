'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
import enum
import ast


class Role(enum.Enum):

    prb = 1
    sib = 1 << 1
    child = 1 << 2

    maternal_half_sibling = 1 << 3
    paternal_half_sibling = 1 << 4

    parent = 1 << 5

    mom = 1 << 6
    dad = 1 << 7

    step_mom = 1 << 8
    step_dad = 1 << 9
    spouse = 1 << 10

    maternal_cousin = 1 << 11
    paternal_cousin = 1 << 12

    maternal_uncle = 1 << 13
    maternal_aunt = 1 << 14
    paternal_uncle = 1 << 15
    paternal_aunt = 1 << 16

    maternal_grandmother = 1 << 17
    maternal_grandfather = 1 << 18
    paternal_grandmother = 1 << 19
    paternal_grandfather = 1 << 20

    unknown = 1 << 31

    all = prb | sib | child | \
        maternal_half_sibling | paternal_half_sibling | \
        parent | \
        mom | dad | \
        step_mom | step_dad | spouse | \
        maternal_cousin | paternal_cousin | \
        maternal_uncle | maternal_aunt | paternal_uncle | paternal_aunt | \
        maternal_grandfather | maternal_grandmother | \
        paternal_grandfather | paternal_grandmother | \
        unknown

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
        if name == 'male' or name == 'M':
            return Sex.male
        elif name == 'female' or name == 'F':
            return Sex.female
        elif name == 'unspecified' or name == 'U':
            return Sex.unspecified
        raise ValueError("unexpected sex type: " + name)

    @staticmethod
    def from_value(val):
        return Sex(int(val))

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Inheritance(enum.Enum):
    mendelian = 1
    denovo = 1 << 1
    omission = 1 << 2
    other = 1 << 3
    unknown = 1 << 15

    @staticmethod
    def from_name(name):
        assert name in Inheritance.__members__
        return Inheritance[name]

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


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
        assert len(node.values) == 2

        left = self.visit(node.values[0])
        right = self.visit(node.values[1])

        if isinstance(node.op, ast.And):
            return QAnd([left, right])
        elif isinstance(node.op, ast.Or):
            return QOr([left, right])

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
