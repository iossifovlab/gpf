'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np

from variants.variant import SummaryVariant, SummaryAllele
from variants.family import Family
from variants.attributes import Inheritance


class FamilyInheritanceMixture(object):

    def __init__(self, family, genotype):
        assert family is not None
        assert genotype is not None
        assert isinstance(family, Family)

        self.family = family
        self.gt = np.copy(genotype)
        self._best_st = None
        self._inheritance = None
        self._inheritance_in_members = None
        self._variant_in_members = None
        self._variant_in_roles = None
        self._variant_in_sexes = None

    @property
    def best_st(self):
        raise NotImplementedError("should be implemented into subclasses")

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
    def inheritance(self):
        """
        Returns the inheritance type of a variant in family. The method
        splits the family into trios, calculates the inheritance type for
        each trio and returns the combined inheritance type as
        :class:`variants.attributes.Inheritance`.
        """
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
    def inheritance_in_members(self):
        if self._inheritance_in_members is None:
            allele_index = getattr(self, "allele_index", None)
            result = {pid: Inheritance.unknown for pid in self.members_ids}
            for ch_id, trio in self.family.trios.items():
                index = self.family.members_index(trio)
                tgt = self.gt[:, index]
                if np.any(tgt == -1):
                    result[ch_id] = Inheritance.unknown
                else:
                    ch = tgt[:, 0]
                    if allele_index is not None and \
                            not np.any(ch == allele_index):
                        result[ch_id] = Inheritance.missing
                    else:
                        p1 = tgt[:, 1]
                        p2 = tgt[:, 2]
                        result[ch_id] = self.calc_inheritance_trio(p1, p2, ch)
            self._inheritance_in_members = set(result.values())
        return self._inheritance_in_members

    def is_reference(self):
        """
        Returns True if all alleles in the family variant are
        `reference`.
        """
        return np.all(self.gt == 0)

    def is_mendelian(self):
        """
        Return True if the inheritance type of the family variant is
        `medelian`.
        """
        return self.inheritance == Inheritance.mendelian

    def is_denovo(self):
        """
        Return True if the inheritance type of the family variant is
        `denovo`.
        """
        return self.inheritance == Inheritance.denovo

    def is_omission(self):
        """
        Return True if the inheritance type of the family variant is
        `omission`.
        """
        return self.inheritance == Inheritance.omission

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

    @staticmethod
    def check_mendelian_trio(p1, p2, ch):
        """
        Checks if the inheritance type for a trio family is `mendelian`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        m1 = (ch[0] == p1[0] or ch[0] == p1[1]) and \
            (ch[1] == p2[0] or ch[1] == p2[1])
        m2 = (ch[0] == p2[0] or ch[0] == p2[1]) and \
            (ch[1] == p1[0] or ch[1] == p1[1])
        return m1 or m2

    @staticmethod
    def check_denovo_trio(p1, p2, ch):
        """
        Checks if the inheritance type for a trio family is `denovo`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        new_alleles = set(ch).difference(set(p1) | set(p2))
        return bool(new_alleles)

    @staticmethod
    def check_omission_trio(p1, p2, ch):
        """
        Checks if the inheritance type for a trio family is `omission`.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
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
        """
        Calculates the inheritance type of a trio family.

        :param p1: genotype of the first parent (pair of allele indexes).
        :param p2: genotype of the second parent.
        :param ch: genotype of the child.
        :return: inheritance type as :class:`variants.attributes.Inheritance`
            of the trio family.
        """
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
        """
        Combines iheritance types and returns inheritance type as
        :class:`variants.attributes.Inheritance`.

        To calculate the inheritance of a non-trio family, it is split into
        trios, iheritance type of each trio is calculated using
        :func:`calc_inheritance_trio`, and the iheritance types of all trio
        families are combined into single inheritacne type.

        :return: combined inheritance type as
            :class:`variants.attributes.Inheritance`
        """
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

#     @staticmethod
#     def get_allele_genotype(genotype, allele_index):
#         """
#         Given a family full genotype and an allele index returns the
#         genotype that corresponds to the specified allele index.
#
#         :Example: if we have a trio family with genotype
#
#
#         .. code-block:: python
#
#             np.array([[0,0,1],[0,0,2]])
#
#
#         the genotype that corresponds to allele index 1 should be:
#
#         .. code-block:: python
#
#             np.array([[0,0,1],[0,0,-1]])
#
#         Similarily the genotype, that corresponds to allele index 2 is:
#
#         .. code-block:: python
#
#             np.array([[0,0,-1],[0,0,2]])
#         """
#         gt = np.copy(genotype)
#         mask = np.logical_not(np.logical_or(
#             gt == 0,
#             gt == allele_index,
#         ))
#         gt[mask] = -2
#         return gt


class FamilyAllele(SummaryAllele, FamilyInheritanceMixture):

    def __init__(self, summary_allele, family, genotype):
        assert isinstance(family, Family)
        assert isinstance(summary_allele, SummaryAllele)

        FamilyInheritanceMixture.__init__(self, family, genotype)
        self.summary_allele = summary_allele

    def __getattr__(self, name):
        return getattr(self.summary_allele, name)

    @property
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
            alt_gt[self.gt == self.allele_index] = 1

            alt = np.sum(alt_gt, axis=0, dtype=np.int8)
            ref = ref - alt

            best = [ref, alt]

            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st


class FamilyVariant(SummaryVariant, FamilyInheritanceMixture):

    def __init__(self, summary_variant, family, genotype):
        assert summary_variant is not None
        assert isinstance(summary_variant, SummaryVariant)

        self.summary_variant = summary_variant

        FamilyInheritanceMixture.__init__(self, family, genotype)

        alleles = [
            FamilyAllele(summary_variant.ref_allele, family, genotype)
        ]

        for allele_index in self.calc_alt_alleles(self.gt):
            summary_allele = summary_variant.alleles[allele_index]
            fa = FamilyAllele(summary_allele, family, genotype)

            alleles.append(fa)
        self.alleles = alleles
        self.alt_alleles = alleles[1:]

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
    def best_st(self):
        if self._best_st is None:
            ref = (2 * np.ones(len(self.family), dtype=np.int8))
            unknown = np.any(self.gt == -1, axis=0)

            balt = []
            for aa in self.summary_variant.alt_alleles:
                alt_gt = np.zeros(self.gt.shape, dtype=np.int8)
                alt_gt[self.gt == aa.allele_index] = 1

                alt = np.sum(alt_gt, axis=0, dtype=np.int8)
                ref = ref - alt
                balt.append(alt)

            best = [ref]
            best.extend(balt)

            self._best_st = np.stack(best, axis=0)
            self._best_st[:, unknown] = -1

        return self._best_st
