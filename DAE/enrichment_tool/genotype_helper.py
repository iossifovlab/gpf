'''
Created on Apr 24, 2017

@author: lubo
'''
from __future__ import print_function, absolute_import
from __future__ import unicode_literals

from builtins import object
from collections import Counter


class GenotypeHelper(object):

    @staticmethod
    def from_studies(denovo_studies, in_child):
        return StudiesGenotypeHelper(denovo_studies, in_child)

    @staticmethod
    def from_dataset(dataset, grouping, grouping_selector):
        return DatasetGenotypeHelper(dataset, grouping, grouping_selector)

    def get_variants(self):
        raise NotImplementedError


class StudiesGenotypeHelper(GenotypeHelper):

    def __init__(self, denovo_studies, in_child):
        super(StudiesGenotypeHelper, self).__init__()
        self.denovo_studies = denovo_studies
        self.in_child = in_child
        self._children_stats = None

    def _get_variants(self, effect_types):
        seen_vs = set()
        for st in self.denovo_studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child.name, effectTypes=effect_types)
            for v in vs:
                v_key = v.familyId + v.location + v.variant
                if v_key in seen_vs:
                    continue
                yield v
                seen_vs.add(v_key)

    def get_variants(self, effect_types):
        return list(self._get_variants(effect_types))

    def get_children_stats(self):
        if self._children_stats is not None:
            return self._children_stats
        seen = set()
        counter = Counter()
        for st in self.denovo_studies:
            for fid, fam in list(st.families.items()):
                for p in fam.children_in_order:
                    iid = "{}:{}".format(fid, p.personId)
                    if iid in seen:
                        continue
                    if p.role != self.in_child:
                        continue

                    counter[p.gender.name] += 1
                    seen.add(iid)
        self._children_stats = counter
        return self._children_stats


class DatasetGenotypeHelper(GenotypeHelper):

    def __init__(
            self, dataset, person_grouping,
            person_grouping_selector,
            study_types=['WE', 'WG']):

        self.dataset = dataset
        self.person_grouping_id = person_grouping
        self.person_grouping_selector = person_grouping_selector
        self.person_grouping = self.dataset.get_people_group(
            person_grouping=person_grouping)
        assert self.person_grouping['id'] == self.person_grouping_id
        self.study_types = study_types
        self._children_stats = None

    def get_variants(self, effect_types):
        variants = self.dataset.get_denovo_variants(
            person_grouping=self.person_grouping_id,
            person_grouping_selector=[self.person_grouping_selector],
            effectTypes=effect_types,
            studyTypes=['WE', 'WG'])
        return list(variants)

    def get_children_stats(self):
        if self._children_stats is not None:
            return self._children_stats
        seen = set()
        counter = Counter()
        enrichment_studies = self.dataset.get_denovo_studies(
            studyTypes=self.study_types)
        for st in enrichment_studies:
            for fid, fam in list(st.families.items()):
                for p in fam.children_in_order:
                    iid = "{}:{}".format(fid, p.personId)
                    if iid in seen:
                        continue

                    if p.atts[self.person_grouping_id] != \
                            self.person_grouping_selector:
                        continue

                    counter[p.gender.name] += 1
                    seen.add(iid)
        self._children_stats = counter
        return self._children_stats
