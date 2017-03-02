'''
Created on Feb 6, 2017

@author: lubo
'''
import itertools
from gene.weights import Weights
import re
# from gene.gene_set_collections import GeneSetsCollections


class EffectTypesMixin(object):
    EFFECT_TYPES = [
        "3'UTR",
        "3'UTR-intron",
        "5'UTR",
        "5'UTR-intron",
        'frame-shift',
        'intergenic',
        'intron',
        'missense',
        'no-frame-shift',
        'no-frame-shift-newStop',
        'noEnd',
        'noStart',
        'non-coding',
        'non-coding-intron',
        'nonsense',
        'splice-site',
        'synonymous',
        'CDS',
        'CNV+',
        'CNV-',
    ]

    EFFECT_TYPES_MAPPING = {
        "Nonsense": ["nonsense"],
        "Frame-shift": ["frame-shift"],
        "Splice-site": ["splice-site"],
        "Missense": ["missense"],
        "Non-frame-shift": ["no-frame-shift"],
        "noStart": ["noStart"],
        "noEnd": ["noEnd"],
        "Synonymous": ["synonymous"],
        "Non coding": ["non-coding"],
        "Intron": ["intron"],
        "Intergenic": ["intergenic"],
        "3'-UTR": ["3'UTR", "3'UTR-intron"],
        "5'-UTR": ["5'UTR", "5'UTR-intron"],
        "CNV": ["CNV+", "CNV-"],
        "CNV+": ["CNV+"],
        "CNV-": ["CNV-"],
    }

    EFFECT_GROUPS = {
        "coding": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "Non-frame-shift",
            "noStart",
            "noEnd",
            "Synonymous",
        ],
        "noncoding": [
            "Non coding",
            "Intron",
            "Intergenic",
            "3'-UTR",
            "5'-UTR",
        ],
        "cnv": [
            "CNV+",
            "CNV-"
        ],
        "lgds": [
            "Frame-shift",
            "Nonsense",
            "Splice-site",
        ],
        "nonsynonymous": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "Non-frame-shift",
            "noStart",
            "noEnd",
        ],
        "utrs": [
            "3'-UTR",
            "5'-UTR",
        ]
    }

    def _build_effect_types_groups(self, effect_types):
        etl = [
            self.EFFECT_GROUPS[
                et.lower()] if et.lower() in self.EFFECT_GROUPS else [et]
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    def _build_effect_types_list(self, effect_types):
        etl = [
            self.EFFECT_TYPES_MAPPING[et]
            if et in self.EFFECT_TYPES_MAPPING else [et]
            for et in effect_types]
        return list(itertools.chain.from_iterable(etl))

    def _build_(self):
        pass

    def build_effect_types(self, effect_types, safe=True):
        if isinstance(effect_types, str) or \
                isinstance(effect_types, unicode):
            effect_types = effect_types.replace(',', ' ')
            effect_types = effect_types.split()
        etl = [et.strip() for et in effect_types]
        etl = self._build_effect_types_groups(etl)
        etl = self._build_effect_types_list(etl)
        if safe:
            assert all([et in self.EFFECT_TYPES for et in etl])
        else:
            etl = [et for et in etl if et in self.EFFECT_TYPES]
        return etl

    def get_effect_types(self, safe=True, **kwargs):
        assert 'effectTypes' in kwargs

        effect_types = kwargs['effectTypes']

        return self.build_effect_types(effect_types, safe)


class VariantTypesMixin(object):
    VARIANT_TYPES = [
        'del', 'ins', 'sub', 'CNV'
    ]

    def get_variant_types(self, safe=True, **kwargs):
        if 'variantTypes' not in kwargs:
            return None
        variant_types = kwargs['variantTypes']
        if safe:
            assert all([vt in self.VARIANT_TYPES for vt in variant_types])
        variant_types = [
            vt for vt in variant_types if vt in self.VARIANT_TYPES
        ]
        if not variant_types:
            return None
        #         if set(variant_types) == set(self.VARIANT_TYPES):
        #             return None
        return variant_types


class ChildGenderMixin(object):
    GENDER = ['male', 'female']
    GENDER_MAP = {'male': 'M', 'female': 'F'}

    def get_child_gender(self, safe=True, **kwargs):
        if 'gender' not in kwargs:
            return None
        gender = kwargs['gender']
        if safe:
            assert all([g in self.GENDER for g in gender])
        gender = [
            g for g in gender if g in self.GENDER
        ]
        if not gender:
            return None
        if set(gender) == set(self.GENDER):
            return None

        return [self.GENDER_MAP[g] for g in gender]


class PresentInMixin(object):
    PRESENT_IN_PARENT_TYPES = [
        "mother only", "father only",
        "mother and father", "neither",
    ]

    PRESENT_IN_CHILD_TYPES = [
        "autism only",
        "affected only",
        "unaffected only",
        "autism and unaffected",
        "affected and unaffected",
        "neither",
    ]

    def get_present_in_child(self, safe=True, **kwargs):
        if 'presentInChild' not in kwargs:
            return None
        present_in_child = kwargs['presentInChild']
        if not present_in_child:
            return None
        if safe:
            assert all([pic in self.PRESENT_IN_CHILD_TYPES
                        for pic in present_in_child])

        present_in_child = [
            pic for pic in present_in_child
            if pic in self.PRESENT_IN_CHILD_TYPES
        ]

        if set(present_in_child) == set(self.PRESENT_IN_CHILD_TYPES):
            return None
        return present_in_child

    def get_present_in_parent(self, safe=True, **kwargs):
        if 'presentInParent' not in kwargs:
            return None
        present_in_parent = kwargs['presentInParent']
        if not present_in_parent:
            return None
        if safe:
            assert all([
                pip in self.PRESENT_IN_PARENT_TYPES
                for pip in present_in_parent
            ])

        present_in_parent = [
            pip for pip in present_in_parent
            if pip in self.PRESENT_IN_PARENT_TYPES
        ]
        return present_in_parent


class RarityMixin(object):

    @classmethod
    def get_ultra_rare(cls, safe=True, **kwargs):
        rarity = kwargs.get('rarity', None)
        if not rarity:
            return None
        ultra_rare = rarity.get('ultraRare', None)
        ultra_rare = bool(ultra_rare)
        return ultra_rare

    @classmethod
    def get_max_alt_freq(cls, safe=True, **kwargs):
        rarity = kwargs.get('rarity', None)
        if not rarity:
            return None

        max_alt_freq = rarity.get('maxFreq', None)
        if max_alt_freq is None:
            return 100.0
        if max_alt_freq >= 100.0:
            return 100.0
        return max_alt_freq

    @classmethod
    def get_min_alt_freq(cls, safe=True, **kwargs):
        rarity = kwargs.get('rarity', None)
        if not rarity:
            return None

        min_alt_freq = rarity.get('minFreq', None)
        if min_alt_freq is None:
            return -1
        if min_alt_freq <= 0.0:
            return -1
        return min_alt_freq

    @classmethod
    def get_min_parents_called(cls, safe=True, **kwargs):
        return 0


class GeneSymsMixin(object):

    @staticmethod
    def get_gene_symbols(**kwargs):
        if 'geneSymbols' not in kwargs:
            return set([])

        gene_symbols = kwargs['geneSymbols']
        if isinstance(gene_symbols, str) or \
                isinstance(gene_symbols, unicode):
            gene_symbols = gene_symbols.replace(',', ' ')
            gene_symbols = gene_symbols.split()

        return set([g.strip() for g in gene_symbols])

    @staticmethod
    def get_gene_weights_query(**kwargs):
        if 'geneWeights' not in kwargs:
            return None, None, None
        gene_weights = kwargs['geneWeights']
        if 'weight' not in gene_weights:
            return None, None, None
        weights_id = gene_weights['weight']
        if weights_id not in Weights.list_gene_weights():
            return None, None, None
        range_start = gene_weights.get('rangeStart', None)
        range_end = gene_weights.get('rangeEnd', None)
        return weights_id, range_start, range_end

    @staticmethod
    def get_gene_set_query(**kwargs):
        if 'geneSet' not in kwargs:
            return None, None, None
        query = kwargs['geneSet']
        if 'geneSet' not in query or 'geneSetsCollection' not in query:
            return None, None, None
        gene_sets_collection = query['geneSetsCollection']
        gene_set = query['geneSet']
        if not gene_sets_collection or not gene_set:
            return None, None, None
        gene_sets_types = query.get('geneSetsTypes', [])
        return gene_sets_collection, gene_set, gene_sets_types


class RegionsMixin(object):
    REGION_REGEXP1 = re.compile("([1-9,X][0-9]?):(\d+)-(\d+)")
    REGION_REGEXP2 = re.compile(
        "^(chr)?(\d+|[Xx]):([\d]{1,3}(,?[\d]{3})*)"
        "(-([\d]{1,3}(,?[\d]{3})*))?$")

    @classmethod
    def get_regions(cls, **kwargs):
        if not kwargs.get('regions', None):
            return None
        regions = kwargs['regions']
        if isinstance(regions, str) or \
                isinstance(regions, unicode):
            regions = regions.split()
        result = []
        for region in regions:
            result.append(cls.get_region(region))
        return [r for r in result if r]

    @classmethod
    def get_region(cls, region):
        res = cls.parse(region)
        if not res:
            return None
        chrome, start, end = res
        return "{}:{}-{}".format(chrome, start, end)

    @classmethod
    def parse(cls, region):
        m = cls.REGION_REGEXP2.match(region)
        if not m:
            return None
        chrome, start, end = m.group(2), m.group(3), m.group(6)
        if not start:
            return None
        start = int(start.replace(',', ''))
        if not end:
            end = start
        else:
            end = int(end.replace(',', ''))

        if start > end:
            return None
        return chrome, start, end


class QueryBase(
    EffectTypesMixin, VariantTypesMixin, ChildGenderMixin,
        PresentInMixin, GeneSymsMixin, RegionsMixin,
        RarityMixin):

    IN_CHILD_TYPES = [
        'prb',
        'sib',
        'prbM',
        'prbF',
        'sibM',
        'sibF',
    ]

    @staticmethod
    def idlist_get(named_list, name):
        for el in named_list:
            if name == el['id']:
                return el
        return None

    @staticmethod
    def get_limit(safe=True, **kwargs):
        limit = kwargs.get('limit', None)
        if limit is None:
            return None
        limit = int(limit)
        return limit
