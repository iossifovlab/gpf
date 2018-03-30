'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.vcf_utils import VcfFamily
from variants.vcf_utils import vcf2cshl

from variants.attributes import VariantType, Inheritance

# from icecream import ic


class VariantBase(object):

    def __init__(self, chromosome, start, reference, alternatives):

        self.chromosome = chromosome
        self.start = start
        self.reference = reference
        self.alternatives = alternatives

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.start,
            self.reference, ",".join(self.alternatives))

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


class FamilyVariantBase(object):

    def __init__(self):
        self._best_st = None
        self._inheritance = None

        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.position,
            self.reference, ",".join(self.alt))

    @staticmethod
    def calc_alt_alleles(gt):
        return sorted(list(set(gt.flatten()).difference({-1, 0})))

    @classmethod
    def calc_alt_allele_index(cls, gt):
        alt_alleles = cls.calc_alt_alleles(gt)
        alt_count = len(alt_alleles)
        if alt_count > 1 or alt_count == 0:
            return None
        else:
            alt_index, = tuple(alt_alleles)
            return alt_index - 1

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

    @classmethod
    def calc_inheritance_trio(cls, p1, p2, ch):
        if cls.check_mendelian_trio(p1, p2, ch):
            return Inheritance.mendelian
        elif cls.check_denovo_trio(p1, p2, ch):
            return Inheritance.denovo
        elif cls.check_omission_trio(p1, p2, ch):
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
        if len(inherits) == 0 or np.any(inherits == Inheritance.unknown.value):
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
            gt = np.copy(self.gt)
            gt[gt == -1] = 0
            index = np.nonzero(np.sum(gt, axis=0))
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
    def from_family_genotype(family, gt):
        fv = FamilyVariantBase()
        fv.family = family
        fv.gt = gt
        return fv


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

        self.size = len(self.items)

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

    def __repr__(self):
        return self.items.__repr__()

    def __str__(self):
        return str(self.items)


class VariantDetail(object):
    def __init__(self, chrom, position, variant, length):
        self.length = length
        self.type = None
        self.chrom = chrom
        self.cshl_position = position
        self.cshl_variant = variant

    @property
    def variant_type(self):
        vt = self.cshl_variant[0]
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

    @staticmethod
    def to_string(gene_effects):
        return str(gene_effects)

    @classmethod
    def from_tuple(cls, t):
        (symbol, effect) = tuple(t)
        return EffectGene(symbol, effect)


class EffectTranscript(object):

    def __init__(self):
        pass


class Effect(object):
    def __init__(self, worst_effect, gene_effects, efffect_transcripts):
        self.worst = worst_effect
        self.gene = EffectGene.from_gene_effects(gene_effects)

    @classmethod
    def from_effects(cls, effect_types, effect_genes, transcripts):
        result = []
        for et, eg, trans in zip(effect_types, effect_genes, transcripts):
            eff = Effect(et, eg, trans)
            result.append(eff)
        return AlleleItems(result)


class SummaryVariant(VariantBase):
    def __init__(self, chromosome, start, reference, alternative, atts={}):
        super(SummaryVariant, self).__init__(
            chromosome, start, reference, alternative)

        self.alt = AlleleItems(alternative)
        self.alt_details = VariantDetail.from_vcf(
            chromosome, start, reference, alternative)
        self.alt_alleles = range(1, len(alternative) + 1)

        self.atts = {}
        self.update_atts(atts)

    @property
    def position(self):
        return self.start

    @property
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

    @classmethod
    def from_dict(cls, row):
        sv = SummaryVariant(
            row['chr'], row['position'], row['refA'], row['altA'], atts=row)
        sv.details = VariantDetail.from_vcf(
            row['chr'], row['position'], row['refA'], row['altA'])

        sv.effect = Effect.from_effects(
            row['effectType'], row['effectGene'], row['effectDetails'])
        sv.frequency = [row['all.refFreq']]
        sv.frequency.extend(row['all.altFreq'])
        return sv

    def get_attr(self, item, default=None):
        val = self.atts.get(item)
        if val is None:
            return default
        return val

    def has_attr(self, item):
        return item in self.atts

    def __getitem__(self, item):
        return self.get_attr(item)

    def __contains__(self, item):
        return item in self.atts

    def update_atts(self, atts):
        for key, val in atts.items():
            self.atts[key] = AlleleItems(val, self.alt_alleles)


class FamilyVariant(FamilyVariantBase):

    def __init__(self, summary_variant, family, gt):
        super(FamilyVariant, self).__init__()

        self.summary = summary_variant
        self.family = family

        self.gt = np.copy(gt)
        unknown = np.any(self.gt == -1, axis=0)
        self.gt[:, unknown] = -1

        self.falt_alleles = self.calc_alt_alleles(self.gt)

    @classmethod
    def from_summary_variant(cls, sv, family, gt=None, vcf=None):
        if gt is None:
            assert vcf is not None
            assert isinstance(family, VcfFamily)

            gt = vcf.gt_idxs[family.alleles]
            gt = gt.reshape([2, len(family)], order='F')

        return [FamilyVariant(sv, family, gt)]

    @property
    def alt(self):
        return self.summary.alt

    @property
    def alt_alleles(self):
        return self.summary.alt_alleles

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
    def location(self):
        return "{}:{}".format(self.chromosome, self.position)

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
    def frequency(self):
        return self.summary.frequency

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

    @property
    def genotype(self):
        return self.gt.T

    @property
    def atts(self):
        return self.summary.atts

    def get_attr(self, item, default=None):
        return self.summary.get_attr(item, default)

    def has_attr(self, item):
        return self.summary.has_attr(item)

    def __getitem__(self, item):
        return self.get_attr(item)

    def __contains__(self, item):
        return item in self.summary


class VariantFactory(object):

    @staticmethod
    def summary_variant_from_dict(data):
        return SummaryVariant.from_dict(data)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariant.from_summary_variant(
            summary_variant, family, vcf=vcf)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return FamilyVariant.from_summary_variant(
            summary_variant, family, gt=gt)


class FamilyVariantSingle(FamilyVariant):

    def __init__(self, summary_variant, family, gt, alt_index):
        super(FamilyVariantSingle, self).__init__(
            summary_variant, family, gt)

        self.alt_index = alt_index
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


class VariantFactorySingle(object):

    @staticmethod
    def summary_variant_from_dict(data):
        return SummaryVariant.from_dict(data)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        return FamilyVariantSingle.from_summary_variant(
            summary_variant, family, vcf=vcf)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return FamilyVariantSingle.from_summary_variant(
            summary_variant, family, gt=gt)
