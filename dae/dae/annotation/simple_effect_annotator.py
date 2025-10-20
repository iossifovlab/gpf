import logging
import textwrap
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import (
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import (
    AnnotatorBase,
    AttributeDesc,
)
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
    TranscriptModel,
)
from dae.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_resource,
)
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.utils.regions import Region

logger = logging.getLogger(__name__)


def build_simple_effect_annotator(
    pipeline: AnnotationPipeline, info: AnnotatorInfo,
) -> Annotator:
    return SimpleEffectAnnotator(pipeline, info)


@dataclass(eq=True, frozen=True, repr=True, unsafe_hash=True)
class SimpleEffect:
    effect_type: str
    transcript_id: str
    gene: str


class SimpleEffectAnnotator(AnnotatorBase):
    """Simple effect annotator class."""

    @staticmethod
    def effect_types() -> list[str]:
        return [
            "coding",
            "inter-coding_intronic",
            "peripheral",
            "noncoding",
            "intergenic",
        ]

    @staticmethod
    def _classification() -> list[tuple[str, str]]:
        return [
            ("coding", "cds_regions"),
            ("inter-coding_intronic", "cds_intron_regions"),
            ("peripheral", "peripheral_regions"),
            ("noncoding", "noncoding_regions"),
        ]

    @staticmethod
    def _attribute_descriptors() -> dict[str, AttributeDesc]:
        gene_lists = {}
        for effect in SimpleEffectAnnotator.effect_types()[:-1]:
            gene_lists[f"{effect}_gene_list"] = AttributeDesc(
                    name=f"{effect}_gene_list", type="objects",
                    description=f"list of genes with {effect} effect.",
                    internal=False,
                    default=False,
                    params={"effect_type": effect},
                )
            gene_lists[f"{effect}_genes"] = AttributeDesc(
                    name=f"{effect}_genes", type="str",
                    description=f"comma separated list of genes with "
                    f"{effect} effect.",
                    internal=False,
                    default=False,
                    params={"effect_type": effect},
                )

        return {
            "worst_effect": AttributeDesc(
                name="worst_effect", type="str",
                description="The worst effect.",
                internal=False,
                default=True,
            ),
            "worst_effect_genes": AttributeDesc(
                name="worst_effect_genes", type="str",
                description="comma separated list of genes with worst effect.",
                internal=False,
                default=True,
            ),
            "worst_effect_gene_list": AttributeDesc(
                name="worst_effect_gene_list", type="objects",
                description="list of genes with worst effect.",
                internal=False,
                default=False,
            ),
            "gene_list": AttributeDesc(
                name="gene_list", type="objects",
                description="List of all affected genes.",
                internal=True,
                default=False,
            ),
            "genes": AttributeDesc(
                name="genes", type="str",
                description="Comma separated list of all affected genes.",
                internal=False,
                default=False,
            ),
            "gene_effects": AttributeDesc(
                name="gene_effects", type="str",
                description="list of gene:effect pairs.",
                internal=False,
                default=False,
            ),
            "effect_details": AttributeDesc(
                name="effect_details", type="str",
                description="list of transcript:gene:effect tuples.",
                internal=False,
                default=False,
            ),
            **gene_lists,
        }

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        gene_models_resrouce_id = info.parameters.get("gene_models")
        if gene_models_resrouce_id is None:
            gene_models = get_genomic_context().get_gene_models()
            if gene_models is None:
                raise ValueError(
                    f"Can't create {info.type}: "
                    "gene model resource are missing in config "
                    "and context")
        else:
            resource = pipeline.repository.get_resource(
                gene_models_resrouce_id)
            gene_models = build_gene_models_from_resource(resource)
        assert isinstance(gene_models, GeneModels)

        info.documentation += textwrap.dedent(
            """

Simple effect annotator.

<a href="https://iossifovlab.com/gpfuserdocs/administration/annotation.html#simple-effect-annotator" target="_blank">More info</a>

""")  # noqa

        info.resources.append(gene_models.resource)
        super().__init__(
            pipeline,
            info,
            self._attribute_descriptors(),
        )

        self.gene_models = gene_models

    def open(self) -> Annotator:
        self.gene_models.load()
        return super().open()

    def _do_annotate(
        self,
        annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()

        annotation = self.run_annotate(
            annotatable.chrom, annotatable.position, annotatable.end_position)

        result: dict[str, Any] = {}
        gene_list: set[str] = set()
        gene_effects: list[tuple[str, str]] = []
        worst_effect = None
        worst_effect_gene_list: list[str] = []
        details: list[str] = []
        for effect_type in self.effect_types():
            simple_effects = annotation.get(effect_type)
            if simple_effects is not None:
                genes = {se.gene for se in simple_effects}
                if worst_effect is None:
                    worst_effect = effect_type
                    worst_effect_gene_list = sorted(genes)
                result[effect_type + "_gene_list"] = sorted(genes)
                result[effect_type + "_genes"] = ",".join(sorted(genes))
                gene_list = gene_list | genes
                gene_effects.extend(
                    (gene, effect_type) for gene in sorted(genes))
                details.extend(
                    f"{se.transcript_id}:{se.gene}:{se.effect_type}"
                    for se in sorted(
                        simple_effects, key=lambda x: (x.transcript_id)))
        result["gene_list"] = sorted(gene_list)
        result["genes"] = ",".join(sorted(gene_list))
        result["worst_effect"] = worst_effect
        result["worst_effect_genes"] = ",".join(worst_effect_gene_list)
        result["worst_effect_gene_list"] = worst_effect_gene_list
        result["gene_effects"] = "|".join(
            f"{gene}:{effect}" for gene, effect in gene_effects)
        result["effect_details"] = "|".join(details)
        for attr in self.get_info().attributes:
            if attr.source not in result:
                result[attr.source] = None
        return result

    def cds_intron_regions(
        self,
        transcript: TranscriptModel,
    ) -> list[Region]:
        """Return whether region is CDS intron."""
        regions: list[Region] = []

        if not transcript.is_coding():
            return regions
        for index in range(len(transcript.exons) - 1):
            beg = transcript.exons[index].stop + 1
            end = transcript.exons[index + 1].start - 1
            if beg > transcript.cds[0] and end < transcript.cds[1]:
                regions.append(Region(transcript.chrom, beg, end))
        return regions

    def cds_regions(self, transcript: TranscriptModel) -> Sequence[Region]:
        """Return whether the region is classified as coding."""
        return transcript.cds_regions()

    def utr_regions(self, transcript: TranscriptModel) -> Sequence[Region]:
        """Return whether the region is classified as UTR."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        regions = transcript.utr5_regions()
        regions.extend(transcript.utr3_regions())
        return regions

    def peripheral_regions(self, transcript: TranscriptModel) -> list[Region]:
        """Return whether the region is peripheral."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        regions = transcript.utr5_regions()
        regions.extend(transcript.utr3_regions())

        if transcript.cds[0] > transcript.tx[0]:
            region.append(
                Region(
                    transcript.chrom,
                    transcript.tx[0], transcript.cds[0] - 1))

        if transcript.cds[1] < transcript.tx[1]:
            region.append(
                Region(
                    transcript.chrom,
                    transcript.cds[1] + 1, transcript.tx[1]))

        return region

    def noncoding_regions(self, transcript: TranscriptModel) -> list[Region]:
        """Return whether the region is noncoding."""
        region: list[Region] = []
        if transcript.is_coding():
            return region

        region.append(
            Region(
                transcript.chrom,
                transcript.tx[0], transcript.tx[1]))
        return region

    def call_region(
        self,
        chrom: str,
        beg: int,
        end: int,
        tx: TranscriptModel,
        *,
        func_name: str,
        classification: str,
    ) -> SimpleEffect | None:
        """Call a region with a specific classification."""
        regions = getattr(self, func_name)(tx)

        for region in regions:
            assert region.chrom == chrom
            if region.stop >= beg and region.start <= end:
                return SimpleEffect(
                    effect_type=classification,
                    transcript_id=tx.tr_id,
                    gene=tx.gene)
        return None

    def run_annotate(
        self,
        chrom: str,
        beg: int,
        end: int,
    ) -> dict[str, set[SimpleEffect]]:
        """Return classification with a set of affected genes."""
        assert self.gene_models.is_loaded()

        tms = self.gene_models.gene_models_by_location(chrom, beg, end)
        if len(tms) == 0:
            return {"intergenic": set()}

        assert all((beg <= t.tx[1] and end >= t.tx[0]) for t in tms)

        result: dict[str, set[SimpleEffect]] = defaultdict(set)
        for tx in tms:
            for effect_type, func_name in self._classification():
                effect = self.call_region(
                    chrom,
                    beg,
                    end,
                    tx,
                    func_name=func_name,
                    classification=effect_type,
                )
                if effect:
                    result[effect.effect_type].add(effect)
                    break

        return dict(result)
