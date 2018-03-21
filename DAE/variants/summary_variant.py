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
        details = [
            VariantDetail(chrom, p, v, l)
            for (p, v, l) in zip(vcf2cshl(position, reference, alternative))
        ]
        return AlleleItems(details)


class EffectDetail(object):
    def __init__(self, worst_effect, gene_effect, effect_details):
        self.worst = worst_effect
        self.gene = gene_effect
        self.transcript = effect_details


class SummaryVariantFull(VariantBase):
    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariantSimple, self).__init__(
            chromosome, start, reference, alternative, atts=atts)

        self.alt = AlleleItems(alternative)
        self.alt_details = VariantDetail.from_vcf(
            chromosome, start, reference, alternative)
