"""Classes and helpers for variant annotation effects."""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Any, ClassVar

from dae.effect_annotation.annotation_request import AnnotationRequest
from dae.genomic_resources.gene_models import TranscriptModel


class AnnotationEffect:  # pylint: disable=too-many-instance-attributes
    """Class to represent variant effect."""

    SEVERITY: ClassVar[dict[str, int]] = {
        "CNV+": 35,
        "CNV-": 35,
        "tRNA:ANTICODON": 30,
        "all": 24,
        "splice-site": 23,
        "frame-shift": 22,
        "nonsense": 21,
        "no-frame-shift-newStop": 20,
        "noStart": 19,
        "noEnd": 18,
        "missense": 17,
        "no-frame-shift": 16,
        "CDS": 15,
        "synonymous": 14,
        "coding_unknown": 13,
        "regulatory": 12,
        "3'UTR": 11,
        "5'UTR": 10,
        "intron": 9,
        "non-coding": 8,
        "5'UTR-intron": 7,
        "3'UTR-intron": 6,
        "promoter": 5,
        "non-coding-intron": 4,
        "unknown": 3,
        "intergenic": 2,
        "no-mutation": 1,
    }

    def __init__(self, effect_name: str) -> None:
        self.effect: str = effect_name
        self.gene: str | None = None
        self.transcript_id: str | None = None
        self.strand: str | None = None
        self.prot_pos: int | None = None
        self.non_coding_pos: int | None = None
        self.prot_length: int | None = None
        self.length: int | None = None
        self.which_intron: int | None = None
        self.how_many_introns: int | None = None
        self.dist_from_coding: int | None = None
        self.aa_change: str | None = None
        self.dist_from_acceptor: int | None = None
        self.dist_from_donor: int | None = None
        self.intron_length: int | None = None
        # pylint: disable=invalid-name
        self.mRNA_length: int | None = None
        self.mRNA_position: int | None = None
        self.ref_aa: list[str] | None = None
        self.alt_aa: list[str] | None = None
        self.dist_from_5utr = None

    def __repr__(self) -> str:
        return (
            f"Effect gene:{self.gene} trID:{self.transcript_id} "
            f"strand:{self.strand} effect:{self.effect} "
            f"protein pos:{self.prot_pos}/{self.prot_length} "
            f"aa: {self.aa_change} "
            f"len: {self.length}"
        )

    def create_effect_details(self) -> str:
        """Build effect details."""
        eff_data = [
            (
                [
                    "CNV+",
                    "CNV-",
                ],
                str(self.length),
            ),
            (
                [
                    "noStart",
                    "noEnd",
                    "CDS",
                    "all",
                ],
                str(self.prot_length),
            ),
            (
                [
                    "intron",
                    "5'UTR-intron",
                    "3'UTR-intron",
                    "non-coding-intron",
                ],
                str(self.which_intron) + "/" + str(self.how_many_introns),
            ),
            (
                [
                    "intron",
                    "5'UTR-intron",
                    "3'UTR-intron",
                    "non-coding-intron",
                ],
                "[" + str(self.dist_from_coding) + "]",
            ),
            (
                [
                    "no-frame-shift",
                    "no-frame-shift-newStop",
                    "frame-shift",
                    "splice-site",
                    "synonymous",
                    "missense",
                    "nonsense",
                    "coding_unknown",
                ],
                str(self.prot_pos) + "/" + str(self.prot_length),
            ),
            (
                [
                    "no-frame-shift",
                    "no-frame-shift-newStop",
                    "missense",
                    "nonsense",
                    "coding_unknown",
                ],
                "(" + str(self.aa_change) + ")",
            ),
            (["no-mutation"], "no-mutation"),
            (["5'UTR", "3'UTR"], str(self.dist_from_coding)),
            (
                [
                    "non-coding",
                    "unknown",
                    "tRNA:ANTICODON",
                ],
                str(self.length),
            ),
            (["promoter"], str(self.dist_from_5utr)),
        ]

        return "".join(
            [data for cond, data in eff_data if self.effect in cond],
        )

    @classmethod
    def effect_severity(cls, effect: AnnotationEffect) -> int:
        return AnnotationEffect.SEVERITY[effect.effect]

    @classmethod
    def sort_effects(
            cls, effects: list[AnnotationEffect]) -> list[AnnotationEffect]:
        return sorted(
            effects, key=lambda v: - cls.effect_severity(v))

    @classmethod
    def worst_effect(cls, effects: list[AnnotationEffect]) -> str:
        sorted_effects = cls.sort_effects(effects)
        return sorted_effects[0].effect

    @classmethod
    def gene_effects(cls, effects: list[AnnotationEffect]) -> list[list[str]]:
        """Build parallel lists of genes and effects in that genes.

        Consider deprecating this.
        """
        sorted_effects = cls.sort_effects(effects)
        worst_effect = sorted_effects[0].effect
        if worst_effect == "intergenic":
            return [["intergenic"], ["intergenic"]]
        if worst_effect == "no-mutation":
            return [["no-mutation"], ["no-mutation"]]

        result = []
        for _severity, severity_effects in itertools.groupby(
            sorted_effects, cls.effect_severity,
        ):
            for gene, gene_effects in itertools.groupby(
                severity_effects, lambda e: e.gene,
            ):
                result.append((gene, next(gene_effects).effect))

        return [[str(r[0]) for r in result], [str(r[1]) for r in result]]

    @classmethod
    def transcript_effects(
        cls, effects: list[AnnotationEffect],
    ) -> tuple[list[str], list[str | None], list[str | None], list[str]]:
        """Build parallel lists of transcripts, genes, effects and details.

        Consider deprecating this.
        """
        worst_effect = cls.worst_effect(effects)
        if worst_effect == "intergenic":
            return (
                ["intergenic"],
                ["intergenic"],
                ["intergenic"],
                ["intergenic"],
            )
        if worst_effect == "no-mutation":
            return (
                ["no-mutation"],
                ["no-mutation"],
                ["no-mutation"],
                ["no-mutation"],
            )

        transcripts = []
        genes = []
        gene_effects = []
        details = []
        for effect in effects:
            transcripts.append(effect.transcript_id)
            genes.append(effect.gene)
            gene_effects.append(effect.effect)
            details.append(effect.create_effect_details())
        return (transcripts, genes, gene_effects, details)  # type: ignore

    @classmethod
    def simplify_effects(
        cls, effects: list[AnnotationEffect],
    ) -> tuple[
        str,
        list[tuple[str, str]],
        list[tuple[str, str | None, str | None, str]],
    ]:
        """Simplify effects.

        Consider deprecating this.
        """
        if effects[0].effect == "unk_chr":
            return (
                "unk_chr",
                [("unk_chr", "unk_chr")],
                [("unk_chr", "unk_chr", "unk_chr", "unk_chr")],
            )

        gene_effects = cls.gene_effects(effects)
        transcript_effects = cls.transcript_effects(effects)

        return (
            cls.worst_effect(effects),
            list(zip(*gene_effects, strict=True)),
            list(zip(*transcript_effects, strict=True)))

    @classmethod
    def filter_gene_effects(
        cls, effects: list[AnnotationEffect],
        effect_type: str,
    ) -> list[list[str]]:
        """Filter and map genes to effects by a group or effect type."""
        gene_effects = zip(*cls.gene_effects(effects), strict=True)
        if effect_type in EffectTypesMixin.EFFECT_GROUPS:
            result = [
                gene_effect
                for gene_effect in gene_effects
                if gene_effect[1] in EffectTypesMixin.EFFECT_GROUPS[
                    effect_type]
            ]
        elif effect_type in EffectTypesMixin.EFFECT_TYPES:
            result = [
                gene_effect
                for gene_effect in gene_effects
                if gene_effect[1] == effect_type
            ]
        else:
            raise ValueError(
                f"{effect_type} does not match any effect type or group",
            )
        return [[str(r[0]) for r in result], [str(r[1]) for r in result]]

    @classmethod
    def effects_description(
        cls, effects: list[AnnotationEffect],
    ) -> tuple[str, str, str]:
        """Build effects description.

        Condider deprecating this.
        """
        worst_effect, gene_effects, transcript_effects = \
            cls.simplify_effects(effects)

        gene_effects_out = "|".join([f"{g}:{e}" for g, e in gene_effects])
        transcript_effects_out = "|".join(
            [f"{t}:{g}:{e}:{d}" for t, g, e, d in transcript_effects],
        )
        return (worst_effect, gene_effects_out, transcript_effects_out)


