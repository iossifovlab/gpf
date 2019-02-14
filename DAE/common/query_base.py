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
        "No-frame-shift": ["no-frame-shift"],
        "No-frame-shift-newStop": ["no-frame-shift-newStop"],
        "noStart": ["noStart"],
        "noEnd": ["noEnd"],
        "Synonymous": ["synonymous"],
        "Non coding": ["non-coding"],
        "Intron": ["intron", 'non-coding-intron'],
        "Intergenic": ["intergenic"],
        "3'-UTR": ["3'UTR", "3'UTR-intron"],
        "5'-UTR": ["5'UTR", "5'UTR-intron"],
        "CNV": ["CNV+", "CNV-"],
        "CNV+": ["CNV+"],
        "CNV-": ["CNV-"],
    }

    EFFECT_TYPES_UI_NAMING = {
        "nonsense": "Nonsense",
        "frame-shift": "Frame-shift",
        "splice-site": "Splice-site",
        "missense": "Missense",
        "no-frame-shift": "No-frame-shift",
        "no-frame-shift-newStop": "No-frame-shift-newStop",
        "synonymous": "Synonymous",
        "non-coding": "Non coding",
        "intron": "Intron",
        'non-coding-intron': 'Intron',
    }
    EFFECT_GROUPS = {
        "coding": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "No-frame-shift",
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
            "No-frame-shift-newStop",
        ],
        "nonsynonymous": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "No-frame-shift",
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

    def build_effect_types_naming(self, effect_types, safe=True):
        if isinstance(effect_types, str) or \
                isinstance(effect_types, unicode):
            effect_types = effect_types.replace(',', ' ')
            effect_types = effect_types.split()
        assert isinstance(effect_types, list)
        if safe:
            assert all([
                et in self.EFFECT_TYPES or
                et in self.EFFECT_TYPES_MAPPING.keys() for et in effect_types])
        return [
            self.EFFECT_TYPES_UI_NAMING.get(et, et) for et in effect_types
        ]

    def get_effect_types(self, safe=True, **kwargs):
        effect_types = kwargs.get('effectTypes', None)
        if effect_types is None:
            return None

        return self.build_effect_types(effect_types, safe)


class VariantTypesMixin(object):
    VARIANT_TYPES = [
        'del', 'ins', 'sub', 'CNV', 'complex'
    ]

    @classmethod
    def get_variant_types(cls, safe=True, **kwargs):
        variant_types = kwargs.get('variantTypes', None)
        if variant_types is None:
            return None
        if safe:
            assert all([vt in cls.VARIANT_TYPES for vt in variant_types])
        variant_types = [
            vt for vt in variant_types if vt in cls.VARIANT_TYPES
        ]
        if not variant_types:
            return None
        if set(variant_types) == set(cls.VARIANT_TYPES):
            return None
        return variant_types


class StudyNamesMixin(object):

    @classmethod
    def get_study_names(self, safe=True, **kwargs):
        study_names = kwargs.get('studyFilters', None)
        if not study_names:
            return None
        study_names = map(lambda el: el.get('studyName', None), study_names)
        study_names = filter(None, study_names)
        if not study_names:
            return None
        return set(study_names)


class StudyTypesMixin(object):
    STUDY_TYPES = [
        'we', 'wg', 'tg', 'cnv'
    ]

    def get_study_types(self, safe=True, **kwargs):
        study_types = kwargs.get('studyTypes', None)
        if study_types is None:
            return None
        study_types = [st.lower() for st in study_types]
        if safe:
            assert all([vt in self.STUDY_TYPES for vt in study_types])
        study_types = [
            st for st in study_types if vt in self.STUDY_TYPES
        ]
        if not study_types:
            return None
        if set(study_types) == set(self.STUDY_TYPES):
            return None
        return study_types


