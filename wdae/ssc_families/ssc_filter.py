'''
Created on Jul 7, 2016

@author: lubo
'''
import preloaded
from api.default_ssc_study import get_ssc_denovo_studies, get_ssc_denovo
from DAE import vDB
import precompute


class PhenoMeasureFilters(object):

    def __init__(self):
        register = preloaded.register.get_register()
        assert register.has_key('pheno_measures')  # @IgnorePep8

        self.measures = register.get('pheno_measures')

    def get_matching_families(self, pheno_measure, mmin=None, mmax=None):
        '''
        List the families that have the specified property

        If a phenotypic property is selected, filter our the families
        that don't have that property and the ones that have that property
        but it's value is outside of the selected interval.
        '''
        return set(self.measures.get_measure_families(
            pheno_measure, mmin, mmax))

    def filter_matching_families(self, families, pheno_measure,
                                 mmin=None, mmax=None):
        filter_families = self.get_matching_families(pheno_measure, mmin, mmax)
        return [f for f in families if f in filter_families]


class SSCStudyFilter(object):
    '''
    If a study or study type is selected filter out the probands and siblings
    that are not included in any of the studies.
    '''

    STUDY_TYPES = set(['we', 'tg', 'cnv'])
    STUDIES = get_ssc_denovo_studies()
    STUDY_NAMES = set(get_ssc_denovo().split(','))

    def __init__(self):
        pass

    def get_matching_families_by_study(self, study_name):
        assert study_name in self.STUDY_NAMES
        study = vDB.get_study(study_name)
        return set(study.families.keys())

    def get_matching_families_by_study_type(self, study_type):
        assert study_type.lower() in self.STUDY_TYPES
        families = set([])
        for st in self.STUDIES:
            if st.get_attr('study.type').lower() != study_type.lower():
                continue
            families = families | set(st.families.keys())
        return families

    def filter_matching_families_by_study(self, families, study_name):
        filter_families = self.get_matching_families_by_study(study_name)
        return [f for f in families if f in filter_families]

    def filter_matching_families_by_study_type(self, families, study_type):
        filter_families = self.get_matching_families_by_study_type(study_type)
        return [f for f in families if f in filter_families]


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


class SSCFamiliesGenderFilter(object):

    def __init__(self):
        self.ssc_families_precompute = precompute.register.get(
            'ssc_families_precompute')

    def filter_matching_probands(self, families, gender):
        filter_families = self.ssc_families_precompute.probands(gender)
        return [f for f in families if f in filter_families]

    def filter_matching_siblings(self, families, gender):
        filter_families = self.ssc_families_precompute.siblings(gender)
        return [f for f in families if f in filter_families]
