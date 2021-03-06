"""
Created on Feb 13, 2018

@author: lubo
"""
from dae.utils.variant_utils import vcf2cshl

from dae.variants.attributes import VariantType, TransmissionType
from typing import List, Dict, Set, Any, Optional
from dae.variants.effects import Effect, EffectGene
import itertools


class AltAlleleItems:
    """
    1-based list for representing list of items relevant to the list
    of alternative alleles.
    """

    def __init__(self, items, alt_alleles=None):
        if not hasattr(items, "__iter__"):
            items = [items]

        if alt_alleles is None:
            self.items = items
            self.alt_alleles = list(range(1, len(self.items) + 1))
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
            return slice(
                self._to_zero_based(index.start),
                self._to_zero_based(index.stop),
                index.step,
            )
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
            return [self.items[i] for i in range(*index.indices(self.size))]
        raise TypeError("bad allele index type: {}".format(index))

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return self.size

    def __repr__(self):
        return self.items.__repr__()

    def __str__(self):
        return str(self.items)

    def __eq__(self, other):
        return len(self.items) == len(other.items) and all(
            [s == o for (s, o) in zip(self.items, other.items)]
        )


class VariantDetail:
    def __init__(self, chrom: str, position, variant, length):
        self.length = length
        self.type = None
        self.chrom = chrom
        self.cshl_position = position
        self.cshl_variant = variant
        self._variant_type = None

    def __repr__(self):
        return "{} {}".format(self.cshl_location, self.cshl_variant)

    @property
    def cshl_location(self):
        return "{}:{}".format(self.chrom, self.cshl_position)

    @property
    def variant_type(self):
        if self._variant_type is None:
            self._variant_type = VariantType.from_cshl_variant(
                self.cshl_variant
            )
        return self._variant_type

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        return VariantDetail(
            chrom, *vcf2cshl(position, reference, alternative)
        )


class Allele:
    @property
    def chromosome(self) -> str:
        raise NotImplementedError()

    @property
    def chrom(self) -> str:
        return self.chromosome

    @property
    def position(self) -> int:
        raise NotImplementedError()

    @property
    def end_position(self) -> Optional[int]:
        raise NotImplementedError()

    @property
    def reference(self) -> str:
        raise NotImplementedError()

    @property
    def alternative(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def summary_index(self) -> int:
        """
        index of the summary variant this allele belongs to
        """
        raise NotImplementedError()

    @property
    def allele_index(self) -> int:
        """
        index of the allele in summary variant
        """
        raise NotImplementedError()

    @property
    def transmission_type(self) -> TransmissionType:
        raise NotImplementedError()

    @property
    def attributes(self) -> Dict[str, Any]:
        """
        additional attributes of the allele
        """
        raise NotImplementedError()

    @property
    def effect(self) -> Optional[Effect]:
        """
        effects of the allele; None for the reference allele.
        """
        raise NotImplementedError()

    @property
    def effects(self) -> Optional[Effect]:
        return self.effect

    @property
    def effect_types(self) -> List[str]:
        if self.effect:
            return self.effect.types
        else:
            return []

    @property
    def effect_genes(self) -> List[EffectGene]:
        if self.effect:
            return self.effect.genes
        else:
            return []

    @property
    def effect_gene_symbols(self) -> List[str]:
        return [eg.symbol for eg in self.effect_genes]

    @property
    def variant_type(self) -> Optional[VariantType]:
        raise NotImplementedError()

    @property
    def frequency(self) -> Optional[float]:
        return self.attributes.get("af_allele_freq")

    @property
    def details(self) -> Optional[VariantDetail]:
        raise NotImplementedError()

    @property
    def cshl_variant(self) -> Optional[str]:
        if self.end_position and self.end_position != -1:
            return str(self.variant_type)
        if self.alternative is None:
            return None
        if self.details is None:
            return None
        return self.details.cshl_variant  # type: ignore

    @property
    def cshl_location(self) -> Optional[str]:
        if self.end_position and self.end_position != -1:
            return f"{self.chrom}:{self.position}-{self.end_position}"
        if self.alternative is None:
            return None
        if self.details is None:
            return None
        return self.details.cshl_location  # type: ignore

    @property
    def cshl_position(self) -> Optional[str]:
        if self.alternative is None:
            return None
        if self.details is None:
            return None
        return self.details.cshl_position  # type: ignore

    @property
    def is_reference_allele(self) -> bool:
        return self.allele_index == 0

    def get_attribute(self, item: str, default=None):
        """
        looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.attributes.get(item, default)
        return val

    def has_attribute(self, item: str) -> bool:
        """
        checks if additional variant attributes contain values for key `item`.
        """
        return item in self.attributes

    def update_attributes(self, atts) -> None:
        """
        updates additional attributes of variant using dictionary `atts`.
        """
        for key, val in list(atts.items()):
            self.attributes[key] = val

    def __getitem__(self, item):
        """
        allows using of standard dictionary access to additional variant
        attributes. For example `sv['af_parents_called']` will return value
        matching key `af_parents_called` from addtional variant attributes.
        """
        return self.attributes.get(item)

    def __contains__(self, item) -> bool:
        """
        checks if additional variant attributes contain value for key `item`.
        """
        return item in self.attributes

    def __repr__(self) -> str:
        if VariantType.is_cnv(self.variant_type):
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        elif not self.alternative:
            return f"{self.chrom}:{self.position} {self.reference}(ref)"
        else:
            return (
                f"{self.chrom}:{self.position}"
                f" {self.reference}->{self.alternative}"
            )


class Variant:
    @property
    def chrom(self) -> str:
        return self.chromosome

    @property
    def chromosome(self) -> str:
        raise NotImplementedError()

    @property
    def position(self) -> int:
        raise NotImplementedError()

    @property
    def end_position(self) -> Optional[int]:
        raise NotImplementedError()

    @property
    def reference(self) -> str:
        raise NotImplementedError()

    @property
    def alternative(self) -> Optional[str]:
        if not self.alt_alleles:
            return None
        # if any([aa.alternative is None for aa in self.alt_alleles]):
        #     assert all([aa.alternative is None for aa in self.alt_alleles])
        #     return None
        return ",".join(
            [
                aa.alternative if aa.alternative else ""
                for aa in self.alt_alleles
            ]
        )

    @property
    def allele_count(self) -> int:
        raise NotImplementedError()

    @property
    def location(self) -> str:
        if self.end_position and self.end_position != -1:
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        else:
            return f"{self.chromosome}:{self.position}"

    @property
    def summary_index(self) -> int:
        raise NotImplementedError()

    @property
    def alleles(self) -> List[Allele]:
        """
        list of all alleles of the variant
        """
        raise NotImplementedError()

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
    def details(self) -> Optional[AltAlleleItems]:
        """
        1-based list of `VariantDetails`, that describes each
        alternative allele.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.details for sa in self.alt_alleles])

    @property
    def effects(self) -> Optional[AltAlleleItems]:
        """
        1-based list of `Effect`, that describes variant effects.
        """
        if not self.alt_alleles:
            return None
        return AltAlleleItems([sa.effect for sa in self.alt_alleles])

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
        self, item: Any, default: Optional[Any] = None
    ) -> List[Any]:
        return [sa.get_attribute(item, default) for sa in self.alleles]

    def has_attribute(self, item: Any) -> bool:
        return any([sa.has_attribute(item) for sa in self.alleles])

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