class EffectFactory:
    """Factory class for build annotation effects."""

    @classmethod
    def create_effect(cls, effect_name: str) -> AnnotationEffect:
        return AnnotationEffect(effect_name)

    @classmethod
    def create_effect_with_tm(
        cls, effect_name: str, transcript_model: TranscriptModel,
    ) -> AnnotationEffect:
        """Create effect with transcript model."""
        effect = cls.create_effect(effect_name)
        effect.gene = transcript_model.gene
        effect.strand = transcript_model.strand
        try:
            effect.transcript_id = transcript_model.tr_name
        except AttributeError:
            effect.transcript_id = transcript_model.tr_id

        return effect

    @classmethod
    def create_effect_with_request(
        cls, effect_name: str, request: AnnotationRequest,
    ) -> AnnotationEffect:
        """Create effect with annotation request."""
        effect = cls.create_effect_with_tm(
            effect_name, request.transcript_model,
        )
        effect.mRNA_length = request.get_exonic_length()
        effect.mRNA_position = request.get_exonic_position()
        return effect

    @classmethod
    def create_effect_with_prot_length(
        cls, effect_name: str, request: AnnotationRequest,
    ) -> AnnotationEffect:
        effect = cls.create_effect_with_request(effect_name, request)
        effect.prot_length = request.get_protein_length()
        return effect

    @classmethod
    def create_effect_with_prot_pos(
        cls, effect_name: str, request: AnnotationRequest,
    ) -> AnnotationEffect:
        """Create effect with protein change position."""
        effect = cls.create_effect_with_prot_length(effect_name, request)
        start_prot, _ = request.get_protein_position()
        effect.prot_pos = start_prot
        return effect

    @classmethod
    def create_effect_with_aa_change(
        cls, effect_name: str, request: AnnotationRequest,
    ) -> AnnotationEffect:
        """Create effect with amino acid change."""
        effect = cls.create_effect_with_prot_pos(effect_name, request)

        ref_aa, alt_aa = request.get_amino_acids()
        assert ref_aa is not None
        assert alt_aa is not None
        effect.aa_change = f"{''.join(ref_aa)}->{''.join(alt_aa)}"
        effect.ref_aa = ref_aa
        effect.alt_aa = alt_aa

        return effect

    @classmethod
    def create_intronic_non_coding_effect(
        cls, effect_type: str,
        request: AnnotationRequest,
        start: int, end: int, index: int,
    ) -> AnnotationEffect:
        """Create intronic non coding effect."""
        effect = cls.create_effect_with_prot_length(effect_type, request)
        dist_left = request.variant.position - start - 1
        dist_right = end - request.variant.ref_position_last
        effect.dist_from_coding = min(dist_left, dist_right)

        effect.how_many_introns = len(request.transcript_model.exons) - 1
        effect.intron_length = end - start - 1
        if request.transcript_model.strand == "+":
            effect.dist_from_acceptor = dist_right
            effect.dist_from_donor = dist_left
            effect.which_intron = index
        else:
            effect.dist_from_acceptor = dist_left
            effect.dist_from_donor = dist_right
            effect.which_intron = effect.how_many_introns - index + 1
        return effect

    @classmethod
    def create_intronic_effect(
        cls, effect_type: str,
        request: AnnotationRequest,
        start: int, end: int, index: int,
    ) -> AnnotationEffect:
        """Create intronic effect."""
        effect = cls.create_intronic_non_coding_effect(
            effect_type, request, start, end, index,
        )
        if request.transcript_model.strand == "+":
            effect.prot_pos = request.get_protein_position_for_pos(end)
        else:
            effect.prot_pos = request.get_protein_position_for_pos(start)
        return effect


