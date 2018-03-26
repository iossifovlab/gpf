'''
Created on Mar 26, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family_variant import FamilyVariantBase
from variants.variant import VariantBase
from variants.vcf_utils import vcf2cshl

from variants.attributes import VariantType


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


class FamilyVariantSimple(VariantBase, FamilyVariantBase):

    def __init__(self, summary_variant, family, gt, alt_index):
        VariantBase.__init__(
            self,
            summary_variant.chromosome,
            summary_variant.start,
            summary_variant.reference,
            summary_variant.alternatives[alt_index])

        FamilyVariantBase.__init__(self)

        self.summary = summary_variant
        self.alt_index = alt_index

        self.family = family
        self.gt = gt

        atts = {}
        for k, v in summary_variant._atts.items():
            if isinstance(v, np.ndarray) or isinstance(v, list):
                if alt_index is not None:
                    atts[k] = v[alt_index]
            else:
                atts[k] = v
        self._atts = atts

        self.position = self.get_attr('position', self.start)
        self.variant = self.get_attr('variant')
        self.length = self.get_attr('length', 0)

        self.effect_type = self.get_attr('effectType')
        self.effect_gene = self.get_attr('effectGene')
        self.effect_details = self.get_attr('effectDetails')

        self.n_alt_alls = self.get_attr('all.nAltAlls')
        self.alt_alls_freq = self.get_attr('all.altFreq')
        self.n_par_called = self.get_attr('all.nParCalled')
        self.prcnt_par_called = self.get_attr('all.prcntParCalled')

    def __repr__(self):
        return '{}:{} {}'.format(
            self.chromosome, self.position,
            self.variant)

    def __len__(self):
        return self.length

    @classmethod
    def from_summary_variant(cls, sv, family, gt=None, vcf=None):
        if gt is None:
            assert vcf is not None
            gt = vcf.gt_idxs[family.alleles]
            gt = gt.reshape([2, len(family)], order='F')

        alt_index = cls.calc_alt_allele_index(gt)
        alt_alleles = cls.calc_alt_alleles(gt)

        if alt_index is not None:
            return [cls(sv, family, gt, alt_index)]
        elif len(alt_alleles) > 1:
            res = []
            for alt in sorted(alt_alleles):
                a_gt = np.copy(gt)
                mask = np.logical_not(
                    np.logical_or(
                        a_gt == 0,
                        a_gt == alt
                    ))
                a_gt[mask] = -1
                res.append(cls(sv, family, a_gt, alt - 1))
            return res
        else:
            res = []
            for alt_index in range(len(sv.alternatives)):
                res.append(cls(sv, family, gt, alt_index))
            return res

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)
            alt_alleles = self.calc_alt_alleles(self.gt)
            assert len(alt_alleles) <= 1

            if not alt_alleles:
                alt = np.zeros(len(self.family), dtype=np.int8)
            else:
                anum = next(iter(alt_alleles))
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == anum] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt

            best = [ref, alt]
            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    @property
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

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
        else:
            raise ValueError("unexpected variant type: {}".format(
                self.variant))

#     @staticmethod
#     def from_dict(row):
#         v = FamilyVariantSimple(
#             row['chr'], row['position'], row['refA'], row['altA'])
#         v.set_summary(row)
#         return v


class VariantFactorySimple(object):

    @staticmethod
    def summary_variant_from_dict(data):
        return SummaryVariantSimple.from_dict(data)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariantSimple.from_summary_variant(
            summary_variant, family, gt=None, vcf=vcf)