class SummaryAllele(Allele):
    """
    `SummaryAllele` represents a single allele for given position.
    """

    def __init__(
        self,
        chromosome: str,
        position: int,
        reference: str,
        alternative: Optional[str] = None,
        end_position: Optional[int] = None,
        summary_index: int = -1,
        allele_index: int = 0,
        transmission_type: TransmissionType = TransmissionType.transmitted,
        variant_type=None,
        attributes: Dict[str, Any] = None,
    ):

        self._chromosome: str = chromosome
        self._position: int = position
        self._end_position: Optional[int] = end_position
        self._reference: str = reference
        self._alternative: Optional[str] = alternative

        self._summary_index: int = summary_index
        self._allele_index: int = allele_index
        self._transmission_type: TransmissionType = transmission_type
        self._variant_type = variant_type

        self._details = None

        self._effect = None

        self._attributes: Dict[str, Any] = {
            "allele_index": allele_index,
            "transmission_type": transmission_type
        }
        if attributes is not None:
            self.update_attributes(attributes)

    @property
    def variant_type(self):
        if self._variant_type is None and self.details:
            self._variant_type = VariantType.from_cshl_variant(
                self.details.cshl_variant
            )
        return self._variant_type

    @property
    def chromosome(self) -> str:
        return self._chromosome

    @property
    def position(self) -> int:
        return self._position

    @property
    def end_position(self) -> Optional[int]:
        return self._end_position

    @property
    def reference(self) -> str:
        return self._reference

    @property
    def alternative(self) -> Optional[str]:
        return self._alternative

    @property
    def summary_index(self) -> int:
        return self._summary_index

    @summary_index.setter
    def summary_index(self, summary_index):
        self._summary_index = summary_index

    @property
    def allele_index(self) -> int:
        return self._allele_index

    @property
    def transmission_type(self) -> TransmissionType:
        return self._transmission_type

    @property
    def attributes(self) -> Dict[str, Any]:
        return self._attributes

    @property
    def details(self) -> Optional[VariantDetail]:
        if self.alternative is None:
            return None
        if self._details is None:
            self._details = VariantDetail.from_vcf(
                self.chromosome,
                self.position,
                self.reference,
                self.alternative,
            )
        return self._details

    @property
    def effect(self) -> Optional[Effect]:
        if self._effect is None:
            record = self.attributes
            if "effect_type" in record:
                worst_effect = record["effect_type"]
                if worst_effect is None:
                    return None
                effects = Effect.from_effects(
                    worst_effect,
                    list(
                        zip(
                            record["effect_gene_genes"],
                            record["effect_gene_types"],
                        )
                    ),
                    list(
                        zip(
                            record["effect_details_transcript_ids"],
                            record["effect_details_details"],
                        )
                    ),
                )
                self._effect = effects
            elif "effects" in record:
                self._effect = Effect.from_string(record.get("effects"))
            else:
                self._effect = None
        return self._effect

    @staticmethod
    def create_reference_allele(allele) -> Allele:
        new_attributes = {
            "chrom": allele.attributes.get("chrom"),
            "position": allele.attributes.get("position"),
            "reference": allele.attributes.get("reference"),
            "summary_variant_index": allele.attributes.get(
                "summary_variant_index"),
            "allele_count": allele.attributes.get("allele_count"),
        }

        return SummaryAllele(
            allele.chromosome,
            allele.position,
            allele.reference,
            summary_index=allele.summary_index,
            transmission_type=allele.transmission_type,
            attributes=new_attributes,
        )


