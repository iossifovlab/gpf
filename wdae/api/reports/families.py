'''
Created on Aug 3, 2015

@author: lubo
'''


def sfun(f):
    return f.familyId


class FamiliesData(object):
    def __init__(self, studies):
        self.studies = studies

    def build(self):
        seen = set()
        self.data = []
        for st in self.studies:
            families = st.families.values()
            families.sort(key=sfun)
            for f in families:
                if f.familyId in seen:
                    continue
                seen.add(f.familyId)
                for (o, p) in enumerate(f.memberInOrder):
                    row = [f.familyId, p.personId, p.role, p.gender, str(o)]
                    line = ','.join(row)
                    self.data.append('{}\n'.format(line))
        return self.data
