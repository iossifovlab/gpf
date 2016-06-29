'''
Created on Jun 29, 2016

@author: lubo
'''
import preloaded


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

    def __init__(self):
        pass

    def get_matching_probands_by_study(self, study_name):
        pass


class PhenoRaceFilter(object):
    '''
    If ethnicity is selected filter our children whose parents are not
    from the selected ethnicity (parents should be found through the family
    data from the phenotypic database.
    '''
    def __init__(self):
        pass
