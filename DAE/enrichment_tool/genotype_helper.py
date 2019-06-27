'''
Created on Apr 24, 2017

@author: lubo
'''
from __future__ import print_function, absolute_import
from __future__ import unicode_literals
from builtins import object

from collections import Counter

from variants.attributes import Inheritance, Role


class GenotypeHelper(object):

    def __init__(
            self, dataset, people_group, people_group_value,
            study_types=['WE', 'WG']):
        self.dataset = dataset
        self.people_group = people_group
        self.people_group_value = people_group_value
        self.study_types = study_types
        self._children_stats = None

    def get_variants(self, effect_types):
        people_with_people_group = self.dataset.get_people_with_people_group(
            self.people_group.source, self.people_group_value)

        # TODO: Remove this when study.query_variants can support non
        # expand_effect_types as LGDs
        from studies.helpers import expand_effect_types
        effect_types = expand_effect_types(effect_types)

        variants = self.dataset.query_variants(
            inheritance=str(Inheritance.denovo.name),
            person_ids=people_with_people_group,
            effect_types=set(effect_types),
            studyTypes=['WE', 'WG']
        )

        return list(variants)

    def get_children_stats(self):
        if self._children_stats is not None:
            return self._children_stats
        seen = set()
        counter = Counter()

        for fid, fam in list(self.dataset.families.items()):
            for p in fam.get_people_with_roles([Role.prb, Role.sib]):
                iid = "{}:{}".format(fid, p.person_id)
                if iid in seen:
                    continue

                if p.atts[self.people_group.source] != self.people_group_value:
                    continue

                counter[p.sex.name] += 1
                seen.add(iid)
        self._children_stats = counter

        return self._children_stats
