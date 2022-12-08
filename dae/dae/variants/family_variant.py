import copy
import logging

from typing import Any, List, Optional

import numpy as np

from deprecation import deprecated  # type: ignore

from dae.pedigrees.family import Family
from dae.utils.variant_utils import GenotypeType, \
    is_all_unknown_genotype, \
    is_reference_genotype, \
    mat2str

from dae.variants.attributes import GeneticModel, \
    Inheritance,\
    TransmissionType

from dae.effect_annotation.effect import AlleleEffects
from dae.variants.core import Allele
from dae.variants.variant import \
    SummaryAllele, \
    SummaryVariant


logger = logging.getLogger(__name__)


def calculate_simple_best_state(
        genotype: np.ndarray, allele_count: int) -> np.ndarray:
    # Simple best state calculation
    # Treats every genotype as diploid (including male X non-PAR)
    ref: np.ndarray = 2 * np.ones(genotype.shape[1], dtype=GenotypeType)
    unknown = np.any(genotype == -1, axis=0)

    best_st = [ref]
    for allele_index in range(1, allele_count):
        alt_gt = np.zeros(genotype.shape, dtype=GenotypeType)
        alt_gt[genotype == allele_index] = 1

        alt = np.sum(alt_gt, axis=0, dtype=GenotypeType)
        best_st[0] = best_st[0] - alt
        best_st.append(alt)

    best_st_arr = np.stack(best_st, axis=0)
    best_st_arr[:, unknown] = -1

    return best_st_arr


