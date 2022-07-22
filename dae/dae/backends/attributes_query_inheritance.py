import operator
import functools

from lark import Lark, Transformer
from dae.variants.attributes import Inheritance


INHERITANCE_QUERY_GRAMMAR = r"""

    reference: "reference"
    mendelian: "mendelian"
    denovo: "denovo"
    possible_denovo: "possible_denovo"
    omission: "omission"
    possible_omission: "possible_omission"
    other: "other"
    missing: "missing"
    unknown: "unknown"

    ?primitive: reference
        | mendelian
        | denovo
        | possible_denovo
        | omission
        | possible_omission
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


inheritance_parser = Lark(INHERITANCE_QUERY_GRAMMAR, start="expression")


class Primitive:
    def __init__(self, value):
        self.value = value


class NegPrimitive:
    def __init__(self, value):
        self.value = value


class Expression:
    def __init__(self, expression):
        self.expression = expression

    def __str__(self):
        return self.expression


class InheritanceTransformer(Transformer):
    def __init__(self, attr_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr_name = attr_name
        self.inheritance_mask = 16383

    def denovo(self, items):
        return Primitive(Inheritance.denovo.value)

    def possible_denovo(self, items):
        return Primitive(Inheritance.possible_denovo.value)

    def possible_omission(self, items):
        return Primitive(Inheritance.possible_omission.value)

    def reference(self, items):
        return Primitive(Inheritance.reference.value)

    def mendelian(self, items):
        return Primitive(Inheritance.mendelian.value)

    def omission(self, items):
        return Primitive(Inheritance.omission.value)

    def other(self, items):
        return Primitive(Inheritance.other.value)

    def missing(self, items):
        return Primitive(Inheritance.missing.value)

    def unknown(self, items):
        return Primitive(Inheritance.unknown.value)

    def primitive(self, items):
        assert len(items) == 1
        return Primitive(Inheritance.from_name(items[0]).value)

    def negative_primitive(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Primitive)

        return NegPrimitive(items[0].value)

    def atom(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Primitive) or \
            isinstance(items[0], NegPrimitive)
        return items[0]

    def atomlist(self, items):
        atom_values = [atom.value for atom in items]
        mask = functools.reduce(operator.or_, atom_values, 0)
        return Primitive(mask)

    def all(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Primitive)
        mask = items[0].value
        return Expression(
            f"BITAND({mask}, {self.attr_name}) = {mask}")

    def any(self, items):
        assert len(items) == 1
        assert isinstance(items[0], Primitive)
        mask = items[0].value
        return Expression(
            f"BITAND({mask}, {self.attr_name}) != 0")

    def _process_list(self, items):
        expressions = []
        for atom in items:
            if isinstance(atom, Primitive):
                expressions.append(
                    f"BITAND({atom.value}, {self.attr_name}) != 0")
            elif isinstance(atom, NegPrimitive):
                expressions.append(
                    f"BITAND({atom.value}, {self.attr_name}) = 0")
            elif isinstance(atom, Expression):
                expressions.append(atom)
            else:
                raise ValueError(f"unexpected expression {atom}")
        return expressions

    def logical_or(self, items):
        expressions = self._process_list(items)
        return Expression(" OR ".join(expressions))

    def logical_and(self, items):
        expressions = self._process_list(items)
        return Expression(" AND ".join(expressions))

    def expression(self, items):
        if len(items) == 1 and isinstance(items[0], Primitive):
            mask = items[0].value
            return Expression(f"BITAND({mask}, {self.attr_name}) != 0")
        if len(items) == 1 and isinstance(items[0], NegPrimitive):
            mask = items[0].value
            return Expression(f"BITAND({mask}, {self.attr_name}) = 0")
        if len(items) == 1 and isinstance(items[0], Expression):
            return items[0].expression

        raise NotImplementedError()
