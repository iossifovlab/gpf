'''
Created on Mar 20, 2018

@author: lubo
'''
from __future__ import print_function

from icecream import ic

from variants.variant import VariantBase
from variants.vcf_utils import vcf2cshl


class SummaryVariantSimple(VariantBase):

    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariantSimple, self).__init__(
            chromosome, start, reference, alternative, atts=atts)
        position, variant, lengths = vcf2cshl(start, reference, alternative)
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
            elif not index:
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


class SummaryVariantFull(VariantBase):
    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariantSimple, self).__init__(
            chromosome, start, reference, alternative, atts=atts)
