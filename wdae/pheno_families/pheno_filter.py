'''
Created on Jun 29, 2016

@author: lubo
'''
import preloaded


class PhenoFilters(object):

    def __init__(self):
        register = preloaded.register.get_register()
        assert register.has_key('pheno_measures')  # @IgnorePep8

        self.measures = register.get('pheno_measures')

    def get_matching_probands(self, pheno_measure, mmin=None, mmax=None):
        '''
        List the probands that have the specified property and separately the
        siblings that have the selected property.
        (At the moment the sibling list should always be empty.)
        '''
        return self.measures.get_measure_probands(pheno_measure, mmin, mmax)