class EffectGene:
    """Combine gene and effect and that gene."""

    def __init__(
        self, symbol: str | None = None,
        effect: str | None = None,
    ) -> None:
        self.symbol = symbol
        self.effect = effect

    @staticmethod
    def from_string(data: str) -> EffectGene | None:
        """Deserialize effect gene."""
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]
        if len(parts) == 2:
            return EffectGene(parts[0], parts[1])
        if len(parts) == 1:
            return EffectGene(symbol=None, effect=parts[0])

        raise ValueError(f"unexpected effect gene format: {data}")

    def __repr__(self) -> str:
        if self.symbol is None and self.effect is None:
            return "(no effect)"
        if self.symbol is None:
            assert self.effect is not None
            return self.effect
        return f"{self.symbol}:{self.effect}"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: Any) -> bool:
        assert isinstance(other, EffectGene)

        return self.symbol == other.symbol and self.effect == other.effect

    def __hash__(self) -> int:
        return hash((self.symbol, self.effect))

    @classmethod
    def from_gene_effects(
        cls, gene_effects: list[tuple[str, str]],
    ) -> list[EffectGene]:
        """Build effect gene objects from list of gene, effect tuples."""
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_tuple(cls, gene_effect: tuple[str, str]) -> EffectGene:
        (symbol, effect) = tuple(gene_effect)
        return EffectGene(symbol, effect)


