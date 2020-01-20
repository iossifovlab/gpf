import numpy as np
from typing import Any, Dict, Optional, List

from dae.variants.variant import Variant, Allele, SummaryVariant, \
    SummaryAllele, Effect
from dae.pedigrees.family import Family
from dae.variants.attributes import Inheritance, GeneticModel, TransmissionType
import itertools
from dae.utils.variant_utils import GENOTYPE_TYPE, is_all_unknown_genotype, \
    is_reference_genotype


def calculate_simple_best_state(
    genotype: np.array, allele_count: int
) -> np.array:
    # Simple best state calculation
    # Treats every genotype as diploid (including male X non-PAR)
    ref = (2 * np.ones(genotype.shape[1], dtype=GENOTYPE_TYPE))
    unknown = np.any(genotype == -1, axis=0)

    best_st = [ref]
    for allele_index in range(1, allele_count):
        alt_gt = np.zeros(genotype.shape, dtype=GENOTYPE_TYPE)
        alt_gt[genotype == allele_index] = 1

        alt = np.sum(alt_gt, axis=0, dtype=GENOTYPE_TYPE)
        best_st[0] = best_st[0] - alt
        best_st.append(alt)

    best_st = np.stack(best_st, axis=0)
    best_st[:, unknown] = -1

    return best_st


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


class FamilyAllele(Allele, FamilyDelegate):

    def __init__(
            self,
            summary_allele: SummaryAllele,
            family: Family,
            genotype,
            best_state):
        assert isinstance(family, Family)

        FamilyDelegate.__init__(self, family)

        #: summary allele that corresponds to this allele in family variant
        self.summary_allele = summary_allele

        self.gt = genotype
        assert self.gt.dtype == GENOTYPE_TYPE, (self.gt, self.gt.dtype)
        self._best_st = best_state
        self._genetic_model = None

        self._inheritance_in_members = None
        self._variant_in_members = None
        self._variant_in_members_objects = None
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
    def chromosome(self) -> str:
        return self.summary_allele.chromosome

    @property
    def position(self) -> int:
        return self.summary_allele.position

    @property
    def reference(self) -> str:
        return self.summary_allele.reference

    @property
    def alternative(self) -> str:
        return self.summary_allele.alternative

    @property
    def summary_index(self) -> int:
        return self.summary_allele.summary_index

    @property
    def allele_index(self) -> int:
        return self.summary_allele.allele_index

    @property
    def transmission_type(self) -> TransmissionType:
        return self.summary_allele.transmission_type

    @property
    def attributes(self) -> Dict[str, Any]:
        return self.summary_allele.attributes

    @property
    def details(self):
        return self.summary_allele.details

    @property
    def effect(self) -> Optional[Effect]:
        return self.summary_allele.effect

    @property
    def genotype(self):
        """
        Returns genotype of the family.
        """
        return self.gt.T

    @property
    def best_st(self):
        if self._best_st is None:
            self._best_st = calculate_simple_best_state(
                self.gt, self.attributes['allele_count']
            )
        return self._best_st

    @property
    def genetic_model(self):
        if self._genetic_model is None:
            self._genetic_model = GeneticModel.autosomal
        return self._genetic_model

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
            result = []
            for pid in self.members_ids:
                if pid not in self.family.trios:
                    result.append(Inheritance.unknown)
                    continue
                trio = self.family.trios[pid]
                trio_index = self.family.members_index(trio)

                trio_gt = self.gt[:, trio_index]
                if np.any(trio_gt == -1):
                    inh = Inheritance.unknown
                elif np.all(trio_gt != allele_index):
                    inh = Inheritance.missing
                else:
                    ch = trio_gt[:, 0]
                    p1 = trio_gt[:, 1]
                    p2 = trio_gt[:, 2]
                    inh = self.calc_inheritance_trio(p1, p2, ch, allele_index)
                    if inh != Inheritance.omission and \
                            np.all(ch != allele_index):
                        inh = Inheritance.missing
                result.append(inh)
            self._inheritance_in_members = result
        return self._inheritance_in_members

    @property
    def variant_in_members(self):
        """
        Returns set of members IDs of the family that are affected by
        this family variant.
        """
        if self._variant_in_members is None:
            allele_index = getattr(self, "allele_index", None)
            gt = np.copy(self.gt)

            if allele_index is not None:
                gt[gt != allele_index] = -1

            index = np.any(gt == allele_index, axis=0)
            self._variant_in_members = [
                m.person_id if has_variant else None
                for m, has_variant in zip(self.members_in_order, index)
            ]

        return self._variant_in_members

    @property
    def variant_in_members_objects(self):
        if self._variant_in_members_objects is None:

            variant_in_members = set(filter(None, self.variant_in_members))
            self._variant_in_members_objects = [
                member
                for member in self.family.members_in_order
                if member.person_id in variant_in_members
            ]
        return self._variant_in_members_objects

    @property
    def variant_in_roles(self):
        """
        Returns list of roles (or 'None') of the members of the family that are
        affected by this family variant.
        """
        if self._variant_in_roles is None:
            self._variant_in_roles = [
                self.family.persons[pid].role if pid is not None else None
                for pid in self.variant_in_members
            ]
        return self._variant_in_roles

    @property
    def variant_in_sexes(self):
        """
        Returns list of sexes (or 'None') of the members of the family that are
        affected by this family variant.
        """
        if self._variant_in_sexes is None:
            self._variant_in_sexes = [
                self.family.persons[pid].sex if pid is not None else None
                for pid in self.variant_in_members
            ]
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