class FamilyDelegate:
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
    def __init__(
            self,
            summary_allele: SummaryAllele,
            family: Family,
            genotype,
            best_state,
            genetic_model=None,
            inheritance_in_members=None):

        assert isinstance(family, Family)

        FamilyDelegate.__init__(self, family)

        #: summary allele that corresponds to this allele in family variant
        self.summary_allele: SummaryAllele = summary_allele

        self.gt = genotype

        # assert self.gt.dtype == GenotypeType, (self.gt, self.gt.dtype)
        self._best_state = best_state
        self._genetic_model = genetic_model
        if self._genetic_model is None:
            self._genetic_model = GeneticModel.autosomal

        self._inheritance_in_members = inheritance_in_members
        self._variant_in_members = None
        self._variant_in_members_objects = None
        self._variant_in_roles = None
        self._variant_in_sexes = None
        self._variant_in_statuses = None
        self._family_index = None
        self._family_attributes: dict = {}

        self.matched_gene_effects: List = []

    def __repr__(self):
        allele_repr = SummaryAllele.__repr__(self)
        return f"{allele_repr} {self.family_id}"

    @property
    def chromosome(self):
        return self.summary_allele.chromosome

    @property
    def chrom(self):
        return self.summary_allele.chromosome

    @property
    def position(self):
        return self.summary_allele.position

    @property
    def reference(self):
        return self.summary_allele.reference

    @property
    def alternative(self):
        return self.summary_allele.alternative

    @property
    def summary_index(self):
        return self.summary_allele.summary_index

    @summary_index.setter
    def summary_index(self, val):
        self.summary_allele.summary_index = val

    @property
    def family_index(self):
        return self._family_index

    @family_index.setter
    def family_index(self, val):
        self._family_index = val

    @property
    def allele_index(self):
        return self.summary_allele.allele_index

    @property
    def transmission_type(self) -> TransmissionType:
        return self.summary_allele.transmission_type

    @property
    def summary_attributes(self):
        return self.summary_allele.attributes

    @property
    def family_attributes(self):
        return self._family_attributes

    @property
    def attributes(self):
        result = copy.deepcopy(self.summary_attributes)
        result.update(self.family_attributes)
        return result

    def get_attribute(self, item: str, default=None):
        """
        looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.family_attributes.get(item, default)
        if val is not None:
            return val
        return self.summary_allele.get_attribute(item, default)

    def has_attribute(self, item: str) -> bool:
        """
        checks if additional variant attributes contain values for key `item`.
        """
        return item in self.family_attributes or \
            item in self.summary_attributes

    def update_attributes(self, atts: dict) -> None:
        """
        updates additional attributes of variant using dictionary `atts`.
        """
        self._family_attributes.update(atts)

    @property
    def details(self):
        return self.summary_allele.details

    @property
    def effects(self) -> Optional[AlleleEffects]:
        return self.summary_allele.effects

    @property
    def allele_type(self) -> Allele.Type:
        return self.summary_allele.allele_type

    @property
    def end_position(self) -> Optional[int]:
        return self.summary_allele.end_position

    @property
    def genotype(self):
        """
        Returns genotype of the family.
        """
        return self.gt.T

    @property
    def best_state(self):
        if self._best_state is None:
            self._best_state = calculate_simple_best_state(
                self.gt, self.attributes["allele_count"]
            )
        return self._best_state

    @property  # type: ignore
    @deprecated(details="Replace `best_st` with `best_state`")
    def best_st(self):
        return self.best_state

    @property
    def genetic_model(self):
        return self._genetic_model

    def gt_flatten(self):
        """
        Return genotype of the family variant flattened to 1-dimensional
        array.
        """
        return self.gt.flatten(order="F")

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
                    if inh != Inheritance.omission and np.all(
                        ch != allele_index
                    ):
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
    def allele_in_members(self):
        return self.variant_in_members

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
    def allele_in_roles(self):
        return self.variant_in_roles
    
    @property
    def variant_in_statuses(self):
        """Return list of statuses (or 'None') of the members with variant."""
        if self._variant_in_statuses is None:
            self._variant_in_statuses = [
                self.family.persons[pid].status if pid is not None else None
                for pid in self.variant_in_members
            ]
        return self._variant_in_statuses

    @property
    def allele_in_statuses(self):
        return self.variant_in_statuses

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

    @property
    def allele_in_sexes(self):
        return self.variant_in_sexes

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

        m1 = (ch[0] == p1[0] == ai or ch[0] == p1[1] == ai) or (
            ch[1] == p2[0] == ai or ch[1] == p2[1] == ai
        )
        m2 = (ch[0] == p2[0] == ai or ch[0] == p2[1] == ai) or (
            ch[1] == p1[0] == ai or ch[1] == p1[1] == ai
        )

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


class FamilyVariant(SummaryVariant, FamilyDelegate):
    def __init__(
            self,
            summary_variant: SummaryVariant,
            family: Family,
            genotype: Any,
            best_state: Any,
            inheritance_in_members=None):

        # super(FamilyVariant, self).__init__()

        assert family is not None
        assert isinstance(family, Family)
        FamilyDelegate.__init__(self, family)

        self.summary_variant = summary_variant
        self.summary_alleles = self.summary_variant.alleles
        self.gt = genotype
        self._genetic_model = None

        self._family_alleles: Optional[List[FamilyAllele]] = None
        self._best_state = best_state

        self._fvuid: Optional[str] = None
        if inheritance_in_members is None:
            self._inheritance_in_members = {}
        else:
            self._inheritance_in_members = inheritance_in_members

        # self._build_family_alleles()

    def _build_family_alleles(self):
        assert self._family_alleles is None

        summary_allele = self.summary_variant.alleles[0]
        alleles = [
            FamilyAllele(
                summary_allele,
                self.family,
                self.gt,
                self._best_state,
                inheritance_in_members=self._inheritance_in_members.get(0)
            )
        ]

        for ai in self.calc_alt_alleles(self.gt):
            summary_allele = None
            for allele in self.summary_variant.alt_alleles:
                if allele.allele_index == ai:
                    summary_allele = allele
                    break
            if summary_allele is None:
                continue

            inheritance = self._inheritance_in_members.get(ai)

            allele = FamilyAllele(
                summary_allele,
                self.family,
                self.gt,
                self._best_state,
                inheritance_in_members=inheritance
            )

            alleles.append(allele)

        self._family_alleles = alleles

    @property
    def fvuid(self) -> Optional[str]:
        if self._fvuid is None:
            self._fvuid = f"{self.family_id}.{self.location}" \
                f".{self.reference}.{self.alternative}"
        return self._fvuid

    @property
    def chromosome(self):
        return self.summary_variant.chromosome

    @property
    def chrom(self):
        return self.summary_variant.chromosome

    @property
    def position(self):
        return self.summary_variant.position

    @property
    def reference(self):
        return self.summary_variant.reference

    # @property
    # def alternative(self) -> Optional[str]:
    #     return self.summary_variant.alternative

    @property
    def end_position(self) -> Optional[int]:
        return self.summary_variant.end_position

    @property
    def allele_count(self):
        return self.summary_variant.allele_count

    @property
    def summary_index(self):
        return self.summary_variant.summary_index

    @summary_index.setter
    def summary_index(self, summary_index):
        self.summary_variant.summary_index = summary_index

    @property
    def family_index(self):
        return self.ref_allele.family_index

    @family_index.setter
    def family_index(self, val):
        for allele in self.alleles:
            allele.family_index = val

    @property
    def allele_indexes(self):
        return [a.allele_index for a in self.alleles]

    @property
    def family_allele_indexes(self):
        return list(range(len(self.alleles)))

    @property
    def alleles(self):
        if self._family_alleles is None:
            self._build_family_alleles()

        return self._family_alleles

    def gt_flatten(self):
        """
        Return genotype of the family variant flattened to 1-dimensional
        array.
        """
        return self.gt.flatten(order="F")

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
        output = SummaryVariant.__repr__(self)
        return f"{output} {self.family_id} {mat2str(self.gt)}"

    @property
    def genotype(self):
        """
        Returns genotype using summary variant allele indexes.
        """
        return [list(self.gt[:, m]) for m in range(self.gt.shape[1])]

    @property
    def family_genotype(self):
        """
        Returns family genotype using family variant indexes.
        """
        gt2fgt = zip(self.allele_indexes, self.family_allele_indexes)
        fgt = np.zeros(shape=self.gt.shape, dtype=np.int8)
        for gi, fgi in gt2fgt:
            fgt[self.gt == gi] = fgi

        return [list(fgt[:, m]) for m in range(fgt.shape[1])]

    @property
    def genetic_model(self):
        if self._genetic_model is None:
            self._genetic_model = GeneticModel.autosomal
        return self._genetic_model

    @property
    def best_state(self):
        if self._best_state is None:
            self._best_state = calculate_simple_best_state(
                self.gt, self.allele_count
            )
        return self._best_state

    @property
    def family_best_state(self):
        return self.best_state[self.allele_indexes, :]

    @property  # type: ignore
    @deprecated(details="Replace usage of `best_st` with `best_state`")
    def best_st(self):
        return self.best_state

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

    @property
    def variant_in_members(self):
        members = set()
        for a in self.alt_alleles:
            members = members.union(filter(None, a.variant_in_members))
        return members

    @property
    def to_record(self):
        return {
            "family_id": self.family_id,
            "summary_index": self.summary_index,
            "family_index": self.family_index,
            "genotype": self.gt.tolist(),
            "best_state": self.best_state.tolist()
        }
