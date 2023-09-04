"""Classes and helpers for variant annotation effects."""

from __future__ import annotations

import itertools

from typing import List, Optional, Dict

from dae.utils.effect_utils import EffectTypesMixin
from dae.genomic_resources.gene_models import TranscriptModel
from dae.effect_annotation.annotation_request import AnnotationRequest


class AnnotationEffect:  # pylint: disable=too-many-instance-attributes
    """Class to represent variant effect."""

    SEVERITY: Dict[str, int] = {
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

    def __init__(self, effect_name):
        self.effect: str = effect_name
        self.gene: Optional[str] = None
        self.transcript_id: Optional[str] = None
        self.strand: Optional[str] = None
        self.prot_pos = None
        self.non_coding_pos = None
        self.prot_length = None
        self.length = None
        self.which_intron = None
        self.how_many_introns = None
        self.dist_from_coding = None
        self.aa_change: Optional[str] = None
        self.dist_from_acceptor = None
        self.dist_from_donor = None
        self.intron_length = None
        self.mRNA_length = None  # pylint: disable=invalid-name
        self.mRNA_position = None  # pylint: disable=invalid-name
        self.ref_aa = None
        self.alt_aa = None
        self.dist_from_5utr = None

    def __repr__(self):
        return \
            f"Effect gene:{self.gene} trID:{self.transcript_id} " \
            f"strand:{self.strand} effect:{self.effect} " \
            f"protein pos:{self.prot_pos}/{self.prot_length} " \
            f"aa: {self.aa_change} " \
            f"len: {self.length}"

    def create_effect_details(self):
        """Build effect details."""
        eff_data = [
            (
                [
                    "CNV+",
                    "CNV-",
                ],
                str(self.length)
            ),
            (
                [
                    "noStart",
                    "noEnd",
                    "CDS",
                    "all"
                ],
                str(self.prot_length)
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
                    "tRNA:ANTICODON"
                ],
                str(self.length)
            ),
            (["promoter"], str(self.dist_from_5utr)),
        ]

        return "".join(
            [data for cond, data in eff_data if self.effect in cond]
        )

    @classmethod
    def effect_severity(cls, effect: AnnotationEffect) -> int:
        return AnnotationEffect.SEVERITY[effect.effect]

    @classmethod
    def sort_effects(
            cls, effects: List[AnnotationEffect]) -> List[AnnotationEffect]:
        sorted_effects = sorted(
            effects, key=lambda v: - cls.effect_severity(v))
        return sorted_effects

    @classmethod
    def worst_effect(cls, effects: List[AnnotationEffect]):
        sorted_effects = cls.sort_effects(effects)
        return sorted_effects[0].effect

    @classmethod
    def gene_effects(cls, effects: List[AnnotationEffect]):
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
            sorted_effects, cls.effect_severity
        ):
            for gene, gene_effects in itertools.groupby(
                severity_effects, lambda e: e.gene
            ):
                result.append((gene, next(gene_effects).effect))

        return [[str(r[0]) for r in result], [str(r[1]) for r in result]]

    @classmethod
    def transcript_effects(cls, effects: List[AnnotationEffect]):
        """Build parallel lists of transcripts, genes, effects and details.

        Consider deprecating this.
        """
        # effects = cls.sort_effects(effects)
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
        return (transcripts, genes, gene_effects, details)

    @classmethod
    def simplify_effects(cls, effects: List[AnnotationEffect]):
        """Simplify effects.

        Consider deprecating this.
        """
        if effects[0].effect == "unk_chr":
            return (
                "unk_chr",
                ["unk_chr"],
                ["unk_chr"],
            )

        gene_effects = cls.gene_effects(effects)
        transcript_effects = cls.transcript_effects(effects)

        return (
            cls.worst_effect(effects),
            list(zip(*gene_effects)),
            list(zip(*transcript_effects)))

    @classmethod
    def lgd_gene_effects(cls, effects: List[AnnotationEffect]):
        """Filter and return a mapping of gene to effects by the LGD group."""
        gene_effects = zip(*cls.gene_effects(effects))
        result = []
        for gene_effect in gene_effects:
            for lgd_effect in EffectTypesMixin.EFFECT_GROUPS["lgds"]:
                if gene_effect[1] == lgd_effect.lower():
                    result.append(gene_effect)

        return [[str(r[0]) for r in result], [str(r[1]) for r in result]]

    @classmethod
    def effects_description(cls, effects: List[AnnotationEffect]):
        """Build effects description.

        Condider deprecating this.
        """
        worst_effect, gene_effects, transcript_effects = \
            cls.simplify_effects(effects)

        gene_effects = "|".join([f"{g}:{e}" for g, e in gene_effects])
        transcript_effects = "|".join(
            [f"{t}:{g}:{e}:{d}" for t, g, e, d in transcript_effects]
        )
        return (worst_effect, gene_effects, transcript_effects)


