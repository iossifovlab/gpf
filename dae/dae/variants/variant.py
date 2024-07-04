"""Classes and helper function to represent variants."""
from __future__ import annotations

import enum
import itertools
import logging
from typing import Any, Callable, cast

import pysam

from dae.effect_annotation.effect import AlleleEffects, EffectGene
from dae.utils.variant_utils import trim_str_left_right, trim_str_right_left
from dae.variants import core
from dae.variants.attributes import TransmissionType

logger = logging.getLogger(__name__)


# pylint: disable=too-many-return-statements
def allele_type_from_name(name: str) -> core.Allele.Type:
    """Return allele type from an allele type name."""
    name = name.lower().strip()
    if name in {"sub", "substitution"}:
        return core.Allele.Type.substitution
    if name in {"ins", "insertion"}:
        return core.Allele.Type.small_insertion
    if name in {"del", "deletion"}:
        return core.Allele.Type.small_deletion
    if name in {"comp", "complex"}:
        return core.Allele.Type.complex
    if name in {"cnv_p", "cnv+", "large_duplication"}:
        return core.Allele.Type.large_duplication
    if name in {"cnv_m", "cnv-", "large_deletion"}:
        return core.Allele.Type.large_deletion
    if name in {"tr", "tandem_repeat"}:
        return core.Allele.Type.tandem_repeat

    raise ValueError(f"unexpected variant type: {name}")


def allele_type_from_cshl_variant(variant: str) -> core.Allele.Type:
    """Return allele type from a CSHL variant type."""
    if variant is None:
        return None

    vt_short = variant[0:2]
    if vt_short == "su":
        return core.Allele.Type.substitution
    if vt_short == "in":
        return core.Allele.Type.small_insertion
    if vt_short == "de":
        return core.Allele.Type.small_deletion
    if vt_short == "co":
        return core.Allele.Type.complex
    if vt_short == "TR":
        return core.Allele.Type.tandem_repeat
    if variant == "CNV+":
        return core.Allele.Type.large_duplication
    if variant == "CNV-":
        return core.Allele.Type.large_duplication
    raise ValueError(f"unexpected variant type: {variant}")


class VariantDesc:
    """Variant description."""

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
            self, variant_type: core.Allele.Type, position: int,
            end_position: int | None = None,
            ref: str | None = None,
            alt: str | None = None,
            length: int | None = None,
            tr_ref: int | None = None,
            tr_alt: int | None = None,
            tr_unit: str | None = None):

        self.variant_type = variant_type
        self.position = position
        self.end_position = end_position

        self.ref = ref
        self.alt = alt
        self.length = length

        self.tr_ref = tr_ref
        self.tr_alt = tr_alt
        self.tr_unit = tr_unit

    def __repr__(self) -> str:
        return self.to_cshl_short()

    def to_cshl_short(self) -> str:
        """Convert variant description into CSHL short type description."""
        if self.variant_type & core.Allele.Type.substitution:
            return f"sub({self.ref}->{self.alt})"
        if self.variant_type & core.Allele.Type.small_insertion:
            return f"ins({self.alt})"
        if self.variant_type & core.Allele.Type.small_deletion:
            return f"del({self.length})"
        if self.variant_type & core.Allele.Type.complex:
            return f"comp({self.ref}->{self.alt})"
        if self.variant_type & core.Allele.Type.large_duplication:
            return "CNV+"
        if self.variant_type & core.Allele.Type.large_deletion:
            return "CNV-"
        raise ValueError(f"unexpected variant type: {self.variant_type}")

    def to_cshl_full(self) -> str:
        """Convert variant description into CSHL full type description.

        Includes tandem repeats descriptions.
        """
        if self.variant_type & core.Allele.Type.tandem_repeat:
            return f"TR({self.tr_ref}x{self.tr_unit}->{self.tr_alt})"
        if self.variant_type & core.Allele.Type.substitution:
            return f"sub({self.ref}->{self.alt})"
        if self.variant_type & core.Allele.Type.small_insertion:
            return f"ins({self.alt})"
        if self.variant_type & core.Allele.Type.small_deletion:
            return f"del({self.length})"
        if self.variant_type & core.Allele.Type.complex:
            return f"comp({self.ref}->{self.alt})"
        if self.variant_type & core.Allele.Type.large_duplication:
            return "CNV+"
        if self.variant_type & core.Allele.Type.large_deletion:
            return "CNV-"
        raise ValueError(f"unexpected variant type: {self.variant_type}")

    @staticmethod
    def combine(variant_descs: list[VariantDesc]) -> list[str]:
        """Combine multiple variant description into list of descriptions."""
        if all(vd.variant_type & core.Allele.Type.tandem_repeat
               for vd in variant_descs):
            tr_ref = variant_descs[0].tr_ref
            tr_alt = ",".join(filter(
                lambda a: a is not None,
                [str(vd.tr_alt) for vd in variant_descs]))
            tr_unit = variant_descs[0].tr_unit
            return [f"TR({tr_ref}x{tr_unit}->{tr_alt})"]

        if all(variant_descs[0].variant_type == vd.variant_type
               for vd in variant_descs):
            result = VariantDesc(
                variant_descs[0].variant_type,
                variant_descs[0].position,
                ref=variant_descs[0].ref,
                alt=",".join(filter(
                    lambda a: a is not None,  # type: ignore
                    [vd.alt for vd in variant_descs])),
                length=variant_descs[-1].length,
            )
            return [result.to_cshl_full()]

        return [str(vd) for vd in variant_descs]