class ChildGenderMixin(object):
    GENDER = ['male', 'female', 'unspecified']
    GENDER_MAP = {'male': 'M', 'female': 'F', 'unspecified': 'U'}

    def build_child_gender(self, gender):
        assert gender in ['all', 'male', 'female', 'unspecified']
        if gender == 'all':
            return ['male', 'female', 'unspecified']
        else:
            return [gender]

    def get_child_gender(self, safe=True, **kwargs):
        gender = kwargs.get('gender', None)
        if gender is None:
            return None
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
        "mother only",
        "father only",
        "mother and father",
        "neither",
    ]

    PRESENT_IN_CHILD_TYPES = [
        "affected only",
        "unaffected only",
        "affected and unaffected",
        "neither",
    ]

    @classmethod
    def get_present_in_child(cls, safe=True, **kwargs):
        if 'presentInChild' not in kwargs:
            return None
        present_in_child = kwargs['presentInChild']
        if not present_in_child:
            return None
        if safe:
            assert all([pic in cls.PRESENT_IN_CHILD_TYPES
                        for pic in present_in_child])

        present_in_child = [
            pic for pic in present_in_child
            if pic in cls.PRESENT_IN_CHILD_TYPES
        ]

        if set(present_in_child) == set(cls.PRESENT_IN_CHILD_TYPES):
            return None
        return present_in_child

    @classmethod
    def _get_present_in_parent_root(cls, safe=True, **kwargs):
        present_in_parent = kwargs.get('presentInParent', None)
        if not present_in_parent:
            return None
        if 'presentInParent' in present_in_parent:
            present_in_parent = present_in_parent['presentInParent']
        return present_in_parent

    @classmethod
    def get_present_in_parent(cls, safe=True, **kwargs):
        present_in_parent = \
            cls._get_present_in_parent_root(safe=safe, **kwargs)
        if not present_in_parent:
            return ['neither']
        if safe:
            assert all([
                pip in cls.PRESENT_IN_PARENT_TYPES
                for pip in present_in_parent
            ])

        present_in_parent = [
            pip for pip in present_in_parent
            if pip in cls.PRESENT_IN_PARENT_TYPES
        ]
        return present_in_parent


class RarityMixin(object):

    @classmethod
    def _get_rarity_root(cls, safe=True, **kwargs):
        if 'rarity' in kwargs:
            return kwargs['rarity']
        elif 'presentInParent' in kwargs:
            present_in_parent = kwargs['presentInParent']
            if isinstance(present_in_parent, dict):
                return present_in_parent.get('rarity', None)
        return None

    @classmethod
    def get_ultra_rare(cls, safe=True, **kwargs):
        rarity = cls._get_rarity_root(safe=safe, **kwargs)
        if not rarity:
            return None
        ultra_rare = rarity.get('ultraRare', None)
        ultra_rare = bool(ultra_rare)
        return ultra_rare

    @classmethod
    def get_max_alt_freq(cls, safe=True, **kwargs):
        rarity = cls._get_rarity_root(safe=safe, **kwargs)
        if not rarity:
            return -1

        max_alt_freq = rarity.get('maxFreq', None)
        if max_alt_freq is None:
            return -1
        if max_alt_freq >= 100.0:
            return -1
        return max_alt_freq

    @classmethod
    def get_min_alt_freq(cls, safe=True, **kwargs):
        rarity = cls._get_rarity_root(safe=safe, **kwargs)
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
        gene_symbols = kwargs.get('geneSymbols', None)
        if gene_symbols is None:
            return set([])

        if isinstance(gene_symbols, str) or \
                isinstance(gene_symbols, unicode):
            gene_symbols = gene_symbols.replace(',', ' ')
            gene_symbols = gene_symbols.split()

        return set([g.strip() for g in gene_symbols])

    @staticmethod
    def get_gene_weights_query(**kwargs):
        gene_weights = kwargs.get('geneWeights', None)
        if gene_weights is None:
            return None, None, None
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
        query = kwargs.get('geneSet', None)
        if query is None:
            return None, None, None
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


class FamiliesMixin(object):

    @staticmethod
    def get_family_ids(safe=True, **kwargs):
        family_ids = kwargs.get('familyIds', None)
        if not family_ids:
            return None
        return set(family_ids)


class GenomicScoresMixin(object):

    @staticmethod
    def get_genomic_scores(safe=True, **kwargs):
        genomic_scores = kwargs.get('genomicScores', None)
        if not genomic_scores:
            return []
        genomic_scores_filter = [{
            'metric': score['metric'],
            'min': (score['rangeStart']
                    if score['rangeStart'] else float("-inf")),
            'max': score['rangeEnd'] if score['rangeEnd'] else float("inf"),
        } for score in genomic_scores]
        return genomic_scores_filter


class QueryBase(
        EffectTypesMixin,
        VariantTypesMixin,
        StudyNamesMixin,
        StudyTypesMixin,
        ChildGenderMixin,
        PresentInMixin,
        GeneSymsMixin,
        RegionsMixin,
        RarityMixin,
        FamiliesMixin,
        GenomicScoresMixin):

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
