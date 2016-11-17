'''
Created on Nov 16, 2016

@author: lubo
'''
from query_variants import dae_query_variants, dae_query_families_with_variants
import itertools
from Variant import variantInMembers
from collections import Counter


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

    def get_persons_variants(self, request):
        vs = self.get_variants(request)
        seen = set([])
        result = Counter()
        for v in vs:
            persons = variantInMembers(v)
            for p in persons:
                vid = "{}:{}:{}".format(p, v.location, v.variant)
                if vid not in seen:
                    seen.add(vid)
                    result[p] += 1
                else:
                    print("skipping {}".format(vid))
        return result

    def get_families_variants(self, pheno_request):
        data = pheno_request._dae_query_request()
        data['inChild'] = 'prb'

        fams = dae_query_families_with_variants(data)
        result = Counter(fams)

        return result
