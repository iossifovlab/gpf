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
    def from_dataset(dataset, grouping_selector, effect_types):
        pass

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

    def __init__(self, dataset, grouping_selector, effect_types):
        self.dataset = dataset
        self.grouping_selector = grouping_selector
        self.effect_types = effect_types

    def get_variants(self):
        raise NotImplemented()
