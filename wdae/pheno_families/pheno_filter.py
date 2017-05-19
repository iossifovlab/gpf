'''
Created on Jun 29, 2016

@author: lubo
'''
import preloaded
from helpers.default_ssc_study import get_ssc_denovo_studies, get_ssc_denovo
from DAE import vDB
import precompute


class PhenoMeasureFilters(object):

    def __init__(self):
        register = preloaded.register
        assert register.has_key('pheno_measures')  # @IgnorePep8

        self.measures = register.get('pheno_measures')

    def get_matching_probands(self, pheno_measure,
                              mmin=None, mmax=None):
        '''
        List the probands that have the specified property and separately the
        siblings that have the selected property.
        (At the moment the sibling list should always be empty.)

        If a phenotypic property is selected, filter our the children
        that don't have that property and the ones that have that property
        but it's value is outside of the selected interval.
        '''
        return set(self.measures.get_measure_probands(
            pheno_measure, mmin, mmax))

    def get_matching_siblings(self, pheno_measure,
                              mmin=None, mmax=None):
        '''
        (At the moment the sibling list should always be empty.)
        '''
        return set([])

    def filter_matching_probands(self, probands,
                                 pheno_measure,
                                 mmin=None, mmax=None):
        filter_probands = self.get_matching_probands(
            pheno_measure, mmin, mmax)
        return [p for p in probands if p in filter_probands]

    def get_matching_families(self, pheno_measure,
                              mmin=None, mmax=None):
        '''
        List the families that have the specified property

        If a phenotypic property is selected, filter our the families
        that don't have that property and the ones that have that property
        but it's value is outside of the selected interval.
        '''
        return set([str(f) for f in self.measures.get_measure_families(
            pheno_measure, mmin, mmax)])

    def filter_matching_families(self, families,
                                 pheno_measure,
                                 mmin=None, mmax=None):
        filter_families = self.get_matching_families(
            pheno_measure, mmin, mmax)
        if families:
            return [f for f in families if f in filter_families]
        else:
            return filter_families


class StudyFilter(object):
    '''
    If a study or study type is selected filter out the probands and siblings
    that are not included in any of the studies.
    '''

    STUDY_TYPES = set(['we', 'tg', 'cnv'])
    STUDIES = get_ssc_denovo_studies()
    STUDY_NAMES = set(get_ssc_denovo().split(','))

    def __init__(self):
        pass

    def get_matching_probands_by_study(self, study_name):
        assert study_name in self.STUDY_NAMES
        probands = set([])
        study = vDB.get_study(study_name)
        for _fid, fam in study.families.items():
            for p in fam.memberInOrder:
                if p.role == 'prb':
                    probands.add(p.personId)
        return probands

    def get_matching_probands_by_study_type(self, study_type):
        assert study_type.lower() in self.STUDY_TYPES
        probands = set([])
        for st in self.STUDIES:
            if st.get_attr('study.type').lower() != study_type.lower():
                continue
            for _fid, fam in st.families.items():
                for p in fam.memberInOrder:
                    if p.role == 'prb':
                        probands.add(p.personId)
        return probands

    def filter_matching_probands_by_study(self, probands, study_name):
        filter_probands = self.get_matching_probands_by_study(study_name)
        return [p for p in probands if p in filter_probands]

    def filter_matching_probands_by_study_type(self, probands, study_type):
        filter_probands = self.get_matching_probands_by_study_type(study_type)
        return [p for p in probands if p in filter_probands]

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
        if families:
            return [f for f in families if f in filter_families]
        else:
            return filter_families

    def filter_matching_families_by_study_type(self, families, study_type):
        filter_families = self.get_matching_families_by_study_type(study_type)
        if families:
            return [f for f in families if f in filter_families]
        else:
            return filter_families


class FamilyFilter(object):

    def __init__(self):
        pass

    @staticmethod
    def strip_proband_id(proband_id):
        return proband_id.split('.')[0]

    @staticmethod
    def filter_probands_by_family_ids(family_ids, probands):
        return [p for p in probands
                if FamilyFilter.strip_proband_id(p) in family_ids]

    @staticmethod
    def probands_to_families(probands):
        return [FamilyFilter.strip_proband_id(p) for p in probands]


class RaceFilter(FamilyFilter):
    '''
    If ethnicity is selected filter our children whose parents are not
    from the selected ethnicity (parents should be found through the family
    data from the phenotypic database.
    '''

    def __init__(self):
        self.families_precompute = precompute.register.get(
            'pheno_families_precompute')

    @staticmethod
    def get_races():
        return set(['african-amer',
                    'asian',
                    'more-than-one-race',
                    'native-american',
                    'native-hawaiian',
                    'white',
                    'other',
                    'not-specified'])

    def get_matching_families_by_race(self, race):
        family_ids = set(self.families_precompute.race(race))
        return family_ids

    def filter_matching_probands_by_race(self, race, probands):
        filter_familys = self.get_matching_families_by_race(race)
        return self.filter_probands_by_family_ids(filter_familys, probands)

    def filter_matching_families_by_race(self, race, families):
        filter_families = self.get_matching_families_by_race(race)
        if families:
            return [f for f in families if f in filter_families]
        else:
            return filter_families
