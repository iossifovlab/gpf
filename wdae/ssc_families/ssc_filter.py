'''
Created on Jul 7, 2016

@author: lubo
'''
import precompute


class QuadFamiliesFilter(object):

    def __init__(self):
        self.ssc_families_precompute = precompute.register.get(
            'ssc_families_precompute')

    def get_matching_families(self, study_type=None, study_name=None):

        if study_type is not None and study_name is None:
            return self.ssc_families_precompute.quads(study_type)
        elif study_name is not None and study_type is None:
            return self.ssc_families_precompute.quads(study_name)
        else:
            return self.ssc_families_precompute.quads(study_name) & \
                self.ssc_families_precompute.quads(study_type)

    def filter_matching_familes(
            self, families, study_type='all', study_name=None):

        filter_families = self.get_matching_families(study_type, study_name)
        return [f for f in families if f in filter_families]


class FamiliesGenderFilter(object):

    def __init__(self):
        self.ssc_families_precompute = precompute.register.get(
            'ssc_families_precompute')

    def get_matching_probands(self, gender):
        return self.ssc_families_precompute.probands(gender)

    def get_matching_siblings(self, gender):
        return self.ssc_families_precompute.siblings(gender)

    def filter_matching_probands(self, families, gender):
        filter_families = self.get_matching_probands(gender)
        return [f for f in families if f in filter_families]

    def filter_matching_siblings(self, families, gender):
        filter_families = self.get_matching_siblings(gender)
        return [f for f in families if f in filter_families]