class FamilyVariant(Variant, FamilyDelegate):

    def __init__(
            self,
            summary_variant: SummaryVariant,
            family: Family,
            genotype: Any,
            best_state: Any):

        self.gt = np.copy(genotype)

        family_alleles = [
            FamilyAllele(sum_allele, family, genotype, best_state)
            for sum_allele in summary_variant.alleles
        ]

        assert family is not None
        assert genotype is not None
        assert isinstance(family, Family)
        assert isinstance(family_alleles, list)
        assert all([isinstance(a, FamilyAllele) for a in family_alleles]), \
            family_alleles

        self.summary_variant = summary_variant

        FamilyDelegate.__init__(self, family)
        self.gt = np.copy(genotype)
        self._genetic_model = None

        self.summary_alleles = self.summary_variant.alleles

        alleles = [
            family_alleles[0]
        ]
        for ai in self.calc_alt_alleles(self.gt):
            allele = None
            for fa in family_alleles:
                if fa.allele_index == ai:
                    allele = fa
                    break
            if allele is None:
                continue
            assert allele.allele_index == ai, \
                (allele.allele_index, ai)

            alleles.append(allele)

        self._family_alleles = alleles
        self._best_st = best_state
        self._matched_alleles = []

    @property
    def chrom(self) -> str:
        return self.summary_variant.chrom

    @property
    def position(self) -> int:
        return self.summary_variant.position

    @property
    def reference(self) -> str:
        return self.summary_variant.reference

    # @property
    # def alternative(self) -> Optional[str]:
    #     return self.summary_variant.alternative

    @property
    def allele_count(self):
        return self.summary_variant.allele_count

    @property
    def summary_index(self) -> int:
        return self.summary_variant.summary_index

    @property
    def alleles(self) -> List[FamilyAllele]:
        return self._family_alleles

    def set_matched_alleles(self, alleles_indexes):
        self._matched_alleles = sorted(alleles_indexes)

    @property
    def matched_alleles(self):
        return [
            aa for aa in self.alleles
            if aa.allele_index in self._matched_alleles
        ]

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

    @property
    def genetic_model(self):
        if self._genetic_model is None:
            self._genetic_model = GeneticModel.autosomal
        return self._genetic_model

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
        return is_reference_genotype(self.gt)

    def is_unknown(self):
        """
        Returns True if all alleles in the family variant are
        `unknown`.
        """
        return is_all_unknown_genotype(self.gt)

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
            self._best_st = calculate_simple_best_state(
                self.gt, self.allele_count
            )
        return self._best_st

    @staticmethod
    def calc_alt_alleles(gt):
        """
        Returns alternative allele indexes that are relevant for the
        given genotype.

        :param gt: genotype as `np.array`.
        :return: list of all alternative allele indexes present into
                 genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({0})))

    @staticmethod
    def calc_alleles(gt):
        """
        Returns allele indexes that are relevant for the given genotype.

        :param gt: genotype as `np.array`.
        :return: list of all allele indexes present into genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({-1})))
