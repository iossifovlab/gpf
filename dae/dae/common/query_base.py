'''
Created on Feb 6, 2017

@author: lubo
'''
import itertools
from dae.gene.weights import Weights


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
        "Intron": ["intron", "non-coding-intron"],
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
        "non-coding-intron": "Intron",
    }
    EFFECT_GROUPS = {
        "coding": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "No-frame-shift-newStop",
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
            "No-frame-shift-newStop",
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
        if isinstance(effect_types, str):
            effect_types = effect_types.split(',')
        etl = [et.strip() for et in effect_types]
        etl = self._build_effect_types_groups(etl)
        etl = self._build_effect_types_list(etl)
        if safe:
            assert all([et in self.EFFECT_TYPES for et in etl])
        else:
            etl = [et for et in etl if et in self.EFFECT_TYPES]
        return etl

    def build_effect_types_naming(self, effect_types, safe=True):
        if isinstance(effect_types, str):
            effect_types = effect_types.split(',')
        assert isinstance(effect_types, list)
        if safe:
            assert all([
                et in self.EFFECT_TYPES or
                et in list(self.EFFECT_TYPES_MAPPING.keys())
                for et in effect_types])
        return [
            self.EFFECT_TYPES_UI_NAMING.get(et, et) for et in effect_types
        ]

    def get_effect_types(self, safe=True, **kwargs):
        effect_types = kwargs.get('effectTypes', None)
        if effect_types is None:
            return None

        return self.build_effect_types(effect_types, safe)


class GeneSymsMixin(object):

    @staticmethod
    def get_gene_symbols(**kwargs):
        gene_symbols = kwargs.get('geneSymbols', None)
        if gene_symbols is None:
            return set([])

        if isinstance(gene_symbols, str):
            gene_symbols = gene_symbols.replace(',', ' ')
            gene_symbols = gene_symbols.split()

        return set([g.strip() for g in gene_symbols])

    @staticmethod
    def get_gene_weights_query(gene_info_config, **kwargs):
        gene_weights = kwargs.get('geneWeights', None)
        if gene_weights is None:
            return None, None, None
        if 'weight' not in gene_weights:
            return None, None, None
        weights_id = gene_weights['weight']
        if weights_id not in Weights.list_gene_weights(gene_info_config):
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

    @classmethod
    def get_gene_syms(cls, gene_info_config, **kwargs):
        result = cls.get_gene_symbols(**kwargs) | \
            cls.get_gene_weights(gene_info_config, **kwargs)

        return result if result else None

    @classmethod
    def get_gene_weights(cls, gene_info_config, **kwargs):
        weights_id, range_start, range_end = cls.get_gene_weights_query(
            gene_info_config, **kwargs)
        if not weights_id or \
                weights_id not in Weights.list_gene_weights(gene_info_config):
            return set([])

        weights = Weights.load_gene_weights(weights_id, gene_info_config)
        return weights.get_genes(wmin=range_start, wmax=range_end)
