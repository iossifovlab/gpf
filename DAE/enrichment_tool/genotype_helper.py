'''
Created on Apr 24, 2017

@author: lubo
'''
import itertools
from collections import Counter


class GenotypeHelper(object):

    @staticmethod
    def from_studies(denovo_studies, in_child):
        return StudiesGenotypeHelper(denovo_studies, in_child)

    @staticmethod
    def from_dataset(dataset, grouping, grouping_selector):
        return DatasetGenotypeHelper(dataset, grouping, grouping_selector)

    def get_variants(self):
        raise NotImplemented


class StudiesGenotypeHelper(GenotypeHelper):

    def __init__(self, denovo_studies, in_child):
        super(StudiesGenotypeHelper, self).__init__()
        self.denovo_studies = denovo_studies
        self.in_child = in_child

    def get_variants(self, effect_types):
        variants = []
        for st in self.denovo_studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child, effectTypes=effect_types)
            variants.append(vs)
        return list(itertools.chain(*variants))

    def get_children_stats(self):
        seen = set()
        counter = Counter()
        for st in self.denovo_studies:
            for fid, fam in st.families.items():
                for p in fam.memberInOrder[2:]:
                    iid = "{}:{}".format(fid, p.personId)
                    if iid in seen:
                        continue
                    if p.role != self.in_child:
                        continue

                    counter[p.gender] += 1
                    seen.add(iid)
        return counter


class DatasetGenotypeHelper(GenotypeHelper):

    def __init__(self, dataset, person_grouping, person_grouping_selector):
        self.dataset = dataset
        self.person_grouping_id = person_grouping
        self.person_grouping_selector = person_grouping_selector
        self.person_grouping = self.dataset.get_pedigree_selector(
            person_grouping=person_grouping)
        print(self.person_grouping)
        assert self.person_grouping['id'] == self.person_grouping_id

    def get_variants(self, effect_types):
        variants = self.dataset.get_variants(
            person_grouping=self.person_grouping_id,
            person_grouping_selector=[self.person_grouping_selector],
            effect_types=effect_types)
        return list(variants)

    def get_children_stats(self):
        raise NotImplementedError()
