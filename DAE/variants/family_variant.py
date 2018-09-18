'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function

from builtins import range
from builtins import object
import numpy as np

from variants.variant import SummaryVariant, SummaryAllele
from variants.family import Family
from variants.attributes import Inheritance
import itertools
from variants.vcf_utils import GENOTYPE_TYPE


class FamilyDelegate(object):

    def __init__(self, family):
        self.family = family

    @property
    def members_in_order(self):
        """
        Returns list of the members of the family in the order specified from
        the pedigree file. Each element of the returned list is an object of
        type :class:`variants.family.Person`.
        """
        return self.family.members_in_order

    @property
    def members_ids(self):
        """
        Returns list of family members IDs.
        """
        return self.family.members_ids

    @property
    def family_id(self):
        """
        Returns the family ID.
        """
        return self.family.family_id


class FamilyAllele(SummaryAllele, FamilyDelegate):

    def __init__(self, summary_allele, family, genotype):
        assert isinstance(family, Family)
        assert isinstance(summary_allele, SummaryAllele)

        #: summary allele that corresponds to this allele in family variant
        self.summary_allele = summary_allele
        self.gt = genotype

        FamilyDelegate.__init__(self, family)

        self._inheritance = None
        self._inheritance_in_members = None
        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

        self.matched_gene_effects = []

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
    def genotype(self):
        """
        Returns genotype of the family.
        """
        return self.gt.T

    def gt_flatten(self):
        """
        Return genotype of the family variant flattened to 1-dimensional
        array.
        """
        return self.gt.flatten(order='F')

    @property
    def inheritance_in_members(self):
        if self._inheritance_in_members is None:
            allele_index = self.allele_index
            result = {pid: Inheritance.unknown for pid in self.members_ids}
            for ch_id, trio in list(self.family.trios.items()):
                index = self.family.members_index(trio)
                tgt = self.gt[:, index]
                if np.any(tgt == -1):
                    result[ch_id] = Inheritance.unknown
                elif np.all(tgt != allele_index):
                    result[ch_id] = Inheritance.missing
                else:
                    ch = tgt[:, 0]
                    p1 = tgt[:, 1]
                    p2 = tgt[:, 2]
                    inh = self.calc_inheritance_trio(p1, p2, ch, allele_index)
                    if inh != Inheritance.omission and \
                            np.all(ch != allele_index):
                        inh = Inheritance.missing
                    result[ch_id] = inh
            self._inheritance_in_members = set(result.values())
        return self._inheritance_in_members

    @property
    def variant_in_members(self):
        """
        Returns set of members IDs of the family that are affected by
        this family variant.
        """
        allele_index = getattr(self, "allele_index", None)
        if self._variant_in_members is None:
            gt = np.copy(self.gt)
            if allele_index is not None:
                gt[gt != allele_index] = 0
            else:
                gt[gt == -1] = 0
            index = np.nonzero(np.sum(gt, axis=0))
            self._variant_in_members = set(self.members_ids[index])
        return self._variant_in_members

    @property
    def variant_in_roles(self):
        """
        Returns set of sexes of the members of the family that are affected by
        this family variant.
        """
        if self._variant_in_roles is None:
            self._variant_in_roles = [
                self.family.persons[pid]['role']
                for pid in self.variant_in_members
            ]
        return self._variant_in_roles

    @property
    def variant_in_sexes(self):
        """
        Returns set of roles of the members of the family that are affected by
        this family variant.
        """
        if self._variant_in_sexes is None:
            self._variant_in_sexes = set([
                self.family.persons[pid]['sex']
                for pid in self.variant_in_members
            ])
        return self._variant_in_sexes

    @staticmethod
    def check_mendelian_trio(p1, p2, ch, allele_index):
        """
        Checks if the inheritance type for a trio family is `mendelian`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        ai = allele_index
        if ai not in set(ch):
            return False

        m1 = (ch[0] == p1[0] == ai or ch[0] == p1[1] == ai) or \
            (ch[1] == p2[0] == ai or ch[1] == p2[1] == ai)
        m2 = (ch[0] == p2[0] == ai or ch[0] == p2[1] == ai) or \
            (ch[1] == p1[0] == ai or ch[1] == p1[1] == ai)

        return m1 or m2

    @staticmethod
    def check_denovo_trio(p1, p2, ch, allele_index):
        """
        Checks if the inheritance type for a trio family is `denovo`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        new_alleles = set(ch).difference(set(p1) | set(p2))
        return allele_index in new_alleles

    @staticmethod
    def check_omission_trio(p1, p2, ch, allele_index):
        """
        Checks if the inheritance type for a trio family is `omission`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        if allele_index not in set(p1) | set(p2):
            return False

        child_alleles = set(ch)
        if allele_index in child_alleles:
            return False

        p1res = False
        p2res = False

        if p1[0] == p1[1] == allele_index:
            p1res = not bool(p1[0] in child_alleles)
        if p2[0] == p2[1] == allele_index:
            p2res = not bool(p2[0] in child_alleles)

        return p1res or p2res

    @classmethod
    def calc_inheritance_trio(cls, p1, p2, ch, allele_index):
        """
        Calculates the inheritance type of a trio family.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: inheritance type as :class:`variants.attributes.Inheritance`
            of the trio family.
        """
        if cls.check_mendelian_trio(p1, p2, ch, allele_index):
            return Inheritance.mendelian
        elif cls.check_denovo_trio(p1, p2, ch, allele_index):
            return Inheritance.denovo
        elif cls.check_omission_trio(p1, p2, ch, allele_index):
            return Inheritance.omission
        else:
            return Inheritance.other

    def __getattr__(self, name):
        return getattr(self.summary_allele, name)


class FamilyVariant(SummaryVariant, FamilyDelegate):

    def __init__(self, summary_variant, family, genotype):
        assert summary_variant is not None
        assert isinstance(summary_variant, SummaryVariant)
        assert family is not None
        assert genotype is not None
        assert isinstance(family, Family)

        FamilyDelegate.__init__(self, family)
        self.summary_variant = summary_variant
        self.gt = np.copy(genotype)

        alleles = [
            FamilyAllele(summary_variant.ref_allele, family, self.gt)
        ]

        for allele_index in self.calc_alt_alleles(self.gt):
            summary_allele = summary_variant.get_allele(allele_index)
            if summary_allele is None:
                continue
            fa = FamilyAllele(summary_allele, family, genotype)

            alleles.append(fa)

        #: list of all family alleles that affect the family variant
        self.alleles = alleles
        #: reference family allele fot the give family variant
        self.ref_allele = alleles[0]
        #: list of all alternative family alleles that affect family variant
        self.alt_alleles = alleles[1:]

        self._best_st = None
        self._inheritance_in_members = None
        self._variant_in_members = None
        self._matched_alleles = []

    def set_matched_alleles(self, alleles_indexes):
        self._matched_alleles = alleles_indexes

    @property
    def matched_alleles(self):
        return [self.alleles[ai] for ai in self._matched_alleles]

    @property
    def matched_alleles_indexes(self):
        return self._matched_alleles

    @property
    def matched_gene_effects(self):
        return set(itertools.chain.from_iterable([
            ma.matched_gene_effects for ma in self.matched_alleles
        ]))

    @property
    def genotype(self):
        """
        Returns genotype of the family.
        """
        return self.gt.T

    def gt_flatten(self):
        """
        Return genotype of the family variant flattened to 1-dimensional
        array.
        """
        return self.gt.flatten(order='F')

    def is_reference(self):
        """
        Returns True if all known alleles in the family variant are
        `reference`.
        """
        return np.any(self.gt == 0) and \
            np.all(np.logical_or(self.gt == 0, self.gt == -1))

    def is_unknown(self):
        """
        Returns True if all known alleles in the family variant are
        `reference`.
        """
        return np.all(self.gt == -1)

    @property
    def inheritance_in_members(self):
        if self._inheritance_in_members is None:
            self._inheritance_in_members = set()
            for allele in self.alleles:
                self._inheritance_in_members = self._inheritance_in_members | \
                    allele.inheritance_in_members
        return self._inheritance_in_members

    @property
    def variant_in_members(self):
        if self._variant_in_members is None:
            self._variant_in_members = set()
            for allele in self.alt_alleles:
                self._variant_in_members = self._variant_in_members | \
                    allele.variant_in_members
        return self._variant_in_members

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
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=GENOTYPE_TYPE))
            unknown = np.any(self.gt == -1, axis=0)

            allele_count = self.summary_variant.allele_count()

            balt = []
            for allele_index in range(1, allele_count):
                alt_gt = np.zeros(self.gt.shape, dtype=GENOTYPE_TYPE)
                alt_gt[self.gt == allele_index] = 1

                alt = np.sum(alt_gt, axis=0, dtype=GENOTYPE_TYPE)
                ref = ref - alt
                balt.append(alt)

            best = [ref]
            best.extend(balt)

            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st

    def __getattr__(self, name):
        return getattr(self.summary_variant, name)

    @staticmethod
    def calc_alt_alleles(gt):
        """
        Returns alternative allele indexes that are relevant for the
        given genotype.

        :param gt: genotype as `np.array`.
        :return: list of all alternative allele indexes present into
        genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({-1, 0})))

    @staticmethod
    def calc_alleles(gt):
        """
        Returns allele indexes that are relevant for the given genotype.

        :param gt: genotype as `np.array`.
        :return: list of all allele indexes present into genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({-1})))
