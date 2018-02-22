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

    unknown = 1 << 21

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
        return "{}: {:023b}".format(self.name, self.value)

    @staticmethod
    def from_name(name):
        if name in Role.__members__:
            return Role[name]
        else:
            return Role.unknown


def bv(v):
    return "{:023b}".format(v)


@enum.unique
class QType(enum.Enum):
    ALL = 1
    ANY = 2
    EQ = 3
    AND = 4
    OR = 5
    NOT = 6


class QNode(object):
    def __init__(self, optype, vals=None, children=None):
        assert isinstance(optype, QType)
        self.optype = optype
        self.vals = vals
        self.children = children

    def match(self, vals):
        raise NotImplemented()


class QComposite(QNode):

    def __init__(self, optype, children):
        assert isinstance(children, list)
        assert all([isinstance(ch, QNode) for ch in children])
        super(QComposite, self).__init__(optype, children=children)


class QLeaf(QNode):

    def __init__(self, optype, vals):
        assert isinstance(vals, set)
        assert all([isinstance(v, enum.Enum) for v in vals])
        super(QLeaf, self).__init__(optype, vals=vals)


class QAnd(QComposite):
    def __init__(self, children):
        super(QAnd, self).__init__(QType.AND, children=children)

    def match(self, vals):
        return all([q.match(vals) for q in self.children])


class QOr(QComposite):
    def __init__(self, children):
        super(QOr, self).__init__(QType.OR, children=children)

    def match(self, vals):
        return any([q.match(vals) for q in self.children])


class QNot(QComposite):
    def __init__(self, children):
        assert len(children) == 1
        super(QNot, self).__init__(QType.NOT, children=children)

    def match(self, vals):
        q = self.children[0]
        return not q.match(vals)


class QAll(QLeaf):
    def __init__(self, vals):
        super(QAll, self).__init__(QType.ALL, vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return not bool(self.vals - vals)


class QAny(QLeaf):
    def __init__(self, vals):
        super(QAny, self).__init__(QType.ANY, vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return bool(self.vals & vals)


class QEq(QLeaf):
    def __init__(self, vals):
        super(QEq, self).__init__(QType.EQ, vals=vals)

    def match(self, vals):
        assert isinstance(vals, set)
        return self.vals == vals


class AQVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        ast.NodeVisitor.__init__(self, *args, **kwargs)
        self.query = None

    def visit(self, node):
        print(ast.dump(node))
        return ast.NodeVisitor.visit(self, node)

    def visit_Call(self, node):
        assert isinstance(node, ast.Call)
        assert node.func.id in set(['eq', 'any', 'all'])
        assert all([a.id in Role.__members__ for a in node.args])

        vals = [Role.from_name(a.id) for a in node.args]
        pred = node.func.id
        if pred == 'eq':
            return RoleQuery.eq_(vals)
        elif pred == 'any':
            return RoleQuery.any_(vals)
        elif pred == 'all':
            return RoleQuery.all_(vals)

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
        assert node.id in Role.__members__
        attr = Role.from_name(node.id)
        return QAny(set([attr]))

    def visit_UnaryOp(self, node):
        assert isinstance(node, ast.UnaryOp)

        assert isinstance(node.op, ast.Not)
        operand = self.visit(node.operand)
        return QNot([operand])


class RoleQuery(object):

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

    @staticmethod
    def role(r):
        return RoleQuery.any_([r])

    @staticmethod
    def any_(vals):
        qnode = QAny(set(vals))
        return RoleQuery(qnode)

    @staticmethod
    def all_(vals):
        qnode = QAll(set(vals))
        return RoleQuery(qnode)

    @staticmethod
    def eq_(vals):
        qnode = QEq(set(vals))
        return RoleQuery(qnode)

    def match(self, vals):
        return self.qnode.match(set(vals))

    @staticmethod
    def parse(query):
        tree = ast.parse(query, mode='eval')
        print(ast.dump(tree))
        visitor = AQVisitor()
        return RoleQuery(visitor.visit(tree))

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
