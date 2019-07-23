import operator
import functools

from lark import Lark, Transformer
from variants.attributes import Inheritance


INHERITANCE_QUERY_GRAMMAR = r"""

    reference: "reference"
    mendelian: "mendelian"
    denovo: "denovo"
    possible_denovo: "possible_denovo"
    omission: "omission"
    other: "other"
    missing: "missing"
    unknown: "unknown"

    ?primitive: reference
        | mendelian
        | denovo
        | possible_denovo
        | omission
        | other
        | missing
        | unknown

    negative_primitive: "not" primitive

    atom: primitive
        | negative_primitive

    atomlist: (atom "," )* atom [","]
    all: "all"i "(" atomlist ")"
    any: "any"i "(" atomlist ")"


    logical_or: atom ("or" atom)+
    logical_and: atom ("and" atom)+

    expression: atom
        | all
        | any
        | logical_or
        | logical_and

    %import common.WS
    %ignore WS
"""


inheritance_parser = Lark(
    INHERITANCE_QUERY_GRAMMAR,
    start='expression')


class Atom:
    def __init__(self, value):
        self.value = value

class Expression:
    def __init__(self, expression):
        self.expression = expression

    def __str__(self):
        return self.expression


class InheritanceTransformer(Transformer):

    def __init__(self, attr_name, *args, **kwargs):
        super(InheritanceTransformer, self).__init__(*args, **kwargs)
        self.attr_name = attr_name

    def denovo(self, items):
        return Inheritance.denovo.value

    def possible_denovo(self, items):
        return Inheritance.possible_denovo.value

    def reference(self, items):
        return Inheritance.reference.value

    def mendelian(self, items):
        return Inheritance.mendelian.value

    def omission(self, items):
        return Inheritance.omission.value

    def other(self, items):
        return Inheritance.other.value

    def missing(self, items):
        return Inheritance.missing.value

    def unknown(self, items):
        return Inheritance.unknown.value

    def primitive(self, items):
        assert len(items) == 1
        return Inheritance.from_name(items[0]).value

    def negative_primitive(self, items):
        assert len(items) == 1
        return operator.invert(items[0])

    def atom(self, items):
        assert len(items) == 1
        return Atom(items[0])

    def atomlist(self, items):
        atom_values = [atom.value for atom in items]
        mask = functools.reduce(operator.or_, atom_values, 0)
        return Atom(mask)

    def all(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Atom)
        mask = items[0].value
        return Expression(
            "BITAND({mask}, {attr}) = {mask}".format(
                mask=mask, attr=self.attr_name))

    def any(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Atom)
        mask = items[0].value
        return Expression(
            "BITAND({mask}, {attr}) != 0".format(
                mask=mask, attr=self.attr_name))

    def logical_or(self, items):
        return self.any([self.atomlist(items)])

    def logical_and(self, items):
        return self.all([self.atomlist(items)])

    def expression(self, items):
        if len(items) == 1 and isinstance(items[0], Atom):
            return self.any(items)
        if len(items) == 1 and isinstance(items[0], Expression):
            return items[0].expression

        raise NotImplementedError()