def cshl_format(
    pos: int, ref: str, alt: str,
    trimmer: Callable[
        [int, str, str], tuple[int, str, str]] = trim_str_left_right,
) -> VariantDesc:
    """Build a description for an CSHL allele."""
    # pylint: disable=invalid-name
    p, r, a = trimmer(pos, ref, alt)
    if len(r) == len(a) and len(r) == 0:
        return VariantDesc(
            core.Allele.Type.complex, p, ref=r, alt=a, length=0)

    if len(r) == len(a) and len(r) == 1:
        return VariantDesc(
            core.Allele.Type.substitution, p, ref=r, alt=a, length=1)

    if len(r) > len(a) and len(a) == 0:
        return VariantDesc(
            core.Allele.Type.small_deletion, p, length=len(r),
        )

    # len(ref) < len(alt):
    if len(r) < len(a) and len(r) == 0:
        return VariantDesc(
            core.Allele.Type.small_insertion, p, alt=a, length=len(a))

    return VariantDesc(
        core.Allele.Type.complex, p, ref=r, alt=a, length=max(len(r), len(a)),
    )


def tandem_repeat(
    ref: str, alt: str, min_mono_reference: int = 8,
) -> tuple[str | None, int | None, int | None]:
    """Check if an allele is a tandem repeat and builds it."""
    for period in range(1, len(ref) // 2 + 1):
        if len(ref) % period != 0:
            continue
        unit = ref[:period]

        ref_repeats = len(ref) // period
        if ref_repeats * unit != ref:
            continue

        if len(alt) % period != 0:
            continue
        alt_repeats = len(alt) // period
        if alt_repeats * unit != alt:
            continue

        if len(unit) == 1 and len(ref) < min_mono_reference:
            return None, None, None

        return unit, ref_repeats, alt_repeats
    return None, None, None


def vcf2cshl(
    pos: int, ref: str, alt: str,
    trimmer: Callable[
        [int, str, str], tuple[int, str, str]] = trim_str_right_left,
) -> VariantDesc:
    """Build a description for an VCF allele."""
    tr_vd = None
    tr_unit, tr_ref, tr_alt = tandem_repeat(ref, alt)

    if tr_unit is not None:

        assert tr_ref is not None
        assert tr_alt is not None

        tr_vd = VariantDesc(
            core.Allele.Type.tandem_repeat, pos,
            tr_ref=tr_ref, tr_alt=tr_alt, tr_unit=tr_unit)

        details = cshl_format(pos, ref, alt, trimmer=trimmer)

        details.variant_type |= tr_vd.variant_type
        details.tr_unit = tr_vd.tr_unit
        details.tr_ref = tr_vd.tr_ref
        details.tr_alt = tr_vd.tr_alt

        return details

    return cshl_format(pos, ref, alt, trimmer=trimmer)


class VariantDetails:
    """Represents CSHL variant details."""

    def __init__(
            self, chrom: str, variant_desc: VariantDesc):

        self.chrom = chrom
        self.variant_desc = variant_desc

        self.cshl_position = self.variant_desc.position
        if core.Allele.Type.cnv & self.variant_desc.variant_type:
            self.cshl_location = (
                f"{self.chrom}:"
                f"{self.variant_desc.position}-"
                f"{self.variant_desc.end_position}"
            )
        else:
            self.cshl_location = f"{self.chrom}:{self.cshl_position}"
        self.cshl_variant = str(variant_desc)
        self.cshl_variant_full = variant_desc.to_cshl_full()

    @staticmethod
    def from_vcf(
            chrom: str, position: int,
            reference: str, alternative: str) -> VariantDetails:
        """Build variant details from a VCF variant."""
        return VariantDetails(
            chrom, vcf2cshl(position, reference, alternative),
        )

    @staticmethod
    def from_cnv(variant: SummaryAllele) -> VariantDetails:
        """Build variant details from a CNV variant."""
        # pylint: disable=protected-access
        assert core.Allele.Type.is_cnv(
            variant._allele_type)  # noqa: SLF001

        variant_desc = VariantDesc(
            variant_type=variant._allele_type,  # noqa: SLF001
            position=variant.position,
            end_position=variant.end_position)
        return VariantDetails(
            variant.chrom, variant_desc)


class SummaryAllele(core.Allele):
    """Class to represents a single allele for given position."""

    # pylint: disable=too-many-public-methods,too-many-arguments
    def __init__(
        self,
        chromosome: str,
        position: int,
        reference: str | None,
        alternative: str | None = None,
        end_position: int | None = None,
        summary_index: int = -1,
        allele_index: int = 0,
        transmission_type: TransmissionType = TransmissionType.transmitted,
        allele_type: core.Allele.Type | None = None,
        attributes: dict[str, Any] | None = None,
        effect: str | None = None,
    ):
        super().__init__(
            chrom=chromosome, pos=position, pos_end=end_position,
            ref=reference, alt=alternative,
            allele_type=allele_type)

        self._summary_index: int = summary_index
        self._allele_index: int = allele_index
        self._transmission_type: TransmissionType = transmission_type

        self._details: VariantDetails | None = None

        self._effects = AlleleEffects.from_string(effect) if effect else None
        self.matched_gene_effects: list[EffectGene] = []
        self._attributes: dict[str, Any] = {
            "allele_index": allele_index,
            "transmission_type": transmission_type,
        }
        if attributes is not None:
            self.update_attributes(attributes)

    @property
    def summary_index(self) -> int:
        return self._summary_index

    @summary_index.setter
    def summary_index(self, summary_index: int) -> None:
        self._summary_index = summary_index

    @property
    def allele_index(self) -> int:
        return self._allele_index

    def to_record(self) -> dict[str, Any]:
        """Construct a record from an allele."""
        def enum_to_value(val: Any) -> Any:
            if isinstance(val, enum.IntEnum):
                return int(val)
            if isinstance(val, enum.Enum):
                return str(val)
            return val

        def encode_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
            filtered_attr = {}
            for key, val in attributes.items():
                if key is not None \
                        and key not in {
                            "worst_effect", "effect_details", "gene_effects"}:
                    filtered_attr[key] = enum_to_value(val)

            return filtered_attr

        attributes = encode_attributes(self._attributes)

        return {**attributes,
            "chrom": self.chromosome,
            "position": self.position,
            "reference": self.reference,
            "alternative": self.alternative,
            "end_position": self.end_position,
            "summary_index": self.summary_index,
            "allele_index": self.allele_index,
            "transmission_type": enum_to_value(self.transmission_type),
            "variant_type":
            self.variant_type.value if self.variant_type is not None else None,
            "effects": str(self.effects) if self.effects is not None else None,
        }

    @property
    def variant_type(self) -> core.Allele.Type:
        return self.allele_type

    @property
    def transmission_type(self) -> TransmissionType:
        return self._transmission_type

    @property
    def attributes(self) -> dict[str, Any]:
        return self._attributes

    @property
    def details(self) -> VariantDetails:
        """Build and return CSHL allele details."""
        if self._details is None:
            if self.Type.cnv & self.allele_type:
                self._details = VariantDetails.from_cnv(self)
            elif self.alternative is None:
                raise ValueError(
                    "variant detailf for allele without alternative "
                    "has no meaning")
            else:
                assert self.reference is not None
                self._details = VariantDetails.from_vcf(
                    self.chromosome,
                    self.position,
                    self.reference,
                    self.alternative,
                )
        assert self._details is not None
        return self._details

    @property
    def effects(self) -> AlleleEffects | None:
        """Build and return allele effect."""
        if self._effects is None:
            record = self.attributes
            if "effect_type" in record:
                worst_effect = record["effect_type"]
                if worst_effect is None:
                    return None
                effects = AlleleEffects.from_simplified_effects(
                    worst_effect,
                    list(
                        zip(
                            record["effect_gene_genes"],
                            record["effect_gene_types"],
                        ),
                    ),
                    list(
                        zip(
                            record["effect_details_transcript_ids"],
                            record["effect_details_details"],
                        ),
                    ),
                )
                self._effects = effects
                return self._effects

            if "effects" in record:
                self._effects = AlleleEffects.from_string(
                    record["effects"])
                return self._effects

            self._effects = None

        return self._effects

    @property
    def worst_effect(self) -> str | None:
        if self.effects:
            return self.effects.worst
        return None

    @property
    def effect_types(self) -> list[str]:
        if self.effects:
            return self.effects.types
        return []

    @property
    def effect_genes(self) -> list[EffectGene]:
        if self.effects:
            return self.effects.genes
        return []

    @property
    def effect_gene_symbols(self) -> list[str]:
        return [eg.symbol for eg in self.effect_genes if eg.symbol]

    @property
    def frequency(self) -> float | None:
        return cast(float | None, self.get_attribute("af_allele_freq"))

    @property
    def cshl_variant(self) -> str | None:
        if self.details is None:
            return None
        return self.details.cshl_variant

    @property
    def cshl_variant_full(self) -> str:
        if self.details is None:
            raise ValueError(
                "cshl location for allele without details")
        return self.details.cshl_variant_full

    @property
    def cshl_location(self) -> str:
        """Return CSHL location (chrom:position) of an allele."""
        if self.Type.cnv & self.allele_type:
            return f"{self.chrom}:{self.position}-{self.end_position}"
        if self.alternative is None:
            raise ValueError(
                "cshl location for allele without alternative "
                "has no meaning")
        if self.details is None:
            raise ValueError(
                "cshl location for allele without details")

        return self.details.cshl_location

    @property
    def cshl_position(self) -> int | None:
        """Return CSHL position of an allele."""
        if self.alternative is None:
            return None
        if self.details is None:
            return None
        return self.details.cshl_position

    @property
    def is_reference_allele(self) -> bool:
        return self.allele_index == 0

    def get_attribute(self, item: str, default_val: Any = None) -> Any:
        """Return attribute value.

        Looks up values matching key `item` in additional attributes passed
        on creation of the variant.
        """
        val = self.attributes.get(item, default_val)
        if val is None:
            return default_val
        return val

    def has_attribute(self, item: str) -> bool:
        """Check if an attribute `item` is available."""
        return item in self.attributes

    def update_attributes(self, atts: dict[str, Any]) -> None:
        """Update allele attributes."""
        for key, val in list(atts.items()):
            self.attributes[key] = val

    def __getitem__(self, item: str) -> Any:
        """Return value of an allele attribute.

        Allows using of standard dictionary access to additional variant
        attributes. For example `sv['af_parents_called']` will return value
        matching key `af_parents_called` from addtional variant attributes.
        """
        if not self.has_attribute(item):
            raise AttributeError(f"attribute <{item}> not found")
        return self.get_attribute(item)

    def __contains__(self, item: str) -> bool:
        """Check if the allele has an attribute."""
        return self.has_attribute(item)

    def __repr__(self) -> str:
        if self.Type.is_cnv(self.allele_type):
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        if not self.alternative:
            return f"{self.chrom}:{self.position} {self.reference} (ref)"
        return (
            f"{self.chrom}:{self.position}"
            f" {self.reference}->{self.alternative}"
        )

    @staticmethod
    def create_reference_allele(allele: SummaryAllele) -> SummaryAllele:
        """Given an allele creates the corresponding reference allele."""
        allele_type = core.Allele.Type.position
        sj_index = allele.attributes.get("sj_index")
        if sj_index is not None:
            sj_index = sj_index - allele.allele_index

        new_attributes = {
            "chrom": allele.attributes.get("chrom"),
            "position": allele.attributes.get("position"),
            "end_position": allele.attributes.get("position"),
            "reference": allele.attributes.get("reference"),
            "summary_index": allele.attributes.get(
                "summary_index"),
            "allele_count": allele.attributes.get("allele_count"),
            "allele_index": 0,
            "bucket_index": allele.attributes.get("bucket_index"),
            "sj_index": sj_index,
        }

        return SummaryAllele(
            allele.chromosome,
            allele.position,
            allele.reference,
            end_position=allele.end_position,
            summary_index=allele.summary_index,
            transmission_type=allele.transmission_type,
            attributes=new_attributes,
            allele_type=allele_type,
        )


class SummaryVariant:
    """Represents summary variant."""

    # pylint: disable=R0913,R0902,R0904
    def __init__(self, alleles: list[SummaryAllele]):

        assert len(alleles) >= 1
        assert len({sa.position for sa in alleles}) == 1

        assert alleles[0].is_reference_allele
        self._alleles: list[SummaryAllele] = alleles
        self._allele_count: int = len(self.alleles)
        self._matched_alleles: list[int] = []

        self._chromosome: str = self.ref_allele.chromosome
        self._position: int = self.ref_allele.position
        self._reference: str | None = self.ref_allele.reference
        if len(alleles) > 1:
            self._end_position = alleles[1].end_position
        else:
            self._end_position = self.ref_allele.position

        for allele_index, allele in enumerate(alleles):
            if allele.allele_index == 0:
                allele._allele_index = allele_index  # noqa: SLF001

        self._svuid: str | None = None

    @property
    def chromosome(self) -> str:
        return self._chromosome

    @property
    def chrom(self) -> str:
        return self._chromosome

    @property
    def position(self) -> int:
        return self._position

    @property
    def end_position(self) -> int | None:
        return self._end_position

    @property
    def reference(self) -> str | None:
        return self._reference

    @property
    def allele_count(self) -> int:
        return self._allele_count

    @property
    def summary_index(self) -> int:
        return self.ref_allele.summary_index

    @summary_index.setter
    def summary_index(self, val: int) -> None:
        for allele in self.alleles:
            allele.summary_index = val

    @property
    def alleles(self) -> list[SummaryAllele]:
        return self._alleles

    @property
    def svuid(self) -> str:
        """Build and return summary variant 'unique' ID."""
        if self._svuid is None:
            self._svuid = (
                f"{self.location}.{self.reference}.{self.alternative}."
                f"{self.transmission_type.value}"
            )

        return self._svuid

    @property
    def alternative(self) -> str | None:
        if not self.alt_alleles:
            return None
        return ",".join(
            [
                aa.alternative or ""
                for aa in self.alt_alleles
            ],
        )

    @property
    def location(self) -> str:
        """Return summary variant location."""
        types = self.variant_types
        if core.Allele.Type.large_deletion in types \
                or core.Allele.Type.large_duplication in types:
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        return f"{self.chromosome}:{self.position}"

    @property
    def ref_allele(self) -> SummaryAllele:
        """Return the reference allele of the variant."""
        return self.alleles[0]

    @property
    def alt_alleles(self) -> list[SummaryAllele]:
        """Return list of all alternative alleles of the variant."""
        return self.alleles[1:]

    @property
    def details(self) -> list[VariantDetails]:
        """Return list of 'VariantDetails' for each allele."""
        if not self.alt_alleles:
            return []
        return [sa.details for sa in self.alt_alleles]

    @property
    def cshl_variant(self) -> list[str | None]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_variant for aa in self.alt_alleles]

    @property
    def cshl_variant_full(self) -> list[str | None]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_variant_full for aa in self.alt_alleles]

    @property
    def cshl_location(self) -> list[str]:
        if not self.alt_alleles:
            return []
        return [aa.cshl_location for aa in self.alt_alleles]

    @property
    def effects(self) -> list[AlleleEffects]:
        """Return list of allele effects."""
        if not self.alt_alleles:
            return []
        return [sa.effects for sa in self.alt_alleles if sa.effects]

    @property
    def effect_types(self) -> list[str]:
        ets: set = set()
        for allele in self.alt_alleles:
            ets = ets.union(allele.effect_types)
        return list(ets)

    @property
    def effect_gene_symbols(self) -> list[str]:
        egs: set[str] = set()
        for allele in self.alt_alleles:
            egs = egs.union(allele.effect_gene_symbols)
        return list(egs)

    @property
    def frequencies(self) -> list[float | None]:
        """Return list of allele frequencies."""
        return [sa.frequency for sa in self.alleles]

    @property
    def variant_types(self) -> set[Any]:
        """Return set of allele types."""
        return {aa.allele_type for aa in self.alt_alleles}

    def get_attribute(
            self, item: Any, default: Any | None = None) -> list[Any]:
        return [sa.get_attribute(item, default) for sa in self.alt_alleles]

    def has_attribute(self, item: Any) -> bool:
        return any(sa.has_attribute(item) for sa in self.alt_alleles)

    def __getitem__(self, item: Any) -> list[Any]:
        return self.get_attribute(item)

    def __contains__(self, item: Any) -> bool:
        return self.has_attribute(item)

    def update_attributes(self, atts: dict[str, Any]) -> None:
        for key, values in list(atts.items()):
            if not values:
                continue
            assert len(values) == 1 or len(values) == len(self.alt_alleles)
            for allele, val in zip(self.alt_alleles, itertools.cycle(values)):
                allele.update_attributes({key: val})

    @property
    def _variant_repr(self) -> str:
        if self.alternative:
            return f"{self.reference}->{self.alternative}"
        return f"{self.reference} (ref)"

    def __repr__(self) -> str:
        types = self.variant_types
        if core.Allele.Type.large_deletion in types \
                or core.Allele.Type.large_duplication in types:
            types_str = ", ".join(map(str, types))
            return f"{self.location} {types_str}"
        return f"{self.location} {self._variant_repr}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SummaryVariant):
            return False
        return (
            self.chromosome == other.chromosome
            and self.position == other.position
            and self.reference == other.reference
            and self.alternative == other.alternative
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, SummaryVariant):
            return False
        return (
            self.chromosome <= other.chromosome
            and self.position < other.position
        )

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, SummaryVariant):
            return False
        return (
            self.chromosome >= other.chromosome
            and self.position > other.position
        )

    def set_matched_alleles(self, alleles_indexes: list[int]) -> None:
        # pylint: disable=protected-access
        self._matched_alleles = sorted(alleles_indexes)

    @property
    def matched_alleles(self) -> list[SummaryAllele]:
        if self._matched_alleles is None:
            return []
        return [
            aa
            for aa in self.alleles
            if aa.allele_index in self._matched_alleles
        ]

    @property
    def matched_alleles_indexes(self) -> list[int]:
        return self._matched_alleles

    @property
    def matched_gene_effects(self) -> set[EffectGene]:
        return set.union(
            *[set(aa.matched_gene_effects) for aa in self.alt_alleles])

    @property
    def transmission_type(self) -> TransmissionType:
        return self.alleles[-1].transmission_type

    def to_record(self) -> list[dict[str, Any]]:
        return [allele.to_record() for allele in self.alt_alleles]


