'''
Created on Aug 3, 2015

@author: lubo
'''
from __future__ import unicode_literals


from builtins import str
from builtins import object
class FamiliesDataCSV(object):

    def __init__(self, studies):
        self.studies = studies

    def serialize(self):
        self.data = []
        self.data.append('study,familyId,personId,role,gender,orderInFamily\n')
        for st in self.studies:
            families = list(st.families.values())
            families.sort(key=lambda f: f.familyId)
            for f in families:
                for (o, p) in enumerate(f.memberInOrder):
                    row = [
                        st.name,
                        f.familyId,
                        p.personId,
                        p.role,
                        p.gender,
                        str(o)]

                    line = ','.join(row)
                    self.data.append('{}\n'.format(line))
        return self.data