class EffectTranscript:
    """Defines effect transcript."""

    def __init__(
        self, transcript_id: str,
        gene: str | None = None,
        effect: str | None = None,
        details: str | None = None,
    ) -> None:
        self.transcript_id = transcript_id
        self.gene = gene
        self.effect = effect
        self.details = details

    @staticmethod
    def from_string(data: str) -> EffectTranscript | None:
        """Deserialize effect transcript/details."""
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]

        if len(parts) == 4:
            return EffectTranscript(
                parts[0], gene=parts[1], effect=parts[2], details=parts[3])
        raise ValueError(
            f"unexpected effect details format: {data}")

    def __repr__(self) -> str:
        return f"{self.transcript_id}:{self.gene}:{self.effect}:{self.details}"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: Any) -> bool:
        assert isinstance(other, EffectTranscript)

        return (
            self.transcript_id == other.transcript_id
            and self.details == other.details
        )

    @classmethod
    def from_tuple(
        cls, transcript_tuple: tuple[str, str | None, str | None, str],
    ) -> EffectTranscript:
        (transcript_id, gene, effect, details) = tuple(transcript_tuple)
        assert transcript_id is not None, transcript_tuple
        return EffectTranscript(
            transcript_id, gene=gene, effect=effect, details=details)

    @classmethod
    def from_effect_transcripts(
            cls, effect_transcripts: list[tuple[str, str]],
    ) -> dict[str, EffectTranscript]:
        """Build effect transcripts."""
        result = {}
        for transcript_id, details in effect_transcripts:
            parts = [p.strip() for p in details.split(":")]
            if transcript_id is None:
                result["intergenic"] = EffectTranscript(
                    "intergenic", "intergenic", "intergenic", "intergenic")
            elif len(parts) == 4:
                result[transcript_id] = EffectTranscript(
                    parts[0], gene=parts[1], effect=parts[2], details=parts[3])
            else:
                result[transcript_id] = EffectTranscript.from_tuple(
                    (transcript_id, None, None, details),
                )
        return result


class AlleleEffects:
    """Class for allele effect used in alleles."""

    def __init__(
            self, worst_effect: str,
            gene_effects: list[EffectGene],
            effect_transcripts: dict[str, EffectTranscript],
    ) -> None:
        self.worst_effect = worst_effect
        self.genes = gene_effects
        self.transcripts = effect_transcripts
        self._effect_types: list | None = None
        self.all_effects: list[AnnotationEffect] | None = None

    @property
    def worst(self) -> str:
        return self.worst_effect

    def __repr__(self) -> str:
        effects = "|".join([str(g) for g in self.genes])
        transcripts = "|".join([str(t) for t in self.transcripts.values()])
        return f"{self.worst}!{effects}!{transcripts}"

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AlleleEffects):
            return False
        assert isinstance(other, AlleleEffects)

        return (
            self.worst == other.worst
            and self.genes == other.genes
            and self.transcripts == other.transcripts
        )

    @property
    def types(self) -> list[str]:
        if self._effect_types is None:
            self._effect_types = [eg.effect for eg in self.genes]
        return self._effect_types

    @classmethod
    def from_simplified_effects(
            cls, effect_type: str,
            effect_genes: list[tuple[str, str]],
            transcripts: list[tuple[str, str]],
    ) -> AlleleEffects | None:
        """Build allele effects from simplified effects."""
        if effect_type is None:
            return None

        effect_genes_out = EffectGene.from_gene_effects(effect_genes)
        transcripts_out = EffectTranscript.from_effect_transcripts(transcripts)
        return AlleleEffects(effect_type, effect_genes_out, transcripts_out)

    @staticmethod
    def from_string(data: str | None) -> AlleleEffects | None:
        """Build allele effect from string."""
        if data is None:
            return None
        parts = data.split("!")
        assert len(parts) == 3, parts
        worst = parts[0].strip()
        effect_genes = list(filter(None, [
            EffectGene.from_string(eg.strip()) for eg in parts[1].split("|")
        ]))
        transcripts_list: list[EffectTranscript] = list(filter(None, [
            EffectTranscript.from_string(et.strip())
            for et in parts[2].split("|")
        ]))
        transcripts = {t.transcript_id: t for t in transcripts_list}
        if not effect_genes and not transcripts:
            return None
        return AlleleEffects(worst, effect_genes, transcripts)

    @classmethod
    def from_effects(cls, effects: list[AnnotationEffect]) -> AlleleEffects:
        """Build allele effects from list of annotation effect."""
        worst_effect, gene_effects, transcript_effects = \
            AnnotationEffect.simplify_effects(effects)
        gene_effects_out = list(itertools.starmap(EffectGene, gene_effects))
        transcript_effects_out = {
            t: EffectTranscript(t, g, e, d)
            for t, g, e, d in transcript_effects
        }

        result = AlleleEffects(
            worst_effect, gene_effects_out, transcript_effects_out)
        result.all_effects = effects
        return result