class SummaryVariantFactory:
    """Factory for summary variants."""

    @staticmethod
    def summary_allele_from_record(
            record: dict[str, Any],
            transmission_type: TransmissionType | None = None,
            attr_filter: set[str] | None = None) -> SummaryAllele:
        """Build a summary allele from a dictionary (record)."""
        if transmission_type is not None:
            record["transmission_type"] = transmission_type
        alternative = record["alternative"]
        attributes = record
        if attr_filter:
            attributes = {
                k: v
                for (k, v) in record.items()
                if k not in attr_filter
            }

        assert "summary_index" in record

        summary_index = record.get("summary_index", -1)
        allele_index = record["allele_index"]

        chrom = record["chrom"]
        position = record["position"]
        end_position = record.get("end_position")
        reference = record["reference"]
        alternative = record.get("alternative")
        allele_type = record.get("variant_type")
        transmission_type = TransmissionType(
            record.get("transmission_type", TransmissionType.transmitted),
        )

        if position is not None and end_position is not None and \
                reference is None and alternative is None and \
                allele_type is None:
            allele_type = SummaryAllele.Type.position

        if allele_type is not None:
            allele_type = core.Allele.Type(allele_type)

        return SummaryAllele(
            chrom,
            position,
            reference,
            alternative=alternative,
            summary_index=summary_index,
            end_position=record.get("end_position"),
            allele_type=allele_type,
            allele_index=allele_index,
            transmission_type=transmission_type,
            attributes=attributes,
        )

    @staticmethod
    def summary_variant_from_records(
            records: list[dict[str, Any]],
            transmission_type: TransmissionType | None = None,
            attr_filter: set[str] | None = None) -> SummaryVariant:
        """Build summary variant from a list of dictionaries (records)."""
        assert len(records) > 0
        alleles = []
        for record in records:
            allele = SummaryVariantFactory.summary_allele_from_record(
                record, transmission_type=transmission_type,
                attr_filter=attr_filter,
            )
            alleles.append(allele)
        if not alleles[0].is_reference_allele:
            ref_allele = SummaryAllele.create_reference_allele(alleles[0])
            alleles.insert(0, ref_allele)

        allele_count = {"allele_count": len(alleles)}
        for allele in alleles:
            allele.update_attributes(allele_count)

        return SummaryVariant(alleles)

    @staticmethod
    def summary_variant_from_vcf(
            vcf_variant: pysam.VariantRecord,
            summary_index: int,
            transmission_type: TransmissionType) -> SummaryVariant:
        """Build sumamry variant from a pysam VCF record."""
        records = []
        alts = vcf_variant.alts \
            if vcf_variant.alts is not None else ["."]
        allele_count = len(alts) + 1

        records.append(
            {
                "chrom": vcf_variant.chrom,
                "position": vcf_variant.pos,
                "reference": vcf_variant.ref,
                "alternative": None,
                "summary_index": summary_index,
                "allele_index": 0,
                "allele_count": allele_count,
            },
        )

        for allele_index, alt in enumerate(alts):
            records.append(
                {
                    "chrom": vcf_variant.chrom,
                    "position": vcf_variant.pos,
                    "reference": vcf_variant.ref,
                    "alternative": alt,
                    "summary_index": summary_index,
                    "allele_index": allele_index + 1,
                    "allele_count": allele_count,
                },
            )
        return SummaryVariantFactory.summary_variant_from_records(
            records, transmission_type=transmission_type)
