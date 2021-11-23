"""
Created on Feb 13, 2018

@author: lubo
"""
import itertools
import logging

from typing import List, Dict, Set, Any, Optional

from dae.utils.variant_utils import trim_str_left_right, trim_str_right_left
from dae.effect_annotation.effect import AlleleEffects, EffectGene

from dae.variants import core
from dae.variants.attributes import TransmissionType


logger = logging.getLogger(__name__)


def allele_type_from_name(name):
    name = name.lower().strip()
    if name == "sub" or name == "substitution":
        return core.Allele.Type.substitution
    elif name == "ins" or name == "insertion":
        return core.Allele.Type.small_insertion
    elif name == "del" or name == "deletion":
        return core.Allele.Type.small_deletion
    elif name == "comp" or name == "complex":
        return core.Allele.Type.complex
    elif name in {"cnv_p", "cnv+", "large_duplication"}:
        return core.Allele.Type.large_duplication
    elif name in {"cnv_m", "cnv-", "large_deletion"}:
        return core.Allele.Type.large_deletion
    elif name in {"tr", "tandem_repeat"}:
        return core.Allele.Type.tandem_repeat

    raise ValueError(f"unexpected variant type: {name}")


def allele_type_from_cshl_variant(variant):
    # FIXME: Change logic to use entire string
    if variant is None:
        return None

    vt = variant[0:2]
    if vt == "su":
        return core.Allele.Type.substitution
    elif vt == "in":
        return core.Allele.Type.small_insertion
    elif vt == "de":
        return core.Allele.Type.small_deletion
    elif vt == "co":
        return core.Allele.Type.complex
    elif vt == "TR":
        return core.Allele.Type.tandem_repeat
    elif variant == "CNV+":
        return core.Allele.Type.large_duplication
    elif variant == "CNV-":
        return core.Allele.Type.large_duplication
    else:
        raise ValueError(f"unexpected variant type: {variant}")


class VariantDesc:

    def __init__(
            self, variant_type, position,
            end_position=None,
            ref=None, alt=None, length=None,
            tr_ref=None, tr_alt=None, tr_unit=None):

        self.variant_type = variant_type
        self.position = position
        self.end_position = end_position

        self.ref = ref
        self.alt = alt
        self.length = length

        self.tr_ref = tr_ref
        self.tr_alt = tr_alt
        self.tr_unit = tr_unit

    def __repr__(self):
        return self.to_cshl_short()

    def to_cshl_short(self):

        if self.variant_type & core.Allele.Type.substitution:
            return f"sub({self.ref}->{self.alt})"
        elif self.variant_type & core.Allele.Type.small_insertion:
            return f"ins({self.alt})"
        elif self.variant_type & core.Allele.Type.small_deletion:
            return f"del({self.length})"
        elif self.variant_type & core.Allele.Type.complex:
            return f"comp({self.ref}->{self.alt})"
        elif self.variant_type & core.Allele.Type.large_duplication:
            return "CNV+"
        elif self.variant_type & core.Allele.Type.large_deletion:
            return "CNV-"

    def to_cshl_full(self):

        if self.variant_type & core.Allele.Type.tandem_repeat:
            return f"TR({self.tr_ref}x{self.tr_unit}->{self.tr_alt})"
        elif self.variant_type & core.Allele.Type.substitution:
            return f"sub({self.ref}->{self.alt})"
        elif self.variant_type & core.Allele.Type.small_insertion:
            return f"ins({self.alt})"
        elif self.variant_type & core.Allele.Type.small_deletion:
            return f"del({self.length})"
        elif self.variant_type & core.Allele.Type.complex:
            return f"comp({self.ref}->{self.alt})"
        elif self.variant_type & core.Allele.Type.large_duplication:
            return "CNV+"
        elif self.variant_type & core.Allele.Type.large_deletion:
            return "CNV-"

    @staticmethod
    def combine(variant_descs):
        if all([variant_descs[0].variant_type == vd.variant_type
                for vd in variant_descs]) or \
            all([
                vd.variant_type & core.Allele.Type.tandem_repeat
                for vd in variant_descs]):

            result = VariantDesc(
                variant_descs[0].variant_type,
                variant_descs[0].position,
                ref=variant_descs[0].ref,
                alt=",".join(filter(
                    lambda a: a is not None,
                    [vd.alt for vd in variant_descs])),
                length=variant_descs[-1].length,
                tr_ref=variant_descs[0].tr_ref,
                tr_alt=",".join(filter(
                    lambda a: a is not None,
                    [str(vd.tr_alt) for vd in variant_descs])),
                tr_unit=variant_descs[0].tr_unit
            )
            return [result.to_cshl_full()]
        return [str(vd) for vd in variant_descs]


