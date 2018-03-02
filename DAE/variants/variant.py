'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import re

from DAE import genomesDB
import numpy as np
from variants.attributes import Inheritance


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


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join([col_sep.join([str(n) for n in mat[i, :]])
                         for i in xrange(mat.shape[0])])


class VariantBase(object):

    def __init__(self, chromosome, position, reference, alternative):
        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self.alternative = alternative
        self.alt = alternative.split(',')

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.position, self.reference, self.alternative)

    @staticmethod
    def from_dae_variant(chrom, pos, variant):
        return VariantBase(*dae2vcf_variant(chrom, pos, variant))

    @staticmethod
    def from_vcf_variant(variant):
        # assert len(variant.ALT) == 1
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
        self._inheritance = None

        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

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

    @property
    def variant_in_sexes(self):
        if self._variant_in_sexes is None:
            self._variant_in_sexes = set([
                self.family.persons[pid]['sex']
                for pid in self.variant_in_members
            ])
        return self._variant_in_sexes

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
            alt_alleles = []
            unknown = np.any(self.gt == -1, axis=0)

            for anum in range(1, len(self.alt) + 1):
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == anum] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt
                alt_alleles.append(alt)
            best = [ref]
            best.extend(alt_alleles)
            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    @staticmethod
    def check_mendelian_trio(p1, p2, ch):
        m1 = (ch[0] == p1[0] or ch[0] == p1[1]) and \
            (ch[1] == p2[0] or ch[1] == p2[1])
        m2 = (ch[0] == p2[0] or ch[0] == p2[1]) and \
            (ch[1] == p1[0] or ch[1] == p1[1])
        return m1 or m2

    @staticmethod
    def check_denovo_trio(p1, p2, ch):
        pred2 = ((p1[0] == p1[1]) and
                 (p2[0] == p2[1]) and
                 ((ch[0] != p1[0] and ch[0] != p2[0]) or
                  (ch[1] != p1[0] and ch[1] != p2[0])))

        pred4 = (((p1[0] != p1[1] and p2[0] != p2[1]) and
                  ((np.any(ch[0] == p1) and np.all(ch[1] != p2)) or
                   (np.any(ch[1] == p1) and np.all(ch[0] != p2)))) or
                 ((p1[0] != p1[1] and p2[0] != p2[1]) and
                  ((np.any(ch[0] == p2) and np.all(ch[1] != p1)) or
                     (np.any(ch[1] == p2) and np.all(ch[0] != p1)))))
        pred5 = p1[0] == p1[1] and p2[0] != p2[1] and \
            ((ch[0] == p1[0] and np.any(ch[1] != p2)) or
             (ch[1] == p1[0] and np.any(ch[0] != p2)))
        pred6 = p2[0] == p2[1] and p1[0] != p1[1] and\
            ((ch[0] == p2[0] and np.any(ch[1] != p1)) or
             (ch[1] == p2[0] and np.any(ch[0] != p1)))

        pred7 = p2[0] == p2[1] and p1[0] != p1[1] and \
            np.all(ch != p2[0]) and \
            np.all(ch != p1[0]) and \
            np.all(ch != p1[1])
        pred8 = p1[0] == p1[1] and p2[0] != p2[1] and \
            np.all(ch != p1[0]) and \
            np.all(ch != p2[0]) and \
            np.all(ch != p2[1])

        # print(pred2, pred4, pred5, pred6, pred7, pred8)

        return pred2 or pred4 or pred5 or pred6 or pred7 or pred8

    @staticmethod
    def check_omission_trio(p1, p2, ch):
        return ((p1[0] == p1[1]) and
                (p2[0] == p2[1]) and
                (p1[0] != p2[0]) and
                ((ch[0] != p1[0] or ch[1] != p1[0]) or
                 (ch[0] != p2[0] or ch[1] != p2[0])) and
                ((ch[0] == p1[0] or ch[0] == p2[0]) and
                 (ch[1] == p1[0] or ch[1] == p2[0]))) or \
            ((p1[0] == p1[1] and ch[0] != p1[0] and ch[1] != p1[0]) or
             (p2[0] == p2[1] and ch[0] != p2[0] and ch[1] != p2[0]))

    @staticmethod
    def calc_inheritance_trio(p1, p2, ch):
        if FamilyVariant.check_mendelian_trio(p1, p2, ch):
            return Inheritance.mendelian
        elif FamilyVariant.check_denovo_trio(p1, p2, ch):
            return Inheritance.denovo
        elif FamilyVariant.check_omission_trio(p1, p2, ch):
            return Inheritance.omission
        else:
            print("strange inheritance:", p1, p2, ch)
            return Inheritance.unknown

    def is_mendelian(self):
        return self.inheritance == Inheritance.mendelian

    def is_denovo(self):
        return self.inheritance == Inheritance.denovo

    def is_omission(self):
        return self.inheritance == Inheritance.omission

    @staticmethod
    def combine_inheritance(*inheritance):
        inherits = np.array([i.value for i in inheritance])
        inherits = np.array(inherits)
        if np.any(inherits == Inheritance.unknown.value):
            return Inheritance.unknown
        elif np.all(inherits == Inheritance.mendelian.value):
            return Inheritance.mendelian
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                inherits == Inheritance.denovo.value)):
            return Inheritance.denovo
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                inherits == Inheritance.omission.value)):
            return Inheritance.omission
        elif np.all(np.logical_or(
                inherits == Inheritance.mendelian.value,
                np.logical_or(
                    inherits == Inheritance.omission.value,
                    inherits == Inheritance.denovo.value
                ))):
            return Inheritance.other
        else:
            print("strange inheritance:", inherits)
            return Inheritance.unknown

    @property
    def inheritance(self):
        if self._inheritance is None:
            inherits = []
            if np.any(self.gt == -1):
                self._inheritance = Inheritance.unknown
            else:
                for _pid, trio in self.family.trios.items():
                    index = self.family.members_index(trio)
                    tgt = self.gt[:, index]
                    ch = tgt[:, 0]
                    p1 = tgt[:, 1]
                    p2 = tgt[:, 2]

                    inherits.append(self.calc_inheritance_trio(p1, p2, ch))
                self._inheritance = self.combine_inheritance(*inherits)

        return self._inheritance

#         if self._inheritance is None:
#             if self.is_mendelian():
#                 self._inheritance = Inheritance.mendelian
#             elif self.is_denovo():
#                 self._inheritance = Inheritance.denovo
#             elif self.is_omission():
#                 self._inheritance = Inheritance.omission
#             elif self.is_unknown():
#                 self._inheritance = Inheritance.unknown
#             else:
#                 self._inheritance = Inheritance.other
#         return self._inheritance