class EffectFactory:
    """Factory class for build annotation effects."""

    @classmethod
    def create_effect(cls, effect_name: str) -> AnnotationEffect:
        return AnnotationEffect(effect_name)

    @classmethod
    def create_effect_with_tm(
        cls, effect_name: str, transcript_model: TranscriptModel
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
        cls, effect_name: str, request: AnnotationRequest
    ) -> AnnotationEffect:
        """Create effect with annotation request."""
        effect = cls.create_effect_with_tm(
            effect_name, request.transcript_model
        )
        effect.mRNA_length = request.get_exonic_length()
        effect.mRNA_position = request.get_exonic_position()
        return effect

    @classmethod
    def create_effect_with_prot_length(
        cls, effect_name: str, request: AnnotationRequest
    ) -> AnnotationEffect:
        effect = cls.create_effect_with_request(effect_name, request)
        effect.prot_length = request.get_protein_length()
        return effect

    @classmethod
    def create_effect_with_prot_pos(
        cls, effect_name: str, request: AnnotationRequest
    ) -> AnnotationEffect:
        effect = cls.create_effect_with_prot_length(effect_name, request)
        start_prot, _ = request.get_protein_position()
        effect.prot_pos = start_prot
        return effect

    @classmethod
    def create_effect_with_aa_change(
        cls, effect_name: str, request: AnnotationRequest
    ) -> AnnotationEffect:
        """Create effect with amino acid change."""
        effect = cls.create_effect_with_prot_pos(effect_name, request)
        # ef.prot_pos, _ = request.get_protein_position()

        ref_aa, alt_aa = request.get_amino_acids()
        effect.aa_change = f"{''.join(ref_aa)}->{''.join(alt_aa)}"

        effect.ref_aa = ref_aa
        effect.alt_aa = alt_aa

        return effect

    @classmethod
    def create_intronic_non_coding_effect(
        cls, effect_type, request, start, end, index
    ):
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
        start: int, end: int, index: int
    ) -> AnnotationEffect:
        """Create intronic effect."""
        effect = cls.create_intronic_non_coding_effect(
            effect_type, request, start, end, index
        )
        if request.transcript_model.strand == "+":
            effect.prot_pos = request.get_protein_position_for_pos(end)
        else:
            effect.prot_pos = request.get_protein_position_for_pos(start)
        return effect


class EffectGene:
    """Combine gene and effect and that gene."""

    def __init__(self, symbol=None, effect=None):
        self.symbol = symbol
        self.effect = effect

    @staticmethod
    def from_string(data):
        """Deserialize effect gene."""
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]
        if len(parts) == 2:
            return EffectGene(parts[0], parts[1])
        if len(parts) == 1:
            return EffectGene(symbol=None, effect=parts[0])

        raise ValueError(f"unexpected effect gene format: {data}")

    def __repr__(self):
        if self.symbol is None:
            return self.effect
        return f"{self.symbol}:{self.effect}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectGene)

        return self.symbol == other.symbol and self.effect == other.effect

    def __hash__(self):
        return hash(tuple([self.symbol, self.effect]))

    @classmethod
    def from_gene_effects(cls, gene_effects):
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_tuple(cls, gene_effect):
        (symbol, effect) = tuple(gene_effect)
        return EffectGene(symbol, effect)


