'''
Created on Nov 21, 2016

@author: lubo
'''
from query_variants import dae_query_variants
import itertools
from collections import Counter
from Variant import variantInMembers


DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class VariantTypes(object):
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
        present_in_child=None,
        present_in_parent=None,
        rarity='ultraRare',
        rarity_max=None,
        rarity_min=None,
    ):

        self.effect_types = effect_types
        self.gene_syms = gene_syms
        self.present_in_child = present_in_child
        self.present_in_parent = present_in_parent
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
            'presentInChild': self.present_in_child,
            'presentInParent': self.present_in_parent,
        }
        return data


class GenotypeHelper(object):

    def __init__(self, studies):
        self.studies = studies

        self.denovo_studies = [st for st in studies if st.has_denovo]
        self.transmitted_studies = [st for st in studies if st.has_transmitted]

    def get_variants(self, request):
        query = request._dae_query_request()
        query.update({
            'denovoStudies': self.denovo_studies,
            'transmittedStudies': self.transmitted_studies,
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
