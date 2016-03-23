'''
Created on Aug 3, 2015

@author: lubo
'''


class FamiliesDataCSV(object):

    def __init__(self, studies):
        self.studies = studies

    def serialize(self):
        seen = set()
        self.data = []
        self.data.append('study,familyId,personId,role,gender,orderInFamily\n')
        for st in self.studies:
            families = st.families.values()
            families.sort(key=lambda f: f.familyId)
            seen = set()
            for f in families:
                if f.familyId in seen:
                    continue
                seen.add(f.familyId)
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
