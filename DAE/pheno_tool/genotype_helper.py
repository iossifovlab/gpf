'''
Created on Nov 16, 2016

@author: lubo
'''
from query_variants import dae_query_variants
import itertools
from Variant import variantInMembers
from collections import Counter

DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class PhenoRequest(object):
    """
    Represents query filters for finding family variants.

    Constructor arguments are:

    `effect_types` -- list of effect types

    `rarity` -- one of `ultraRare`, `rare`, `interval`. Together with
    `ratiry_max` and `rarity_min` specifies the rarity of transmitted variants.

    `rarity_max` -- used when *rarity* is `rare` or `interval`. Specifies the
    the upper boundary of the rarity (percents)

    `rarity_min` -- used when *rarity* is `interval`. Specifies the lower
    boundary of rarity (percents)
    """

    def __init__(
        self,
        effect_types=None,
        gene_syms=None,
        rarity='ultraRare',
        rarity_max=None,
        rarity_min=None,
    ):

        self.effect_types = effect_types
        self.probands = None
        self.gene_syms = gene_syms
        self.rarity = rarity
        self.rarity_max = rarity_max
        self.rarity_min = rarity_min

    def _dae_query_request(self):
        data = {
            'geneSyms': self.gene_syms,
            'effectTypes': self.effect_types,
            'rarity': self.rarity,
            'popFrequencyMax': self.rarity_max,
            'popFrequencyMin': self.rarity_min,
        }
        return data


class GenotypeHelper(object):

    def __init__(self, studies, roles=['prb']):
        self.studies = studies

        self.denovo_studies = [st for st in studies if st.has_denovo]
        self.transmitted_studies = [st for st in studies if st.has_transmitted]

        self.roles = roles

    @property
    def present_in_child(self):
        pic = set([])
        if 'prb' in self.roles:
            pic.add('autism only')
            pic.add('autism and unaffected')
        if 'sib' in self.roles:
            pic.add('unaffected only')
            pic.add('autism and unaffected')
        if not pic or 'mom' in self.roles or 'dad' in self.roles:
            pic.add('neither')
        return ','.join(pic)

    @property
    def present_in_parent(self):
        pic = set([])
        if 'mom' in self.roles:
            pic.add('mother only')
            pic.add('mother and father')
        if 'dad' in self.roles:
            pic.add('father only')
            pic.add('mother and father')
        if not pic or 'prb' in self.roles or 'sib' in self.roles:
            pic.add('neither')
        return ','.join(pic)

    def get_variants(self, request):
        query = request._dae_query_request()
        query.update({
            'denovoStudies': self.denovo_studies,
            'transmittedStudies': self.transmitted_studies,
            'presentInChild': self.present_in_child,
            'presentInParent': self.present_in_parent,
        })
        vs = dae_query_variants(query)
        return itertools.chain(*vs)

    def get_persons_variants(self, pheno_request):
        vs = self.get_variants(pheno_request)
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
        vs = self.get_variants(pheno_request)
        seen = set([])
        result = Counter()
        for v in vs:
            vid = "{}:{}:{}".format(v.familyId, v.location, v.variant)
            if vid not in seen:
                seen.add(vid)
                result[v.familyId] += 1
        return result
