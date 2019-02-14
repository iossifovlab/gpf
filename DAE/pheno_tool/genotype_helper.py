'''
Created on Nov 21, 2016

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
# from query_variants import dae_query_variants, PRESENT_IN_CHILD_TYPES,\
#     PRESENT_IN_PARENT_TYPES
import itertools
import pandas as pd
from collections import Counter
from Variant import variantInMembers
from VariantAnnotation import get_effect_types
# from query_prepare import build_effect_types_list
import logging

LOGGER = logging.getLogger(__name__)

DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class VariantsType(object):
    """
    Represents query filters for finding family variants.

    Constructor arguments are:

    `effect_types` -- list of effect types

    `gene_syms` -- list of gene symbols

    `present_in_child` -- list of present in child specifiers ("affected only",
    "unaffected only", "affected and unaffected", "proband only",
    "sibling only", "proband and sibling", "neither").

    `present_in_parent` -- list of present in parent specifiers ("mother only",
    "father only", "mother and father", "neither")

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
        present_in_child=['affected only', 'affected and unaffected'],
        present_in_parent=['neither'],
        rarity='ultraRare',
        rarity_max=None,
        rarity_min=None,
        family_ids=None,
    ):
        assert self._check_present_in_child(present_in_child)
        assert self._check_present_in_parent(present_in_parent)
        assert self._check_effect_types(effect_types)
        assert self._check_rarity(rarity, rarity_min, rarity_max)

        self.effect_types = effect_types
        self.gene_syms = gene_syms
        self.present_in_child = present_in_child
        self.present_in_parent = present_in_parent
        self.rarity = rarity
        self.rarity_max = rarity_max
        self.rarity_min = rarity_min
        self.family_ids = family_ids

    def _dae_query_request(self):
        data = {
            'geneSyms': self.gene_syms,
            'effectTypes': self.effect_types,
            'rarity': self.rarity,
            'maxAltFreqPrcnt': self.rarity_max,
            'minAltFreqPrcnt': self.rarity_min,
            'presentInChild': self.present_in_child,
            'presentInParent': self.present_in_parent,
            'familyIds': self.family_ids,
        }
        return data

    @staticmethod
    def _check_present_in_child(present_in_child):
        assert isinstance(present_in_child, list)

        return all([pic in PRESENT_IN_CHILD_TYPES
                    for pic in present_in_child])

    @staticmethod
    def _check_present_in_parent(present_in_parent):
        assert isinstance(present_in_parent, list)

        return all([pip in PRESENT_IN_PARENT_TYPES
                    for pip in present_in_parent])

    @staticmethod
    def _check_effect_types(effect_types):
        assert isinstance(effect_types, list)

        elist = build_effect_types_list(effect_types)
        return all([et in get_effect_types(types=True, groups=True)
                    for et in elist])

    @staticmethod
    def _check_rarity(rarity, rarity_min, rarity_max):
        assert rarity in ['ultraRare', 'rare', 'interval', 'all']

        if rarity == 'ultraRare':
            assert rarity_min is None and rarity_max is None
        if rarity == 'rare':
            assert rarity_min is None and \
                (rarity_max >= 0.0 and rarity_max <= 100.0)
        if rarity == 'interval':
            assert (rarity_min >= 0.0 and rarity_min <= 100.0) and \
                (rarity_max >= 0.0 and rarity_max <= 100.0) and \
                rarity_min <= rarity_max
        if rarity == 'all':
            assert rarity_min is None and rarity_max is None
        return True


class GenotypeHelper(object):

    def __init__(self, studies):
        self.studies = studies

        self.denovo_studies = [st for st in studies if st.has_denovo]
        self.transmitted_studies = [st for st in studies if st.has_transmitted]

    def get_variants(self, variants_type):
        assert isinstance(variants_type, VariantsType)

        query = variants_type._dae_query_request()
        query.update({
            'denovoStudies': self.denovo_studies,
            'transmittedStudies': self.transmitted_studies,
        })
        vs = dae_query_variants(query)
        return itertools.chain(*vs)

    def get_persons_variants(self, variants_type):
        vs = self.get_variants(variants_type)
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
                    LOGGER.info("skipping {}".format(vid))
        return result

    def get_persons_variants_df(self, variants_type):
        vs = self.get_persons_variants(variants_type)
        df = pd.DataFrame(
            data=[(k, v) for (k, v) in list(vs.items())],
            columns=['person_id', 'variants'])
        df.set_index('person_id', inplace=True, verify_integrity=True)
        return df

    def get_families_variants(self, variants_type):
        vs = self.get_variants(variants_type)
        seen = set([])
        result = Counter()
        for v in vs:
            vid = "{}:{}:{}".format(v.familyId, v.location, v.variant)
            if vid not in seen:
                seen.add(vid)
                result[v.familyId] += 1
        return result
