'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.family import Family
from variants.vcf_utils import vcf2cshl

from variants.attributes import VariantType, Inheritance
from variants.effects import Effect
import itertools


class VariantBase(object):
    """
    VariantBase is a base class for variants. It supports description of
    a variant in *a la VCF* style.

    Expected parameters of the constructor are:

    :param chromosome: chromosome label where variant is located
    :param position: position of the variant using *VCF* convention
    :param reference: reference DNA string
    :param alternatives: list of alternative DNA strings

    Each object of `VariantBase` has following fields:

    :ivar chromosome: chromosome lable where variant is located
    :ivar position: position of the variant using *VCF* convention
    :ivar reference: reference DNA string
    :ivar alternative: alternative DNA string
    """

    def __init__(self, chromosome, position, reference,
                 alternative=None):

        #: chromosome on which the variant is located
        self.chromosome = chromosome
        #: 1-based start postion of this variant on the reference
        self.position = position
        #: reference DNA string
        self.reference = reference

        self._alternative = alternative

    @property
    def alternative(self):
        """
        alternative DNA string; comma separated string when multiple
        alternative DNA strings should be represented; alternative is None
        when the variant is a reference variant.
        """
        return self._alternative

    def __repr__(self):
        if not self._alternative:
            return '{}:{} {} (ref)'.format(
                self.chromosome, self.position,
                self.reference)
        else:
            return '{}:{} {}->{}'.format(
                self.chromosome, self.position,
                self.reference,
                self._alternative)

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


class AltAlleleItems(object):
    """
    1-based list for representing list of items relevant to the list
    of alternative alleles.
    """

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
        self.variant_type = VariantType.from_cshl_variant(self.cshl_variant)

    def __repr__(self):
        return "{} {}".format(
            self.cshl_location,
            self.cshl_variant)

    @property
    def cshl_location(self):
        return "{}:{}".format(self.chrom, self.cshl_position)

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        return VariantDetail(
            chrom, *vcf2cshl(position, reference, alternative))