class SummaryVariant(Variant):
    def __init__(self, alleles):
        assert len(alleles) >= 1
        assert len(set([sa.position for sa in alleles])) == 1

        assert alleles[0].is_reference_allele
        self._alleles: List[Allele] = alleles
        self._allele_count: int = len(self.alleles)

        self._chromosome: str = self.ref_allele.chromosome
        self._position: int = self.ref_allele.position
        self._reference: str = self.ref_allele.reference
        if len(alleles) > 1:
            self._end_position = alleles[1].end_position
        else:
            self._end_position = None

        self._svuid: Optional[str] = None

    @property
    def chromosome(self) -> str:
        return self._chromosome

    @property
    def position(self) -> int:
        return self._position

    @property
    def end_position(self) -> Optional[int]:
        return self._end_position

    @property
    def reference(self) -> str:
        return self._reference

    @property
    def allele_count(self) -> int:
        return self._allele_count

    @property
    def summary_index(self):
        return self.ref_allele.summary_index

    @summary_index.setter
    def summary_index(self, val):
        for allele in self.alleles:
            allele.summary_index = val

    @property
    def alleles(self):
        return self._alleles

    @property
    def svuid(self):
        if self._svuid is None:
            self._svuid = \
                f"{self.location}.{self.reference}.{self.alternative}"

        return self._svuid


class SummaryVariantFactory(object):
    @staticmethod
    def summary_allele_from_record(
        record, transmission_type=TransmissionType.transmitted,
        attr_filter=None
    ):
        record["transmission_type"] = transmission_type
        alternative = record["alternative"]
        attributes = record
        if attr_filter:
            attributes = {
                k: v
                for (k, v) in record.items()
                if k not in attr_filter
            }

        if "summary_variant_index" not in record:
            summary_index = record["summary_index"]
        else:
            summary_index = record["summary_variant_index"]

        return SummaryAllele(
            record["chrom"],
            record["position"],
            record["reference"],
            alternative=alternative,
            summary_index=summary_index,
            end_position=record.get("end_position", None),
            variant_type=record.get("variant_type", None),
            allele_index=record["allele_index"],
            transmission_type=transmission_type,
            attributes=attributes,
        )

    @staticmethod
    def summary_variant_from_records(
            records, transmission_type=TransmissionType.transmitted,
            attr_filter=None):

        assert len(records) > 0

        alleles = []
        for record in records:
            sa = SummaryVariantFactory.summary_allele_from_record(
                record, transmission_type, attr_filter
            )
            alleles.append(sa)
        if not alleles[0].is_reference_allele:
            ref_allele = SummaryAllele.create_reference_allele(alleles[0])
            alleles.insert(0, ref_allele)

        allele_count = {"allele_count": len(alleles)}
        for allele in alleles:
            allele.update_attributes(allele_count)

        return SummaryVariant(alleles)

    @staticmethod
    def summary_variant_from_vcf(vcf_variant, summary_variant_index):
        records = []
        allele_count = len(vcf_variant.ALT) + 1
        records.append(
            {
                "chrom": vcf_variant.CHROM,
                "position": vcf_variant.start + 1,
                "reference": vcf_variant.REF,
                "alternative": None,
                "summary_variant_index": summary_variant_index,
                "allele_index": 0,
                "allele_count": allele_count,
            }
        )
        for allele_index, alt in enumerate(vcf_variant.ALT):
            records.append(
                {
                    "chrom": vcf_variant.CHROM,
                    "position": vcf_variant.start + 1,
                    "reference": vcf_variant.REF,
                    "alternative": alt,
                    "summary_variant_index": summary_variant_index,
                    "allele_index": allele_index + 1,
                    "allele_count": allele_count,
                }
            )
        return SummaryVariantFactory.summary_variant_from_records(records)