def cshl_format(pos, ref, alt, trimmer=trim_str_left_right):
    p, r, a = trimmer(pos, ref, alt)
    if len(r) == len(a) and len(r) == 0:
        return VariantDesc(
            core.Allele.Type.complex, p, ref=r, alt=a, length=0)

    if len(r) == len(a) and len(r) == 1:
        return VariantDesc(
            core.Allele.Type.substitution, p, ref=r, alt=a, length=1)

    if len(r) > len(a) and len(a) == 0:
        return VariantDesc(
            core.Allele.Type.small_deletion, p, length=len(r)
        )

    # len(ref) < len(alt):
    if len(r) < len(a) and len(r) == 0:
        return VariantDesc(
            core.Allele.Type.small_insertion, p, alt=a, length=len(a))

    return VariantDesc(
        core.Allele.Type.complex, p, ref=r, alt=a, length=max(len(r), len(a))
    )


def tandem_repeat(ref, alt, min_mono_reference=8):
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


def vcf2cshl(pos, ref, alt, trimmer=trim_str_right_left):
    tr_vd = None
    tr_unit, tr_ref, tr_alt = tandem_repeat(ref, alt)

    if tr_unit is not None:

        assert tr_ref is not None
        assert tr_alt is not None

        tr_vd = VariantDesc(
            core.Allele.Type.tandem_repeat, pos,
            tr_ref=tr_ref, tr_alt=tr_alt, tr_unit=tr_unit)

        vd = cshl_format(pos, ref, alt, trimmer=trimmer)

        vd.variant_type |= tr_vd.variant_type
        vd.tr_unit = tr_vd.tr_unit
        vd.tr_ref = tr_vd.tr_ref
        vd.tr_alt = tr_vd.tr_alt

        return vd

    return cshl_format(pos, ref, alt, trimmer=trimmer)


class VariantDetails:

    def __init__(
            self, chrom: str, variant_desc: VariantDesc):

        self.chrom = chrom
        self.variant_desc = variant_desc

        self.cshl_position = self.variant_desc.position
        if core.Allele.Type.cnv & self.variant_desc.variant_type:
            self.cshl_location = f"{self.chrom}:" \
                f"{self.variant_desc.position}-" \
                f"{self.variant_desc.end_position}"
        else:
            self.cshl_location = f"{self.chrom}:{self.cshl_position}"
        self.cshl_variant = str(variant_desc)
        self.cshl_variant_full = variant_desc.to_cshl_full()

    @staticmethod
    def from_vcf(chrom, position, reference, alternative):
        return VariantDetails(
            chrom, vcf2cshl(position, reference, alternative)
        )

    @staticmethod
    def from_cnv(variant):
        assert core.Allele.Type.cnv & variant._variant_type

        variant_desc = VariantDesc(
            variant_type=variant._variant_type,
            position=variant.position,
            end_position=variant.end_position)
        return VariantDetails(
            variant.chrom, variant_desc)