class SummaryAllele(VariantBase):
    """
    `SummaryAllele` represents a single allele for given position.
    """

    def __init__(self,
                 chromosome,
                 position,
                 reference,
                 alternative=None,
                 summary_index=None,
                 allele_index=0,
                 effect=None,
                 frequency=None,
                 attributes=None):
        super(SummaryAllele, self).__init__(
            chromosome, position, reference, alternative)

        #: index of the summary variant this allele belongs to
        self.summary_index = summary_index
        #: index of the allele of summary variant
        self.allele_index = allele_index

        if alternative is None:
            self.details = None
        else:
            self.details = VariantDetail.from_vcf(
                chromosome, position, reference, alternative)
        #: variant effect of the allele; None for the reference allele.
        self.effect = effect
        #: frequency of the allele
        self.frequency = frequency

        if attributes is None:
            #: allele additional attributes
            self.attributes = {}
        else:
            self.attributes = {}
            self.update_attributes(attributes)

    @property
    def is_reference_allele(self):
        return self.alternative is None

    def get_attribute(self, item, default=None):
        """
        looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.attributes.get(item, default)
        return val

    def has_attribute(self, item):
        """
        checks if additional variant attributes contain values for key `item`.
        """
        return item in self.attributes

    def update_attributes(self, atts):
        """
        updates additional attributes of variant using dictionary `atts`.
        """
        for key, val in atts.items():
            self.attributes[key] = val

    def __getitem__(self, item):
        """
        allows using of standard dictionary access to additional variant
        attributes. For example `sv['af_parents_called']` will return value
        matching key `af_parents_called` from addtional variant attributes.
        """
        return self.get_attribute(item)

    def __contains__(self, item):
        """
        checks if additional variant attributes contain value for key `item`.
        """
        return item in self.attribute


class SummaryVariant(VariantBase):

    def __init__(self, alleles):
        assert len(alleles) >= 1
        assert len(set([sa.position for sa in alleles])) == 1

        assert alleles[0].is_reference_allele

        self.alleles = alleles
        self.ref_allele = alleles[0]
        self.alt_alleles = alleles[1:]

        super(SummaryVariant, self).__init__(
            self.ref_allele.chromosome,
            self.ref_allele.position,
            self.ref_allele.reference)

        self.summary_index = self.ref_allele.summary_index

    @property
    def alternative(self):
        if not self.alt_alleles:
            return None
        return ','.join([aa.alternative for aa in self.alt_alleles])

    @property
    def details(self):
        """
        1-based list of `VariantDetails`, that describes each
        alternative allele.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.details for sa in self.alt_alleles])

    @property
    def effects(self):
        """
        1-based list of `Effect`, that describes variant effects.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.effect for sa in self.alt_alleles])

    @property
    def frequencies(self):
        """
        0-base list of frequencies for variant.
        """
        return [sa.frequency for sa in self.alleles]

    @property
    def variant_types(self):
        """
        returns set of variant types.
        """
        return set([aa.details.variant_type for aa in self.alt_alleles])

    def get_attribute(self, item, default=None):
        return [sa.get_attribute(item, default) for sa in self.alt_alleles]

    def has_attribute(self, item):
        return any([sa.has_attribute(item) for sa in self.alt_alleles])

    def __getitem__(self, item):
        return self.get_attribute(item)

    def __contains__(self, item):
        return self.has_attribute(item)

    def update_attributes(self, atts):
        # FIXME:
        for key, values in atts.items():
            assert len(values) == 1 or len(values) == len(self.alt_alleles)
            for sa, val in zip(self.alt_alleles, itertools.cycle(values)):
                sa.update_attributes({key: val})


class FamilyVariant(SummaryVariant):

    def __init__(self, summary_variant, family, genotype):
        assert summary_variant is not None
        assert isinstance(summary_variant, SummaryVariant)

        self.summary_variant = summary_variant

        assert family is not None
        assert genotype is not None
        assert isinstance(family, Family)

        self.family = family
        self._best_st = None
        self._inheritance = None
        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

        self.gt = np.copy(genotype)
        alleles = [summary_variant.ref_allele]

        for allele_index in self.calc_alt_alleles(self.gt):
            fa = summary_variant.alleles[allele_index]
            alleles.append(fa)
        self.alleles = alleles
        self.alt_alleles = AltAlleleItems(alleles[1:])

    def __getattr__(self, name):
        return getattr(self.summary_variant, name)

    def __repr__(self):
        if not self.alternative:
            return '{}:{} {}(ref) {}'.format(
                self.chromosome, self.position,
                self.reference, self.family_id)
        else:
            return '{}:{} {}->{} {}'.format(
                self.chromosome, self.position,
                self.reference, self.alternative,
                self.family_id)

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
    def genotype(self):
        return self.gt.T

    def gt_flatten(self):
        return self.gt.flatten(order='F')

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            balt = []
            if len(self.alleles) == 1:
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                balt.append(alt)
            else:
                for anum, _ in enumerate(self.alt_alleles):
                    alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                    alt_gt[self.gt == (anum + 1)] = 1

                    alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                    ref = ref - alt
                    balt.append(alt)

            best = [ref]
            best.extend(balt)

            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

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

    def is_reference(self):
        return self.inheritance == Inheritance.reference

    def is_mendelian(self):
        return self.inheritance == Inheritance.mendelian

    def is_denovo(self):
        return self.inheritance == Inheritance.denovo

    def is_omission(self):
        return self.inheritance == Inheritance.omission

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
    def calc_alt_alleles(gt):
        return sorted(list(set(gt.flatten()).difference({-1, 0})))

    @staticmethod
    def calc_alleles(gt):
        return sorted(list(set(gt.flatten()).difference({-1})))

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


class SummaryVariantFactory(object):

    @staticmethod
    def summary_allele_from_record(record):
        if not isinstance(record['effect_type'], str):
            effects = None
        else:
            effects = Effect.from_effects(
                record['effect_type'],
                zip(record['effect_gene_genes'],
                    record['effect_gene_types']),
                zip(record['effect_details_transcript_ids'],
                    record['effect_details_details']))
        alternative = record['alternative']

        return SummaryAllele(
            record['chrom'], record['position'],
            record['reference'],
            alternative=alternative,
            summary_index=record['summary_index'],
            allele_index=record['allele_index'],
            effect=effects,
            frequency=record['af_allele_freq'],
            attributes=record)

    @staticmethod
    def summary_variant_from_records(records):
        assert len(records) > 0

        alleles = []
        for record in records:
            sa = SummaryVariantFactory.summary_allele_from_record(record)
            alleles.append(sa)

        return SummaryVariant(alleles)
