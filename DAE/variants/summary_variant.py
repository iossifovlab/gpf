'''
Created on Mar 20, 2018

@author: lubo
'''
from __future__ import print_function

# from icecream import ic

from variants.variant import VariantBase
from variants.vcf_utils import vcf2cshl


class SummaryVariantSimple(VariantBase):

    def __init__(self, chromosome, start, reference, alternatives, atts={}):
        super(SummaryVariantSimple, self).__init__(
            chromosome, start, reference, alternatives, atts=atts)
        position, variant, lengths = vcf2cshl(start, reference, alternatives)
        self._atts.update({
            'position': position,
            'variant': variant,
            'lengths': lengths,
        })


class AlleleItems(object):

    def __init__(self, items):
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


class VariantDetail(object):
    def __init__(self, chrom, position, variant, length):
        self.length = length
        self.type = None
        self.chrom = chrom
        self.cshl_position = position
        self.cshl_variant = variant

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
            chromosome, start, reference, alternative, atts=atts)

        self.alt = AlleleItems(alternative)
        self.alt_details = VariantDetail.from_vcf(
            chromosome, start, reference, alternative)

    @classmethod
    def from_annot_df(cls, row):
        sv = SummaryVariantFull(
            row['chr'], row['position'], row['refA'], row['altA'])
        sv.details = VariantDetail.from_vcf(
            row['chr'], row['position'], row['refA'], row['altA'])

        sv.effect = Effect.from_effects(
            row['effectType'], row['effectGene'], row['effectDetails'])
        return sv