class SummaryAllele(core.Allele):
    """
    `SummaryAllele` represents a single allele for given position.
    """
    # class Type(core.Allele.Type):
    #     def __and__(self, other):
    #         assert isinstance(other, core.Allele.Type), type(other)
    #         return self.value & other.value

    #     def __or__(self, other):
    #         assert isinstance(other, core.Allele.Type)
    #         return self.value | other.value

    #     def __ior__(self, other):
    #         assert isinstance(other, SummaryAllele.Type)
    #         return SummaryAllele.Type(self.value | other.value)

    #     @classmethod
    #     def from_value(cls, value):
    #         if value is None:
    #             return None
    #         return cls(value)

    #     # @classmethod
    #     # def is_cnv(cls, vt):
    #     #     if vt is None:
    #     #         return False
    #     #     assert isinstance(vt, core.Allele.Type)
    #     #     return vt & cls.cnv

    #     @classmethod
    #     def is_tr(cls, vt):
    #         if vt is None:
    #             return False
    #         assert isinstance(vt, core.Allele.Type)
    #         return vt & core.Allele.Type.tandem_repeat

    #     def __str__(self) -> str:
    #         return self.TYPE_DISPLAY_NAME.get(self.name) or self.name

    #     def __lt__(self, other):
    #         return self.value < other.value

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
        allele_type=None,
        attributes: Dict[str, Any] = None,
        effect: str = None,
    ):
        super(SummaryAllele, self).__init__(
            chrom=chromosome, pos=position, pos_end=end_position,
            ref=reference, alt=alternative,
            allele_type=allele_type)

        self._summary_index: int = summary_index
        self._allele_index: int = allele_index
        self._transmission_type: TransmissionType = transmission_type

        self._details = None

        self._effects = AlleleEffects.from_string(effect) if effect else None

        self._attributes: Dict[str, Any] = {
            "allele_index": allele_index,
            "transmission_type": transmission_type
        }
        if attributes is not None:
            self.update_attributes(attributes)

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
    def variant_type(self) -> core.Allele.Type:
        return self.allele_type

    @property
    def transmission_type(self) -> TransmissionType:
        return self._transmission_type

    @property
    def attributes(self) -> Dict[str, Any]:
        return self._attributes

    @property
    def details(self) -> Optional[VariantDetails]:
        if self._details is None:
            if self.Type.cnv & self.allele_type:
                self._details = VariantDetails.from_cnv(self)
            elif self.alternative is None:
                return None
            else:
                self._details = VariantDetails.from_vcf(
                    self.chromosome,
                    self.position,
                    self.reference,
                    self.alternative,
                )
        return self._details

    @property
    def effects(self) -> Optional[AlleleEffects]:
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
                        )
                    ),
                    list(
                        zip(
                            record["effect_details_transcript_ids"],
                            record["effect_details_details"],
                        )
                    ),
                )
                self._effects = effects
            elif "effects" in record:
                self._effects = AlleleEffects.from_string(
                    record.get("effects"))
            else:
                self._effects = None
        return self._effects

    @effects.setter
    def effects(self, effects: AlleleEffects) -> None:
        # assert self._effects is None
        self._effects = effects

    @property
    def worst_effect(self) -> Optional[str]:
        if self.effects:
            return self.effects.worst
        return None

    @property
    def effect_types(self) -> List[str]:
        if self.effects:
            return self.effects.types
        else:
            return []

    @property
    def effect_genes(self) -> List[EffectGene]:
        if self.effects:
            return self.effects.genes
        else:
            return []

    @property
    def effect_gene_symbols(self) -> List[str]:
        return [eg.symbol for eg in self.effect_genes]

    @property
    def frequency(self) -> Optional[float]:
        return self.get_attribute("af_allele_freq")

    @property
    def cshl_variant(self) -> Optional[str]:
        if self.details is None:
            return None
        return self.details.cshl_variant  # type: ignore

    @property
    def cshl_variant_full(self) -> Optional[str]:
        if self.details is None:
            return None
        return self.details.cshl_variant_full  # type: ignore

    @property
    def cshl_location(self) -> Optional[str]:
        if self.Type.cnv & self.allele_type:
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
        if val is None:
            val = default
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
        return self.get_attribute(item)

    def __contains__(self, item) -> bool:
        """
        checks if additional variant attributes contain value for key `item`.
        """
        return item in self.has_attributes(item)

    def __repr__(self) -> str:
        if self.Type.cnv & self.allele_type:
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        elif not self.alternative:
            return f"{self.chrom}:{self.position} {self.reference} (ref)"
        else:
            return (
                f"{self.chrom}:{self.position}"
                f" {self.reference}->{self.alternative}"
            )

    @staticmethod
    def create_reference_allele(allele) -> "SummaryAllele":
        new_attributes = {
            "chrom": allele.attributes.get("chrom"),
            "position": allele.attributes.get("position"),
            "end_position": allele.attributes.get("end_position"),
            "reference": allele.attributes.get("reference"),
            "summary_variant_index": allele.attributes.get(
                "summary_variant_index"),
            "allele_count": allele.attributes.get("allele_count"),
        }

        return SummaryAllele(
            allele.chromosome,
            allele.position,
            allele.reference,
            end_position=allele.end_position,
            summary_index=allele.summary_index,
            transmission_type=allele.transmission_type,
            attributes=new_attributes,
        )


class SummaryVariant:

    def __init__(self, alleles):
        super(SummaryVariant, self).__init__()

        assert len(alleles) >= 1
        assert len(set([sa.position for sa in alleles])) == 1

        assert alleles[0].is_reference_allele
        self._alleles: List[SummaryAllele] = alleles
        self._allele_count: int = len(self.alleles)

        self._chromosome: str = self.ref_allele.chromosome
        self._position: int = self.ref_allele.position
        self._reference: str = self.ref_allele.reference
        if len(alleles) > 1:
            self._end_position = alleles[1].end_position
        else:
            self._end_position = None

        for allele_index, allele in enumerate(alleles):
            if allele.allele_index == 0:
                allele._allele_index = allele_index

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
                f"{self.location}.{self.reference}.{self.alternative}." \
                f"{self.transmission_type.value}"

        return self._svuid

    @property
    def alternative(self) -> Optional[str]:
        if not self.alt_alleles:
            return None
        return ",".join(
            [
                aa.alternative if aa.alternative else ""
                for aa in self.alt_alleles
            ]
        )

    @property
    def location(self) -> str:
        types = self.variant_types
        if core.Allele.Type.large_deletion in types \
                or core.Allele.Type.large_duplication in types:
            return f"{self.chromosome}:{self.position}-{self.end_position}"
        else:
            return f"{self.chromosome}:{self.position}"

    @property
    def ref_allele(self) -> SummaryAllele:
        """
        the reference allele
        """
        return self.alleles[0]

    @property
    def alt_alleles(self) -> List[SummaryAllele]:
        """list of all alternative alleles"""
        return self.alleles[1:]

    @property
    def details(self) -> List[VariantDetails]:
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
        return [sa.effects for sa in self.alt_alleles]

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
        return set([aa.allele_type for aa in self.alt_alleles])

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
        if core.Allele.Type.large_deletion in types \
                or core.Allele.Type.large_duplication in types:
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

    def set_matched_alleles(self, alleles_indexes):
        self._matched_alleles = sorted(alleles_indexes)

    @property
    def matched_alleles(self):
        return [
            aa
            for aa in self.alleles
            if aa.allele_index in self._matched_alleles
        ]

    @property
    def matched_alleles_indexes(self):
        return self._matched_alleles

    @property
    def matched_gene_effects(self):
        return set(
            itertools.chain.from_iterable(
                [ma.matched_gene_effects for ma in self.matched_alleles]
            )
        )

    @property
    def transmission_type(self):
        return self.alleles[-1].transmission_type


