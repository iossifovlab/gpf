from abc import abstractproperty
from typing import List, Dict, Set, Any, Optional

from dae.variants.variant import Allele, Variant
from dae.variants.family_variant import FamilyVariant


class RemoteBaseVariant(Variant):

    def __init__(self, columns: List[str], attributes_list: list):
        # columns is an ordered list of columns by their source name
        self.columns = columns
        self.attributes_list = attributes_list

    def _find_attribute(self, source: str):
        if source not in self.columns:
            return None
        return self.attributes_list[self.columns.index(source)]

    @property
    def chrom(self) -> str:
        return self._find_attribute("chromosome")

    @property
    def chromosome(self) -> str:
        return self.chrom

    @property
    def position(self) -> int:
        return self._find_attribute("position")

    @property
    def end_position(self) -> Optional[int]:
        return self._find_attribute("end_position")

    @property
    def reference(self) -> str:
        return self._find_attribute("reference")

    @property
    def alternative(self) -> Optional[str]:
        return self._find_attribute("alternative")

    @property
    def allele_count(self) -> int:
        return self._find_attribute("allele_count")

    @property
    def summary_index(self) -> int:
        return self._find_attribute("summary_index")

    @property
    def alleles(self) -> List[Allele]:
        """
        list of all alleles of the variant
        """
        pass

    @property
    def ref_allele(self) -> Allele:
        """
        the reference allele
        """
        return self.alleles[0]

    @property
    def alt_alleles(self) -> List[Allele]:
        """list of all alternative alleles"""
        return self.alleles[1:]

    @property
    def details(self) -> List[Allele]:
        """
        list of `VariantDetails`, that describe each
        alternative allele.
        """
        if not self.alt_alleles:
            return []
        return [sa.details for sa in self.alt_alleles]

    @property
    def cshl_variant(self) -> List[Optional[str]]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_variant for aa in self.alt_alleles]

    @property
    def cshl_variant_full(self) -> List[Optional[str]]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_variant_full for aa in self.alt_alleles]

    @property
    def cshl_location(self) -> Optional[str]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_location for aa in self.alt_alleles]

    @property
    def effects(self) -> List[str]:
        """
        1-based list of `Effect`, that describes variant effects.
        """
        if not self.alt_alleles:
            return []
        return [sa.effect for sa in self.alt_alleles]

    @property
    def effect_types(self) -> List[str]:
        ets = set()
        for a in self.alt_alleles:
            ets = ets.union(a.effect_types)
        return list(ets)

    @property
    def effect_gene_symbols(self):
        egs = set()
        for a in self.alt_alleles:
            egs = egs.union(a.effect_gene_symbols)
        return list(egs)

    @property
    def frequencies(self) -> List[Optional[float]]:
        """
        0-base list of frequencies for variant.
        """
        return [sa.frequency for sa in self.alleles]

    @property
    def variant_types(self) -> Set[Any]:
        """
        returns set of variant types.
        """
        return set([aa.variant_type for aa in self.alt_alleles])

    def get_attribute(
            self, item: Any, default: Optional[Any] = None) -> List[Any]:
        return [sa.get_attribute(item, default) for sa in self.alt_alleles]

    def has_attribute(self, item: Any) -> bool:
        return any([sa.has_attribute(item) for sa in self.alt_alleles])

    def __getitem__(self, item: Any) -> List[Any]:
        return self.get_attribute(item)

    def __contains__(self, item: Any) -> bool:
        return self.has_attribute(item)

    def update_attributes(self, atts: Dict[str, Any]) -> None:
        # FIXME:
        for key, values in list(atts.items()):
            assert len(values) == 1 or len(values) == len(self.alt_alleles)
            for sa, val in zip(self.alt_alleles, itertools.cycle(values)):
                sa.update_attributes({key: val})

    @property
    def _variant_repr(self) -> str:
        if self.alternative:
            return "{}->{}".format(self.reference, self.alternative)
        else:
            return "{} (ref)".format(self.reference)

    def __repr__(self):
        types = self.variant_types
        if VariantType.cnv_m in types or VariantType.cnv_p in types:
            types_str = ", ".join(map(str, types))
            return f"{self.location} {types_str}"
        else:
            return f"{self.location} {self._variant_repr}"

    def __eq__(self, other):
        return (
            self.chromosome == other.chromosome
            and self.position == other.position
            and self.reference == other.reference
            and self.alternative == other.alternative
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return (
            self.chromosome <= other.chromosome
            and self.position < other.position
        )

    def __gt__(self, other):
        return (
            self.chromosome >= other.chromosome
            and self.position > other.position
        )


class RemoteVariant(RemoteBaseVariant, FamilyVariant):
    pass
