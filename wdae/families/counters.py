'''
Created on Mar 23, 2016

@author: lubo
'''


class FamilyFilterCounters(object):

    def __init__(self, families_buffer):
        self.families_buffer = families_buffer

    def count(self, family_ids):
        prb_counter = {"M": 0, "F": 0}
        sib_counter = {"M": 0, "F": 0}
        families_counter = {'prb': set(), 'sib': set()}

        family_ids = set(family_ids)
        for fid, family in self.families_buffer.items():
            if fid not in family_ids:
                continue
            for person in family.values():
                families_counter[person.role].add(fid)
                if person.role == 'sib':
                    sib_counter[person.gender] += 1
                elif person.role == 'prb':
                    prb_counter[person.gender] += 1

        result = {'autism': {'male': prb_counter['M'],
                             'female': prb_counter['F'],
                             'families': len(families_counter['prb'])},
                  'unaffected': {'male': sib_counter['M'],
                                 'female': sib_counter['F'],
                                 'families': len(families_counter['sib'])}, }
        return result
