'''
Created on Feb 13, 2018

@author: lubo
'''
import enum


class Role(enum.Enum):

    prb = 1
    sib = 1 << 2
    child = 1 << 3

    maternal_half_sibling = 1 << 4
    paternal_half_sibling = 1 << 5

    parent = 1 << 6

    mom = 1 << 7
    dad = 1 << 8

    step_mom = 1 << 9
    step_dad = 1 << 10
    spouse = 1 << 11

    maternal_cousin = 1 << 12
    paternal_cousin = 1 << 13

    maternal_uncle = 1 << 14
    maternal_aunt = 1 << 15
    paternal_uncle = 1 << 16
    paternal_aunt = 1 << 17

    maternal_grandmother = 1 << 18
    maternal_grandfather = 1 << 19
    paternal_grandmother = 1 << 20
    paternal_grandfather = 1 << 21

    unknown = 1 << 22

    all = prb | sib | child | maternal_half_sibling | paternal_half_sibling | \
        parent | mom | dad | step_mom | step_dad | spouse | \
        maternal_cousin | paternal_cousin | \
        maternal_uncle | maternal_aunt | paternal_uncle | paternal_aunt | \
        maternal_grandfather | maternal_grandmother | \
        paternal_grandfather | paternal_grandmother | \
        unknown

    @staticmethod
    def from_name(name):
        if name in Role.__members__:
            return Role[name]
        else:
            return Role.unknown


class RoleQuery(object):

    def __init__(self, role=None):
        self.value = 0
        if role:
            self.value = role.value

    def and_(self, role):
        self.value &= role.value
        return self

    def and_not_(self, role):
        self.value &= (~role.value & Role.all.value)
        return self

    def or_(self, role):
        self.value |= role.value
        return self

    def or_not_(self, role):
        self.value |= (~role.value & Role.all.value)
        return self

    def complement(self):
        self.value = (~self.value & Role.all.value)
        return self

    @classmethod
    def from_list(cls, roles):
        rqs = map(RoleQuery, roles)
        return reduce(lambda r1, r2: r1.or_(r2), rqs)

    def match(self, role):
        return bool(self.value & role.value)
