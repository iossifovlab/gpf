'''
Created on Mar 26, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family_variant import FamilyVariantBase
from variants.variant import VariantBase
from variants.vcf_utils import vcf2cshl, VcfFamily

from variants.attributes import VariantType
from variants.variant_full import SummaryVariantFull, FamilyVariantFull


class FamilyVariantSimple(FamilyVariantFull):

    def __init__(self, summary_variant, family, gt, alt_index):
        super(FamilyVariantSimple, self).__init__(
            summary_variant, family, gt)

        self.alt_index = alt_index
        # self.falt_alleles = [alt_index + 1]
        assert len(self.falt_alleles) <= 1

    @classmethod
    def from_summary_variant(cls, sv, family, gt=None, vcf=None):
        assert isinstance(family, VcfFamily)

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


class VariantFactorySimple(object):

    @staticmethod
    def summary_variant_from_dict(data):
        return SummaryVariantFull.from_dict(data)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariantSimple.from_summary_variant(
            summary_variant, family, vcf=vcf)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return FamilyVariantSimple.from_summary_variant(
            summary_variant, family, gt=gt)
