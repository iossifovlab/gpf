
class Family:

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


class Person:

    def __init__(self, atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {}

    def __repr__(self):
        return "Person({}; {}; {})".format(
            self.personId, self.role, self.gender)

    @property
    def is_child(self):
        return self.role == 'prb' or self.role == 'sib'

    @property
    def is_parent(self):
        return not self.is_parent