class SummaryVariantFactory(object):
    @staticmethod
    def summary_allele_from_record(
            record, transmission_type=None,
            attr_filter=None):

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

        if "summary_variant_index" in record:
            summary_index = record["summary_variant_index"]
        else:
            summary_index = record.get("summary_index")

        allele_index = record.get("allele_index")

        chrom = record.get("chrom")
        position = record.get("position")
        end_position = record.get("end_position")
        reference = record.get("reference")
        alternative = record.get("alternative")
        allele_type = record.get("variant_type")

        if position is not None and end_position is not None and \
                reference is None and alternative is None and \
                allele_type is None:
            allele_type = SummaryAllele.Type.position

        return SummaryAllele(
            chrom,
            position,
            reference,
            alternative=alternative,
            summary_index=summary_index,
            end_position=record.get("end_position", None),
            allele_type=allele_type,
            allele_index=allele_index,
            transmission_type=record.get("transmission_type"),
            attributes=attributes,
        )

    @staticmethod
    def summary_variant_from_records(
            records, transmission_type=None,
            attr_filter=None):

        assert len(records) > 0

        alleles = []
        for record in records:
            sa = SummaryVariantFactory.summary_allele_from_record(
                record, transmission_type=transmission_type,
                attr_filter=attr_filter
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
    def blank_summary_allele_from_record(record):
        attributes = record

        chrom = record.get("chrom", "1")
        position = record.get("position", 1000)
        reference = record.get("reference", "G")
        alternative = record.get("alternative", "C")
        summary_index = record.get("summary_index", -1)
        end_position = record.get("end_position", None)
        allele_type = record.get("variant_type", None)
        allele_index = record.get("allele_index", 1)
        transmission_type = record.get(
            "transmission_type", TransmissionType.transmitted
        )

        return SummaryAllele(
            chrom,
            position,
            reference,
            alternative=alternative,
            summary_index=summary_index,
            end_position=end_position,
            allele_type=allele_type,
            allele_index=allele_index,
            transmission_type=transmission_type,
            attributes=attributes,
        )

    @staticmethod
    def blank_summary_variant_from_records(records):
        assert len(records) > 0

        alleles = []
        for record in records:
            sa = SummaryVariantFactory.blank_summary_allele_from_record(record)
            alleles.append(sa)
        if not alleles[0].is_reference_allele:
            ref_allele = SummaryAllele.create_reference_allele(alleles[0])
            alleles.insert(0, ref_allele)

        allele_count = {"allele_count": len(alleles)}
        for allele in alleles:
            allele.update_attributes(allele_count)

        return SummaryVariant(alleles)

    @staticmethod
    def summary_variant_from_vcf(
            vcf_variant, summary_variant_index, transmission_type):
        records = []
        alts = vcf_variant.alts \
            if vcf_variant.alts is not None else ["."]
        allele_count = (len(alts) + 1)

        records.append(
            {
                "chrom": vcf_variant.chrom,
                "position": vcf_variant.pos,
                "reference": vcf_variant.ref,
                "alternative": None,
                "summary_variant_index": summary_variant_index,
                "allele_index": 0,
                "allele_count": allele_count,
            }
        )

        for allele_index, alt in enumerate(alts):
            records.append(
                {
                    "chrom": vcf_variant.chrom,
                    "position": vcf_variant.pos,
                    "reference": vcf_variant.ref,
                    "alternative": alt,
                    "summary_variant_index": summary_variant_index,
                    "allele_index": allele_index + 1,
                    "allele_count": allele_count,
                }
            )
        return SummaryVariantFactory.summary_variant_from_records(
            records, transmission_type=transmission_type)
