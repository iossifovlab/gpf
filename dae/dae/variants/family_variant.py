import copy
import logging
from typing import Any, List, Optional, cast

import numpy as np
from deprecation import deprecated

from dae.effect_annotation.effect import AlleleEffects
from dae.pedigrees.family import Family, Person
from dae.utils.variant_utils import (
    GenotypeType,
    is_all_unknown_genotype,
    is_reference_genotype,
    mat2str,
)
from dae.variants.attributes import (
    GeneticModel,
    Inheritance,
    Role,
    Sex,
    Status,
    TransmissionType,
)
from dae.variants.core import Allele
from dae.variants.variant import SummaryAllele, SummaryVariant, VariantDetails

logger = logging.getLogger(__name__)


def calculate_simple_best_state(
        genotype: np.ndarray, allele_count: int) -> np.ndarray:
    """Calculate and return the best state of a genotype."""
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

    best_st_arr = cast(np.ndarray, np.stack(best_st, axis=0))
    best_st_arr[:, unknown] = -1

    return best_st_arr


class FamilyDelegate:
    """Delegate for handling families."""

    def __init__(self, family: Family):
        self.family = family

    @property
    def members_in_order(self) -> list[Person]:
        """
        Return the members from the pedigree file in order.

        Return list of the members of the family in the order specified from
        the pedigree file. Each element of the returned list is an object of
        type :class:`variants.family.Person`.
        """
        return self.family.members_in_order

    @property
    def members_ids(self) -> list[str]:
        """Return list of family members IDs."""
        return self.family.members_ids

    @property
    def members_fpids(self) -> list[tuple[str, str]]:
        """Return list of family members IDs."""
        return [m.fpid for m in self.family.members_in_order]

    @property
    def family_id(self) -> str:
        """Return the family ID."""
        return self.family.family_id


