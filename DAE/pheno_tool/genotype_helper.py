'''
Created on Nov 16, 2016

@author: lubo
'''
from query_variants import dae_query_variants, dae_query_families_with_variants
import itertools
from Variant import variantInMembers
from collections import Counter

DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class PhenoRequest(object):
    """
    Represents query filters for finding family variants.

    Constructor arguments are:

    `effect_type_groups` -- list of effect type groups

    `in_child` -- one of *prb* or *sib*

    `study` -- study of group of studies to search
    (defaults to 'ALL SSC')

    `transmitted` -- transmitted study to search for variants

    `present_in_parent` -- a comma separted combination of `father only`,
    `mother only`, `father and mother`, `neither`. Specifies what kind of
    transmitted variants to find.

    `rarity` -- one of `ultraRare`, `rare`, `interval`. Together with
    `ratiry_max` and `rarity_min` specifies the rarity of transmitted variants.

    `rarity_max` -- used when *rarity* is `rare` or `interval`. Specifies the
    the upper boundary of the rarity (percents)

    `rarity_min` -- used when *rarity* is `interval`. Specifies the lower
    boundary of rarity (percents)
    """

    def __init__(
        self,
        effect_type_groups=['LGDs'],
        gene_syms=None,
        in_child='prb',
        present_in_parent='neither',
        rarity='ultraRare',
        rarity_max=None,
        rarity_min=None,
        study=DEFAULT_STUDY,
        transmitted=DEFAULT_TRANSMITTED
    ):

        self.study = study
        self.transmitted = transmitted
        self.effect_type_groups = effect_type_groups
        self.in_child = in_child
        self.present_in_parent = present_in_parent
        self.probands = None
        self.gene_syms = gene_syms
        self.rarity = rarity
        self.rarity_max = rarity_max
        self.rarity_min = rarity_min

    def _dae_query_request(self):
        data = {
            'denovoStudies': self.study,
            'transmittedStudies': self.transmitted,
            'inChild': self.in_child,
            'effectTypes': self.effect_type_groups,
            'presentInParent': self.present_in_parent,
            'rarity': self.rarity,
            'popFrequencyMax': self.rarity_max,
            'popFrequencyMin': self.rarity_min,
        }
        if self.gene_syms:
            data['geneSyms'] = self.gene_syms

        return data


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
