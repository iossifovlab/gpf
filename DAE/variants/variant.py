'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import re

from DAE import genomesDB
import numpy as np


SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
INS_RE = re.compile('^ins\(([ACGT]+)\)$')
DEL_RE = re.compile('^del\((\d+)\)$')

GA = genomesDB.get_genome()  # @UndefinedVariable


def dae2vcf_variant(chrom, position, var):
    # print(chrom, position, var)

    match = SUB_RE.match(var)
    if match:
        return chrom, position, match.group(1), match.group(2)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = GA.getSequence(chrom, position - 1, position - 1)
        return chrom, position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = GA.getSequence(chrom, position - 1, position + count - 1)
        return chrom, position - 1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)


class VariantBase(object):

    def __init__(self, chromosome, position, reference, alternative):
        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self.alternative = alternative

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.position, self.reference, self.alternative)

    @staticmethod
    def from_dae_variant(chrom, pos, variant):
        return VariantBase(*dae2vcf_variant(chrom, pos, variant))

    @staticmethod
    def from_vcf_variant(variant):
        assert len(variant.ALT) == 1
        return VariantBase(
            variant.CHROM, variant.start + 1, variant.REF, str(variant.ALT[0]))

    @staticmethod
    def from_dict(row):
        v = FamilyVariant(
            row['chr'], row['position'], row['refA'], row['altA'])
        return v

    def __eq__(self, other):
        return self.chromosome == other.chromosome and \
            self.position == other.position and \
            self.reference == other.reference and \
            self.alternative == other.alternative

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return int(self.chromosome) <= int(other.chromosome) and \
            self.position < other.position

    def __gt__(self, other):
        return int(self.chromosome) >= int(other.chromosome) and \
            self.position > other.position


class FamilyVariant(VariantBase):

    def __init__(self, chromosome, position, reference, alternative):
        super(FamilyVariant, self).__init__(
            chromosome, position, reference, alternative)
        self.n_par_called = None
        self.prcnt_par_called = None
        self.n_alt_allels = None
        self.alt_freq = None

        self.effect_type = None
        self.effect_gene = None
        self.effect_details = None

        self.family = None
        self.vcf = None
        self.gt = None

        self._best_st = None
        self._is_mendelian = None
        self._variant_in_members = None
        self._variant_in_roles = None

    @staticmethod
    def from_variant_base(v):
        return FamilyVariant(
            v.chromosome, v.position, v.reference, v.alternative)

    @staticmethod
    def from_dae_variant(chrom, pos, variant):
        return FamilyVariant(*dae2vcf_variant(chrom, pos, variant))

    @staticmethod
    def from_vcf_variant(variant):
        assert len(variant.ALT) == 1
        print(
            variant.CHROM, variant.start + 1,
            variant.REF, str(variant.ALT[0]))
        return FamilyVariant(
            variant.CHROM, variant.start, variant.REF, str(variant.ALT[0]))

    @property
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

    @property
    def members_in_order(self):
        return self.family.members_in_order

    @property
    def members_ids(self):
        return self.family.members_ids

    @property
    def family_id(self):
        return self.family.family_id

    @property
    def variant_in_members(self):
        if self._variant_in_members is None:
            index = np.nonzero(np.sum(self.gt, axis=0))
            self._variant_in_members = set(self.members_ids[index])
        return self._variant_in_members

    @property
    def variant_in_roles(self):
        if self._variant_in_roles is None:
            self._variant_in_roles = [
                self.family.persons[pid]['role']
                for pid in self.variant_in_members
            ]
        return self._variant_in_roles

    @staticmethod
    def from_dict(row):
        v = FamilyVariant(
            row['chr'], row['position'], row['refA'], row['altA'])
        v.set_summary(row)
        return v

    def set_family(self, family):
        self.family = family
        return self

    def set_genotype(self, vcf, gt=None):
        self.vcf = vcf
        if gt is not None:
            self.gt = gt
        else:
            gt = vcf.gt_idxs[self.family.alleles]
            self.gt = gt.reshape([2, len(self.family)], order='F')
        return self

    def set_summary(self, sv):
        # self.n_par_called = sv['all.nParCalled']
        # self.prcnt_par_called = sv['all.prcntParCalled']
        # self.n_alt_allels = sv['all.nAltAlls']
        # self.alt_freq = sv['all.altFreq']

        self.effect_type = sv['effectType']
        self.effect_gene = sv['effectGene']
        self.effect_details = sv['effectDetails']

        return self

    def clone(self):
        v = FamilyVariant.from_variant_base(self)
        v.n_par_called = self.n_par_called
        v.prcnt_par_called = self.prcnt_par_called
        v.n_alt_allels = self.n_alt_allels
        v.alt_freq = self.alt_freq

        v.effect_type = self.effect_type
        v.effect_gene = self.effect_gene
        v.effect_details = self.effect_details

        v.family = self.family
        v.vcf = self.vcf
        v.gt = self.gt

        v._best_st = None
        v._gt = None

        return v

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            alt = np.sum(self.gt, axis=0, dtype=np.int8)
            ref = ref - alt
            self._best_st = np.stack([ref, alt], axis=0)
        return self._best_st

    def is_mendelian(self):
        if self._is_mendelian is None:
            mendelians = []
            for _pid, trio in self.family.trios.items():
                index = self.family.members_index(trio)
                tgt = self.gt[:, index]
                ch = tgt[:, 0]
                p1 = tgt[:, 1]
                p2 = tgt[:, 2]

                m1 = (ch[0] == p1[0] or ch[0] == p1[1]) and \
                    (ch[1] == p2[0] or ch[1] == p2[1])
                m2 = (ch[0] == p2[0] or ch[0] == p2[1]) and \
                    (ch[1] == p1[0] or ch[1] == p1[1])
                mendelians.append(m1 or m2)
            self._is_mendelian = all(mendelians)
        return self._is_mendelian
