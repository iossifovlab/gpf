'''
Created on Jun 29, 2016

@author: lubo
'''
import preloaded
from api.default_ssc_study import get_ssc_denovo_studies, get_ssc_denovo
from DAE import vDB


class PhenoMeasureFilters(object):

    def __init__(self):
        register = preloaded.register.get_register()
        assert register.has_key('pheno_measures')  # @IgnorePep8

        self.measures = register.get('pheno_measures')

    def get_matching_probands(self, pheno_measure, mmin=None, mmax=None):
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

    def get_matching_siblings(self, pheno_measure, mmin=None, mmax=None):
        '''
        (At the moment the sibling list should always be empty.)
        '''
        return set([])


class PhenoStudyFilter(object):
    '''
    If a study or study type is selected filter out the probands and siblings
    that are not included in any of the studies.
    '''

    STUDY_TYPES = set(['all', 'we', 'tg', 'cnv'])
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

    def _build_study_types(self):
        stypes = set()
        for st in self.STUDIES:
            stypes.add(st.get_attr('study.type'))
        self._study_types = list(stypes)
        self._study_types.sort()
        return self._study_types


class PhenoRaceFilter(object):
    '''
    If ethnicity is selected filter our children whose parents are not
    from the selected ethnicity (parents should be found through the family
    data from the phenotypic database.
    '''

    def __init__(self):
        pass
