'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

# from icecream import ic

import numpy as np
from variants.attributes import Inheritance
from variants.vcf_utils import vcf2cshl


class VariantBase(object):

    def __init__(self, chromosome, start, reference, alternatives, atts={}):
        self._atts = atts
        self.chromosome = chromosome
        self.start = start
        self.reference = reference
        self.alt = alternatives

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.start, self.reference, self.alt)

#     @property
#     def alternative(self):
#         return ','.join(self.alt)

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
            self.alt == other.alt

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


class SummaryVariant(VariantBase):

    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariant, self).__init__(
            chromosome, start, reference, alternative, atts=atts)
        position, variant, lengths = vcf2cshl(start, reference, alternative)
        self._atts.update({
            'position': position,
            'variant': variant,
            'lengths': lengths,
        })


class FamilyVariant(VariantBase):

    def __init__(self, summary_variant, family, gt, alt_index):
        super(FamilyVariant, self).__init__(
            summary_variant.chromosome,
            summary_variant.start,
            summary_variant.reference,
            summary_variant.alt[alt_index])

        self.summary = summary_variant
        self.alt_index = alt_index

        self.family = family
        self.gt = gt

        atts = {}
        for k, v in summary_variant._atts.items():
            if isinstance(v, np.ndarray):
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

        self._best_st = None
        self._inheritance = None

        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

    def __repr__(self):
        return '{}:{} {} vcf({}->{})'.format(
            self.chromosome, self.position,
            self.variant, self.reference, ','.join(self.alt))

    def __len__(self):
        return self.length

    @staticmethod
    def from_summary_variant(sv, family, gt=None, vcf=None):
        if gt is None:
            assert vcf is not None
            gt = vcf.gt_idxs[family.alleles]
            gt = gt.reshape([2, len(family)], order='F')

        alt_index = FamilyVariant.calc_alt_allele_index(gt)
        alt_alleles = FamilyVariant.calc_alt_alleles(gt)

        if alt_index is not None:
            return [FamilyVariant(sv, family, gt, alt_index)]
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
                res.append(FamilyVariant(sv, family, a_gt, alt - 1))
            return res
        else:
            res = []
            for alt_index in range(len(sv.alt)):
                res.append(FamilyVariant(sv, family, gt, alt_index))
            return res

    @staticmethod
    def calc_alt_alleles(gt):
        return set(gt.flatten()).difference({-1, 0})

    @staticmethod
    def calc_alt_allele_index(gt):
        alt_alleles = FamilyVariant.calc_alt_alleles(gt)
        alt_count = len(alt_alleles)
        if alt_count > 1 or alt_count == 0:
            return None
        else:
            alt_index, = tuple(alt_alleles)
            return alt_index - 1

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)
            alt_alleles = FamilyVariant.calc_alt_alleles(self.gt)
            assert len(alt_alleles) <= 1

            if not alt_alleles:
                alt = np.zeros(len(self.family))
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
            return 'sub'
        elif vt == 'i':
            return 'ins'
        elif vt == 'd':
            return 'del'
        elif vt == 'c':
            return 'complex'
        else:
            raise ValueError("unexpected variant type: {}".format(
                self.variant))

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

    @staticmethod
    def check_mendelian_trio(p1, p2, ch):
        m1 = (ch[0] == p1[0] or ch[0] == p1[1]) and \
            (ch[1] == p2[0] or ch[1] == p2[1])
        m2 = (ch[0] == p2[0] or ch[0] == p2[1]) and \
            (ch[1] == p1[0] or ch[1] == p1[1])
        return m1 or m2

    @staticmethod
    def check_denovo_trio(p1, p2, ch):
        new_alleles = set(ch).difference(set(p1) | set(p2))
        return bool(new_alleles)

    @staticmethod
    def check_omission_trio(p1, p2, ch):
        child_alleles = set(ch)
        p1res = False
        p2res = False

        if p1[0] == p1[1]:
            p1res = not bool(p1[0] in child_alleles)
        if p2[0] == p2[1]:
            p2res = not bool(p2[0] in child_alleles)

        return p1res or p2res

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

    def is_reference(self):
        return self.inheritance == Inheritance.reference

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
            elif np.all(self.gt == 0):
                self._inheritance = Inheritance.reference
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
