'''
Created on Nov 16, 2016

@author: lubo
'''
from query_variants import dae_query_variants
import itertools


class GenotypeHelper(object):

    def __init__(self, studies, roles=['prb']):
        self.studies = studies

        self.denovo_studies = studies[:]
        self.transmitted_studies = [st for st in studies if st.has_transmitted]

        self.roles = roles

    def get_variants(self, request):
        query = request._dae_query_request()
        query['denovoStudies'] = self.studies
        query['transmittedStudies'] = self.transmitted_studies

        vs = dae_query_variants(request._dae_query_request())
        return itertools.chain(*vs)
