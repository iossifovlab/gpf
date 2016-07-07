'''
Created on Jul 7, 2016

@author: lubo
'''
import preloaded


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
