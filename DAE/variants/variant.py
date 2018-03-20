'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function


# from icecream import ic
class VariantBase(object):

    def __init__(self, chromosome, start, reference, alternatives, atts={}):
        self._atts = atts
        self.chromosome = chromosome
        self.start = start
        self.reference = reference
        self.alternatives = alternatives

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.start,
            self.reference, self.alternatives)

    @staticmethod
    def from_vcf_variant(variant):
        return VariantBase(
            variant.CHROM, variant.start, variant.REF, variant.ALT)

    @classmethod
    def from_dict(cls, row):
        v = cls(
            row['chr'], row['position'], row['refA'], row['altA'], atts=row)
        return v

    def __eq__(self, other):
        return self.chromosome == other.chromosome and \
            self.start == other.start and \
            self.reference == other.reference and \
            self.alternatives == other.alternatives

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return int(self.chromosome) <= int(other.chromosome) and \
            self.start < other.start

    def __gt__(self, other):
        return int(self.chromosome) >= int(other.chromosome) and \
            self.start > other.start

    def get_attr(self, item, default=None):
        val = self._atts.get(item)
        if val is None:
            return default
        return val

    def has_attr(self, item):
        return item in self._atts

    def __getitem__(self, item):
        return self.get_attr(item)

    def __contains__(self, item):
        return item in self._atts

    def update_atts(self, atts):
        self._atts.update(atts)