class EffectTypesMixin:
    """Helper function to work with variant effects."""

    EFFECT_TYPES: ClassVar[list[str]] = [
        "3'UTR",
        "3'UTR-intron",
        "5'UTR",
        "5'UTR-intron",
        "frame-shift",
        "intergenic",
        "intron",
        "missense",
        "no-frame-shift",
        "no-frame-shift-newStop",
        "noEnd",
        "noStart",
        "non-coding",
        "non-coding-intron",
        "nonsense",
        "splice-site",
        "synonymous",
        "CDS",
        "CNV+",
        "CNV-",
        # "cnv+",
        # "cnv-",
        # "nonsynonymous"
    ]

    EFFECT_TYPES_MAPPING: ClassVar[dict[str, list[str]]] = {
        "Nonsense": ["nonsense"],
        "Frame-shift": ["frame-shift"],
        "Splice-site": ["splice-site"],
        "Missense": ["missense"],
        "No-frame-shift": ["no-frame-shift"],
        "No-frame-shift-newStop": ["no-frame-shift-newStop"],
        "noStart": ["noStart"],
        "noEnd": ["noEnd"],
        "Synonymous": ["synonymous"],
        "Non coding": ["non-coding"],
        "Intron": ["intron", "non-coding-intron"],
        "Intergenic": ["intergenic"],
        "3'-UTR": ["3'UTR", "3'UTR-intron"],
        "5'-UTR": ["5'UTR", "5'UTR-intron"],
        "CNV": ["CNV"],
        "CNV+": ["CNV+"],
        "CNV-": ["CNV-"],
        "Nonsynonymous": ["nonsynonymous"],
    }

    EFFECT_TYPES_UI_NAMING: ClassVar[dict[str, str]] = {
        "nonsense": "Nonsense",
        "frame-shift": "Frame-shift",
        "splice-site": "Splice-site",
        "missense": "Missense",
        "no-frame-shift": "No-frame-shift",
        "no-frame-shift-newStop": "No-frame-shift-newStop",
        "synonymous": "Synonymous",
        "non-coding": "Non coding",
        "intron": "Intron",
        "non-coding-intron": "Intron",
    }
    EFFECT_GROUPS: ClassVar[dict[str, list[str]]] = {
        "coding": [
            "nonsense",
            "frame-shift",
            "splice-site",
            "no-frame-shift-newStop",
            "missense",
            "no-frame-shift",
            "noStart",
            "noEnd",
            "synonymous",
        ],
        "noncoding": [
            "non coding",
            "intron",
            "intergenic",
            "3'UTR",
            "5'UTR",
        ],
        "CNV": ["CNV+", "CNV-"],
        "LGDs": [
            "frame-shift",
            "nonsense",
            "splice-site",
            "no-frame-shift-newStop",
        ],
        "nonsynonymous": [
            "nonsense",
            "frame-shift",
            "splice-site",
            "no-frame-shift-newStop",
            "missense",
            "no-frame-shift",
            "noStart",
            "noEnd",
        ],
        "UTRs": [
            "3'UTR",
            "5'UTR",
            "3'UTR-intron",
            "5'UTR-intron",
        ],
    }

    @classmethod
    def build_effect_types_groups(cls, effect_types: list[str]) -> list[str]:
        """Expand effect groups into effect types."""
        etl = [
            cls.EFFECT_GROUPS.get(et, [et])
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    @classmethod
    def build_effect_types_list(cls, effect_types: list[str]) -> list[str]:
        """Fix naming of effect types coming from the UI."""
        etl = [
            cls.EFFECT_TYPES_MAPPING.get(et, [et])
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    @classmethod
    def build_effect_types(
        cls, effect_types: str | Iterable[str], *,
        safe: bool = True,
    ) -> list[str]:
        """Build list of effect types."""
        if isinstance(effect_types, str):
            effect_types = effect_types.split(",")
        etl = [et.strip() for et in effect_types]
        etl = cls.build_effect_types_list(etl)
        etl = cls.build_effect_types_groups(etl)
        if safe:
            assert all(et in cls.EFFECT_TYPES for et in etl), etl
        else:
            etl = [et for et in etl if et in cls.EFFECT_TYPES]
        return etl

    @classmethod
    def build_effect_types_naming(
        cls, effect_types: str | Iterable[str], *,
        safe: bool = True,
    ) -> list[str]:
        """Build list of effect types appropriate for the UI."""
        if isinstance(effect_types, str):
            effect_types = effect_types.split(",")
        assert isinstance(effect_types, list)
        if safe:
            assert all(
                et in cls.EFFECT_TYPES
                or et in cls.EFFECT_TYPES_MAPPING
                for et in effect_types
            )
        return [cls.EFFECT_TYPES_UI_NAMING.get(et, et) for et in effect_types]

    @classmethod
    def get_effect_types(
        cls, *, safe: bool = True, **kwargs: Any,
    ) -> list[str] | None:
        """Process effect types from kwargs."""
        effect_types = kwargs.get("effectTypes")
        if effect_types is None:
            return None

        return cls.build_effect_types(effect_types, safe=safe)


def expand_effect_types(
    effect_groups: str | Iterable[str] | Iterable[Iterable[str]],
) -> list[str]:
    """Expand effect type groups into list of effect types."""
    if isinstance(effect_groups, str):
        effect_groups = [effect_groups]

    effects = []
    for effect_group in effect_groups:
        if isinstance(effect_group, str):
            effect_group = [effect_group]
        for effect in effect_group:
            assert isinstance(effect, str)
            if effect in EffectTypesMixin.EFFECT_GROUPS:
                effects += EffectTypesMixin.EFFECT_GROUPS[effect]
            else:
                effects.append(effect)

    result = []
    for effect in effects:
        if effect not in EffectTypesMixin.EFFECT_TYPES_MAPPING:
            result.append(effect)
        else:
            result.extend(EffectTypesMixin.EFFECT_TYPES_MAPPING[effect])
    return result


def ge2str(eff: AlleleEffects) -> str:
    return "|".join([f"{g.symbol}:{g.effect}" for g in eff.genes])


def gd2str(eff: AlleleEffects) -> str:
    return "|".join(
        [
            str(t) for t in eff.transcripts.values()
        ],
    )


def gene_effect_get_worst_effect(
    gene_effects: AlleleEffects | None,
) -> str:
    if gene_effects is None:
        return ""
    return ",".join([gene_effects.worst])


def gene_effect_get_genes_worst(
    gene_effects: AlleleEffects | None,
) -> str:
    """Return comma separted list of genes."""
    if gene_effects is None:
        return ""
    genes_set: set[str] = {
        x.symbol for x in gene_effects.genes
        if x.symbol is not None and x.effect == gene_effects.worst
    }
    genes = sorted(genes_set)
    return ";".join(genes)


def gene_effect_get_genes(
    gene_effects: AlleleEffects | None,
) -> str:
    """Return comma separted list of genes."""
    if gene_effects is None:
        return ""
    genes_set: set[str] = {
        x.symbol for x in gene_effects.genes if x.symbol is not None
    }
    genes = sorted(genes_set)

    return ";".join(genes)
