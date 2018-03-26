'''
Created on Mar 26, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family_variant import FamilyVariantBase
from variants.variant import VariantBase
from variants.vcf_utils import VcfFamily
from variants.vcf_utils import vcf2cshl

from variants.attributes import VariantType


class AlleleItems(object):

    def __init__(self, items, alt_alleles=None):
        if not hasattr(items, '__iter__'):
            items = [items]

        if alt_alleles is None:
            self.items = items
            self.alt_alleles = range(1, len(self.items) + 1)
        else:
            assert len(alt_alleles) == len(items) or len(items) == 1
            if len(items) == 1:
                item = items[0]
                self.items = [item for _ in alt_alleles]
            else:
                self.items = items

        self.size = len(items)

    def _to_zero_based(self, index):
        if isinstance(index, slice):
            return slice(self._to_zero_based(index.start),
                         self._to_zero_based(index.stop),
                         index.step)
        else:
            if index is None or index < 0:
                return index
            elif not 1 <= index <= self.size:
                raise IndexError("invalid allele index: {}".format(index))
            return index - 1

    def __getitem__(self, key):
        index = self._to_zero_based(key)
        if isinstance(index, int):
            return self.items[index]
        elif isinstance(index, slice):
            return [
                self.items[i]
                for i in range(*index.indices(self.size))
            ]
        raise TypeError("bad allele index type: {}".format(index))

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return self.size


class VariantDetail(object):
    def __init__(self, chrom, position, variant, length):
        self.length = length
        self.type = None
        self.chrom = chrom
        self.cshl_position = position
        self.cshl_variant = variant

    @property
    def variant_type(self):
        vt = self.variant[0]
        if vt == 's':
            return VariantType.substitution
        elif vt == 'i':
            return VariantType.insertion
        elif vt == 'd':
            return VariantType.deletion
        elif vt == 'c':
            return VariantType.complex
        elif vt == 'C':
            return VariantType.CNV
        else:
            raise ValueError("unexpected variant type: {}".format(
                self.variant))

    @property
    def cshl_location(self):
        return "{}:{}".format(self.chrom, self.cshl_position)

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        variant_details = vcf2cshl(position, reference, alternative)
        variant_details = zip(*variant_details)
        details = [
            VariantDetail(chrom, p, v, l)
            for (p, v, l) in variant_details
        ]
        return AlleleItems(details)


class EffectGene(object):
    def __init__(self, symbol=None, effect=None):
        self.symbol = symbol
        self.effect = effect

    def __repr__(self):
        return "{}:{}".format(self.symbol, self.effect)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_gene_effects(cls, gene_effects):
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_string(cls, data):
        return cls.from_tuple(data.split(":"))

    @classmethod
    def from_tuple(cls, (symbol, effect)):
        return EffectGene(symbol, effect)


class EffectTranscript(object):

    def __init__(self):
        pass


class Effect(object):
    def __init__(self, worst_effect, gene_effects, efffect_transcripts):
        self.worst = worst_effect
        self.gene = EffectGene.from_gene_effects(gene_effects)

    @classmethod
    def from_effects(cls, effect_types, effect_genes, effect_transcripts):
        result = []
        for et, eg, et in zip(effect_types, effect_genes, effect_transcripts):
            eff = Effect(et, eg, et)
            result.append(eff)
        return AlleleItems(result)


class SummaryVariantFull(VariantBase):
    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariantFull, self).__init__(
            chromosome, start, reference, alternative, atts={})

        self.alt = AlleleItems(alternative)
        self.alt_details = VariantDetail.from_vcf(
            chromosome, start, reference, alternative)
        self.alt_alleles = range(1, len(alternative) + 1)

        for key, val in atts.items():
            self._atts[key] = AlleleItems(val, self.alt_alleles)

    @property
    def position(self):
        return self.start

    @property
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

    @classmethod
    def from_dict(cls, row):
        sv = SummaryVariantFull(
            row['chr'], row['position'], row['refA'], row['altA'], atts=row)
        sv.details = VariantDetail.from_vcf(
            row['chr'], row['position'], row['refA'], row['altA'])

        sv.effect = Effect.from_effects(
            row['effectType'], row['effectGene'], row['effectDetails'])
        return sv


class FamilyVariantFull(FamilyVariantBase):

    def __init__(self, summary_variant, family, gt):
        super(FamilyVariantFull, self).__init__()

        self.summary = summary_variant
        self.family = family
        self.gt = gt

        self.alt_alleles = self.calc_alt_alleles(self.gt)

    @classmethod
    def from_vcf(cls, sv, family, vcf):
        assert isinstance(family, VcfFamily)
        assert vcf is not None

        gt = vcf.gt_idxs[family.alleles]
        gt = gt.reshape([2, len(family)], order='F')

        return [FamilyVariantFull(sv, family, gt)]

    @property
    def alt(self):
        return self.summary.alt

    @property
    def alternatives(self):
        return self.summary.alternatives

    @property
    def chromosome(self):
        return self.summary.chromosome

    @property
    def position(self):
        return self.summary.position

    @property
    def reference(self):
        return self.summary.reference

    @property
    def alt_details(self):
        return self.summary.alt_details

    @property
    def effect(self):
        return self.summary.effect

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            balt = []
            for anum in self.summary.alt_alleles:
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == anum] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt
                balt.append(alt)

            best = [ref]
            best.extend(balt)
            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    def get_attr(self, item, default=None):
        val = self.summary._atts.get(item)
        if val is None:
            return default
        return val

    def has_attr(self, item):
        return item in self.summary._atts

    def __getitem__(self, item):
        return self.get_attr(item)

    def __contains__(self, item):
        return item in self.summary._atts


class VariantFactoryFull(object):

    @staticmethod
    def summary_variant_from_dict(data):
        return SummaryVariantFull.from_dict(data)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariantFull.from_vcf(summary_variant, family, vcf)