class EffectTranscript:
    """Defines effect transcript."""

    def __init__(self, transcript_id, gene=None, effect=None, details=None):
        self.transcript_id = transcript_id
        self.gene = gene
        self.effect = effect
        self.details = details

    @staticmethod
    def from_string(data):
        """Deserialize effect transcript/details."""
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]

        if len(parts) == 4:
            return EffectTranscript(
                parts[0], gene=parts[1], effect=parts[2], details=parts[3])
        # if len(parts) == 3:
        #     return EffectTranscript(parts[0], gene=parts[1], details=data)
        # if len(parts) == 2:
        #     return EffectTranscript(parts[0], gene=None, details=data)
        raise ValueError(
            f"unexpected effect details format: {data}")

    def __repr__(self):
        return f"{self.transcript_id}:{self.gene}:{self.effect}:{self.details}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectTranscript)

        return (
            self.transcript_id == other.transcript_id
            and self.details == other.details
        )

    @classmethod
    def from_tuple(cls, transcript_tuple):
        (transcript_id, gene, effect, details) = tuple(transcript_tuple)
        return EffectTranscript(
            transcript_id, gene=gene, effect=effect, details=details)

    @classmethod
    def from_effect_transcripts(
            cls, effect_transcripts) -> Dict[str, EffectTranscript]:
        """Build effect transcripts."""
        result = {}
        for transcript_id, details in effect_transcripts:
            parts = [p.strip() for p in details.split(":")]

            if len(parts) == 4:
                result[transcript_id] = EffectTranscript(
                    parts[0], gene=parts[1], effect=parts[2], details=parts[3])
            else:
                result[transcript_id] = EffectTranscript.from_tuple(
                    (transcript_id, None, None, details)
                )
        return result


class AlleleEffects:
    """Class for allele effect used in alleles."""

    def __init__(
            self, worst_effect: str,
            gene_effects: List[EffectGene],
            effect_transcripts):
        self.worst_effect = worst_effect
        self.genes = gene_effects
        self.transcripts = effect_transcripts
        self._effect_types: Optional[list] = None
        self.all_effects: Optional[list[AnnotationEffect]] = None

    @property
    def worst(self):
        return self.worst_effect

    def __repr__(self):
        effects = "|".join([str(g) for g in self.genes])
        transcripts = "|".join([str(t) for t in self.transcripts.values()])
        return f"{self.worst}!{effects}!{transcripts}"

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        assert isinstance(other, AlleleEffects)

        return (
            self.worst == other.worst
            and self.genes == other.genes
            and self.transcripts == other.transcripts
        )

    @property
    def types(self):
        if self._effect_types is None:
            self._effect_types = [eg.effect for eg in self.genes]
        return self._effect_types

    @classmethod
    def from_simplified_effects(
            cls, effect_type,
            effect_genes, transcripts) -> Optional[AlleleEffects]:
        """Build allele effects from simplified effects."""
        if effect_type is None:
            return None

        transcripts = EffectTranscript.from_effect_transcripts(transcripts)
        effect_genes = EffectGene.from_gene_effects(effect_genes)
        return AlleleEffects(effect_type, effect_genes, transcripts)

    @staticmethod
    def from_string(data) -> Optional[AlleleEffects]:
        """Build allele effect from string."""
        if data is None:
            return None
        parts = data.split("!")
        assert len(parts) == 3, parts
        worst = parts[0].strip()
        effect_genes = [
            EffectGene.from_string(eg.strip()) for eg in parts[1].split("|")
        ]
        effect_genes = list(filter(None, effect_genes))
        transcripts_list: List[EffectTranscript] = list(filter(None, [
            EffectTranscript.from_string(et.strip())
            for et in parts[2].split("|")
        ]))
        transcripts = {t.transcript_id: t for t in transcripts_list}
        if not effect_genes and not transcripts:
            return None
        return AlleleEffects(worst, effect_genes, transcripts)

    @classmethod
    def from_effects(cls, effects: List[AnnotationEffect]) -> AlleleEffects:
        """Build allele effects from list of annotation effect."""
        worst_effect, gene_effects, transcript_effects = \
            AnnotationEffect.simplify_effects(effects)
        gene_effects = [EffectGene(g, e) for g, e in gene_effects]
        transcript_effects = {
            t: EffectTranscript(t, g, e, d)
            for t, g, e, d in transcript_effects
        }

        result = AlleleEffects(worst_effect, gene_effects, transcript_effects)
        result.all_effects = effects
        return result
