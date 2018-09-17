from __future__ import unicode_literals

from builtins import object
class Family(object):

    def __init__(self, atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {}
        self.memberInOrder = []

    def __repr__(self):
        return "Family({}: {})".format(self.familyId, self.memberInOrder)

    @property
    def children_in_order(self):
        return [p for p in self.memberInOrder if p.is_child]


class Person(object):

    def __init__(self, atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {}

    def __repr__(self):
        return "Person({}; {}; {})".format(
            self.personId, self.role, self.gender)

    @property
    def layout_position(self):
        return self.atts.get("layoutCoords", None)

    @property
    def is_child(self):
        return self.role == Role.prb or self.role == Role.sib