class FamilyAllele(SummaryAllele, FamilyDelegate):
    # pylint: disable=super-init-not-called,too-many-public-methods
    """Class representing an allele in a family."""

    def __init__(
        self,
        summary_allele: SummaryAllele,
        family: Family,
        genotype: Optional[np.ndarray],
        best_state: Optional[np.ndarray],
        genetic_model: Optional[GeneticModel] = None,
        inheritance_in_members: Optional[list[Inheritance]] = None,
    ):

        assert isinstance(family, Family)

        FamilyDelegate.__init__(self, family)

        #: summary allele that corresponds to this allele in family variant
        self.summary_allele: SummaryAllele = summary_allele

        self.gt = genotype

        # assert self.gt.dtype == GenotypeType, (self.gt, self.gt.dtype)
        self._best_state = best_state
        if genetic_model is None:
            self._genetic_model = GeneticModel.autosomal
        else:
            self._genetic_model = genetic_model

        self._inheritance_in_members = inheritance_in_members
        self._variant_in_members: Optional[list[str]] = None
        self._variant_in_members_objects: Optional[list[Person]] = None
        self._variant_in_roles: Optional[list[Optional[Role]]] = None
        self._variant_in_sexes: Optional[list[Optional[Sex]]] = None
        self._variant_in_statuses: Optional[list[Optional[Status]]] = None
        self._family_index: Optional[int] = None
        self._family_attributes: dict = {}

        self.matched_gene_effects: List = []

    def __repr__(self) -> str:
        allele_repr = SummaryAllele.__repr__(self)
        return f"{allele_repr} {self.family_id}"

    @property
    def chromosome(self) -> str:
        return self.summary_allele.chromosome

    @property
    def chrom(self) -> str:
        return self.summary_allele.chromosome

    @property
    def position(self) -> int:
        return self.summary_allele.position

    @property
    def reference(self) -> Optional[str]:
        return self.summary_allele.reference

    @property
    def alternative(self) -> Optional[str]:
        return self.summary_allele.alternative

    @property
    def summary_index(self) -> int:
        return self.summary_allele.summary_index

    @summary_index.setter
    def summary_index(self, val: int) -> None:
        self.summary_allele.summary_index = val

    @property
    def family_index(self) -> Optional[int]:
        return self._family_index

    @family_index.setter
    def family_index(self, val: int) -> None:
        self._family_index = val

    @property
    def allele_index(self) -> int:
        return self.summary_allele.allele_index

    @property
    def transmission_type(self) -> TransmissionType:
        return self.summary_allele.transmission_type

    @property
    def summary_attributes(self) -> dict[str, Any]:
        return self.summary_allele.attributes

    @property
    def family_attributes(self) -> dict[str, Any]:
        return self._family_attributes

    @property
    def attributes(self) -> dict[str, Any]:
        result = copy.deepcopy(self.summary_attributes)
        result.update(self.family_attributes)
        return result

    def get_attribute(self, item: str, default_val: Any = None) -> Any:
        """
        Return list of values from additional attributes matching given key.

        looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.family_attributes.get(item)
        if val is not None:
            return val
        val = self.summary_allele.get_attribute(item, default_val)
        if val is None:
            return default_val
        return val

    def has_attribute(self, item: str) -> bool:
        """Check if the additional variant attributes contain a given key."""
        return item in self.family_attributes or \
            item in self.summary_attributes

    def update_attributes(self, atts: dict[str, Any]) -> None:
        """Update additional attributes of the variant."""
        self._family_attributes.update(atts)

    @property
    def details(self) -> VariantDetails:
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
    def genotype(self) -> np.ndarray:
        """Return the genotype of the family."""
        assert self.gt is not None
        return self.gt.T

    @property
    def best_state(self) -> np.ndarray:
        """Return the best state of the variant."""
        if self._best_state is None:
            assert self.gt is not None
            self._best_state = calculate_simple_best_state(
                self.gt, self.attributes["allele_count"],
            )
        return self._best_state

    @property
    @deprecated(details="Replace `best_st` with `best_state`")
    def best_st(self) -> np.ndarray:
        return self.best_state

    @property
    def genetic_model(self) -> Optional[GeneticModel]:
        return self._genetic_model

    def gt_flatten(self) -> np.ndarray:
        """Return the family variant genotype flattened to a 1d array."""
        assert self.gt is not None
        return self.gt.flatten(order="F")

    @property
    def inheritance_in_members(self) -> list[Inheritance]:
        """Return list of family member inheritance."""
        if self._inheritance_in_members is None:
            assert self.gt is not None
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
                    child = trio_gt[:, 0]
                    parent_1 = trio_gt[:, 1]
                    parent_2 = trio_gt[:, 2]
                    inh = self.calc_inheritance_trio(
                        parent_1, parent_2, child, allele_index,
                    )
                    if inh != Inheritance.omission and np.all(
                        child != allele_index,
                    ):
                        inh = Inheritance.missing
                result.append(inh)
            self._inheritance_in_members = result
        return self._inheritance_in_members

    @property
    def variant_in_members(self) -> list[str]:
        """Return set of affected by this variant family members' IDs."""
        if self._variant_in_members is None:
            assert self.gt is not None
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
    def allele_in_members(self) -> list[str]:
        return self.variant_in_members

    @property
    def variant_in_members_objects(self) -> list[Person]:
        """Return list of person with the variant."""
        if self._variant_in_members_objects is None:

            variant_in_members = set(filter(None, self.variant_in_members))
            self._variant_in_members_objects = [
                member
                for member in self.family.members_in_order
                if member.person_id in variant_in_members
            ]
        return self._variant_in_members_objects

    @property
    def variant_in_members_fpid(self) -> list[tuple[str, str]]:
        """Return list of person with the variant."""
        return [p.fpid for p in self.variant_in_members_objects]

    @property
    def variant_in_roles(self) -> list[Optional[Role]]:
        """
        Return list of roles that have affected by this variant members.

        Returns None if none found.
        """
        if self._variant_in_roles is None:
            self._variant_in_roles = [
                self.family.persons[pid].role if pid is not None else None
                for pid in self.variant_in_members
            ]
        return self._variant_in_roles

    @property
    def allele_in_roles(self) -> list[Optional[Role]]:
        return self.variant_in_roles

    @property
    def variant_in_statuses(self) -> list[Optional[Status]]:
        """Return list of statuses (or 'None') of the members with variant."""
        if self._variant_in_statuses is None:
            self._variant_in_statuses = [
                self.family.persons[pid].status if pid is not None else None
                for pid in self.variant_in_members
            ]
        return self._variant_in_statuses

    @property
    def allele_in_statuses(self) -> list[Optional[Status]]:
        return self.variant_in_statuses

    @property
    def variant_in_sexes(self) -> list[Optional[Sex]]:
        """Return list of sexes that are affected by this variant in family."""
        if self._variant_in_sexes is None:
            self._variant_in_sexes = [
                self.family.persons[pid].sex if pid is not None else None
                for pid in self.variant_in_members
            ]
        return self._variant_in_sexes

    @property
    def allele_in_sexes(self) -> list[Optional[Sex]]:
        return self.variant_in_sexes

    @staticmethod
    def check_mendelian_trio(
            parent_1: np.ndarray, parent_2: np.ndarray,
            child: np.ndarray, allele_index: int) -> bool:
        """Check if the inheritance type for a trio family is `mendelian`.

        :param parent_1: genotype of the first parent (pair of allele indexes).
        :param parent_2: genotype of the second parent.
        :param child: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        # pylint: disable=invalid-name
        ai = allele_index
        if ai not in set(child):
            return False

        m1: bool = (
            child[0] == parent_1[0] == ai or child[0] == parent_1[1] == ai
        ) or (
            child[1] == parent_2[0] == ai or child[1] == parent_2[1] == ai
        )

        m2: bool = (
            child[0] == parent_2[0] == ai or child[0] == parent_2[1] == ai
        ) or (
            child[1] == parent_1[0] == ai or child[1] == parent_1[1] == ai
        )

        return m1 or m2

    @staticmethod
    def check_denovo_trio(
            parent_1: np.ndarray, parent_2: np.ndarray,
            child: np.ndarray, allele_index: int) -> bool:
        """
        Check if the inheritance type for a trio family is `denovo`.

        :param parent_1: genotype of the first parent (pair of allele indexes).
        :param parent_2: genotype of the second parent.
        :param child: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        new_alleles = set(child).difference(set(parent_1) | set(parent_2))
        return allele_index in new_alleles

    @staticmethod
    def check_omission_trio(
            parent_1: np.ndarray, parent_2: np.ndarray,
            child: np.ndarray, allele_index: int) -> bool:
        """Check if the inheritance type for a trio family is `omission`.

        :param parent_1: genotype of the first parent (pair of allele indexes).
        :param parent_2: genotype of the second parent.
        :param child: genotype of the child.
        :return: True, when the inheritance is mendelian.
        """
        if allele_index not in set(parent_1) | set(parent_2):
            return False

        child_alleles = set(child)
        if allele_index in child_alleles:
            return False

        p1res = False
        p2res = False

        if parent_1[0] == parent_1[1] == allele_index:
            p1res = not bool(parent_1[0] in child_alleles)
        if parent_2[0] == parent_2[1] == allele_index:
            p2res = not bool(parent_2[0] in child_alleles)

        return p1res or p2res

    @classmethod
    def calc_inheritance_trio(
            cls, parent_1: np.ndarray, parent_2: np.ndarray,
            child: np.ndarray, allele_index: int) -> Inheritance:
        """Calculate the inheritance type of a trio family.

        :param parent_1: genotype of the first parent (pair of allele indexes).
        :param parent_2: genotype of the second parent.
        :param child: genotype of the child.
        :return: inheritance type as :class:`variants.attributes.Inheritance`
            of the trio family.
        """
        if cls.check_mendelian_trio(parent_1, parent_2, child, allele_index):
            return Inheritance.mendelian
        if cls.check_denovo_trio(parent_1, parent_2, child, allele_index):
            return Inheritance.denovo
        if cls.check_omission_trio(parent_1, parent_2, child, allele_index):
            return Inheritance.omission
        return Inheritance.other


class FamilyVariant(SummaryVariant, FamilyDelegate):
    # pylint: disable=super-init-not-called,too-many-public-methods
    """Class representing a variant in a family."""

    def __init__(
        self,
        summary_variant: SummaryVariant,
        family: Family,
        genotype: Optional[np.ndarray],
        best_state: Optional[np.ndarray],
        inheritance_in_members: Optional[dict[int, list[Inheritance]]] = None,
    ):

        # super(FamilyVariant, self).__init__()

        assert family is not None
        assert isinstance(family, Family)
        FamilyDelegate.__init__(self, family)

        self.summary_variant = summary_variant
        self.summary_alleles = self.summary_variant.alleles
        self.gt = genotype
        self._genetic_model: Optional[GeneticModel] = None

        self._family_alleles: Optional[List[FamilyAllele]] = None
        self._best_state = best_state

        self._fvuid: Optional[str] = None
        if inheritance_in_members is None:
            self._inheritance_in_members = {}
        else:
            self._inheritance_in_members = inheritance_in_members

    def _build_family_alleles(self) -> None:
        assert self._family_alleles is None
        alleles = [
            FamilyAllele(
                self.summary_variant.alleles[0],
                self.family,
                self.gt,
                self._best_state,
                inheritance_in_members=self._inheritance_in_members.get(0),
            ),
        ]
        # pylint: disable=invalid-name
        assert self.gt is not None
        for ai in self.calc_alt_alleles(self.gt):
            summary_allele: Optional[SummaryAllele] = None
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
                inheritance_in_members=inheritance,
            )

            alleles.append(allele)

        self._family_alleles = alleles

    @property
    def fvuid(self) -> str:
        if self._fvuid is None:
            self._fvuid = f"{self.family_id}.{self.location}" \
                f".{self.reference}.{self.alternative}"
        return self._fvuid

    @property
    def chromosome(self) -> str:
        return self.summary_variant.chromosome

    @property
    def chrom(self) -> str:
        return self.summary_variant.chromosome

    @property
    def position(self) -> int:
        return self.summary_variant.position

    @property
    def reference(self) -> Optional[str]:
        return self.summary_variant.reference

    # @property
    # def alternative(self) -> Optional[str]:
    #     return self.summary_variant.alternative

    @property
    def end_position(self) -> Optional[int]:
        return self.summary_variant.end_position

    @property
    def allele_count(self) -> int:
        return self.summary_variant.allele_count

    @property
    def summary_index(self) -> int:
        return self.summary_variant.summary_index

    @summary_index.setter
    def summary_index(self, summary_index: int) -> None:
        self.summary_variant.summary_index = summary_index

    @property
    def family_index(self) -> Optional[int]:
        return cast(FamilyAllele, self.ref_allele).family_index

    @family_index.setter
    def family_index(self, val: int) -> None:
        for allele in self.family_alleles:
            allele.family_index = val

    @property
    def allele_indexes(self) -> list[int]:
        return [a.allele_index for a in self.alleles]

    @property
    def family_allele_indexes(self) -> list[int]:
        return list(range(len(self.alleles)))

    @property
    def alleles(self) -> list[SummaryAllele]:
        if self._family_alleles is None:
            self._build_family_alleles()
        assert self._family_alleles is not None
        return cast(list[SummaryAllele], self._family_alleles)

    @property
    def family_alleles(self) -> list[FamilyAllele]:
        if self._family_alleles is None:
            self._build_family_alleles()
        return cast(list[FamilyAllele], self._family_alleles)

    @property
    def family_alt_alleles(self) -> List[FamilyAllele]:
        return self.family_alleles[1:]

    def gt_flatten(self) -> np.ndarray:
        """Return genotype of the family variant flattened to a 1d array."""
        assert self.gt is not None
        return self.gt.flatten(order="F")

    def is_reference(self) -> bool:
        """Return True if all known alleles in the variant are `reference`."""
        assert self.gt is not None
        return is_reference_genotype(self.gt)

    def is_unknown(self) -> bool:
        """Return True if all alleles in the variant are `unknown`."""
        assert self.gt is not None
        return is_all_unknown_genotype(self.gt)

    def __repr__(self) -> str:
        assert self.gt is not None
        output = SummaryVariant.__repr__(self)
        return f"{output} {self.family_id} {mat2str(self.gt)}"

    @property
    def genotype(self) -> list[list[int]]:
        """Return genotype using summary variant allele indexes."""
        assert self.gt is not None
        return [list(self.gt[:, m]) for m in range(self.gt.shape[1])]

    @property
    def family_genotype(self) -> list[list[int]]:
        """Return family genotype using family variant indexes."""
        assert self.gt is not None
        gt2fgt = zip(self.allele_indexes, self.family_allele_indexes)
        fgt = np.zeros(shape=self.gt.shape, dtype=np.int8)
        # pylint: disable=invalid-name
        for gi, fgi in gt2fgt:
            fgt[self.gt == gi] = fgi

        return [list(fgt[:, m]) for m in range(fgt.shape[1])]

    @property
    def genetic_model(self) -> GeneticModel:
        if self._genetic_model is None:
            self._genetic_model = GeneticModel.autosomal
        assert self._genetic_model is not None
        return self._genetic_model

    @property
    def best_state(self) -> np.ndarray:
        """Return best state of the variant."""
        if self._best_state is None:
            assert self.gt is not None
            self._best_state = calculate_simple_best_state(
                self.gt, self.allele_count,
            )
        assert self._best_state is not None
        return self._best_state

    @property
    def family_best_state(self) -> np.ndarray:
        return self.best_state[self.allele_indexes, :]

    @property  # type: ignore
    @deprecated(details="Replace usage of `best_st` with `best_state`")
    def best_st(self):
        return self.best_state

    @staticmethod
    def calc_alt_alleles(gt: np.ndarray) -> list[int]:
        """
        Return relevant for the given genotype alternative allele indexes.

        :param gt: genotype as `np.array`.
        :return: list of all alternative allele indexes present into
                 genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({0})))

    @staticmethod
    def calc_alleles(gt: np.ndarray) -> list[int]:
        """
        Return allele indexes that are relevant for the given genotype.

        :param gt: genotype as `np.array`.
        :return: list of all allele indexes present into genotype passed.
        """
        return sorted(list(set(gt.flatten()).difference({-1})))

    @property
    def variant_in_members(self) -> set[str]:
        """Return list of members with the variant."""
        members: set[str] = set()
        for allele in self.alt_alleles:
            members = members.union(filter(
                None,
                cast(FamilyAllele, allele).variant_in_members))
        return members

    def _serialize_inheritance_in_members(
        self,
    ) -> dict[int, list[int]]:
        result = {}
        for allele in self.family_alleles:
            result[allele.allele_index] = [
                inh.value for inh in allele.inheritance_in_members]
        return result

    def to_record(self) -> dict[str, Any]:  # type: ignore
        assert self.gt is not None
        return {
            "family_id": self.family_id,
            "summary_index": self.summary_index,
            "family_index": self.family_index,
            "genotype": self.gt.tolist(),
            "best_state": self.best_state.tolist(),
            "inheritance_in_members": self._serialize_inheritance_in_members(),
        }
