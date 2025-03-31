from __future__ import annotations

import logging
import textwrap
from typing import Any

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_config import (
    AnnotationConfigParser,
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.gene_models import (
    GeneModels,
    TranscriptModel,
    build_gene_models_from_resource,
)
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)

logger = logging.getLogger(__name__)


def build_spliceai_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return SpliceAIAnnotator(pipeline, info)


class SpliceAIAnnotator(AnnotatorBase):
    """SpliceAI annotator class."""

    def __init__(
        self,
        pipeline: AnnotationPipeline,
        info: AnnotatorInfo,
    ):
        gene_models_resource_id = info.parameters.get("gene_models")
        if gene_models_resource_id is None:
            gene_models = get_genomic_context().get_gene_models()
            if gene_models is None:
                raise ValueError(f"Can't create {info.type}: "
                                 "gene model resource are missing in config "
                                 "and context")
        else:
            resource = pipeline.repository.get_resource(
                gene_models_resource_id)
            gene_models = build_gene_models_from_resource(resource)
        assert isinstance(gene_models, GeneModels)

        genome_resource_id = info.parameters.get("genome") or \
            gene_models.reference_genome_id or \
            (pipeline.preamble.input_reference_genome
             if pipeline.preamble is not None else None)
        if genome_resource_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError(f"The {info} has no reference genome"
                                  " specified and no genome was found"
                                  " in the gene models' configuration,"
                                  " the context or the annotation config's"
                                  " preamble.")
        else:
            genome = build_reference_genome_from_resource_id(
                genome_resource_id, pipeline.repository)
        assert isinstance(genome, ReferenceGenome)


        info.documentation += textwrap.dedent("""

Annotator to use 
<a href="https://www.cell.com/cell/fulltext/S0092-8674(18)31629-5">SpliceAI</a>
models to predict splice site variant effects.

""")  # noqa
        info.resources += [genome.resource, gene_models.resource]
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "delta_score",
            ])

        super().__init__(pipeline, info, {
            "delta_score":
            ("str", "Delta score calculated using SpliceAI models."),
        })

        self.used_attributes = [
            attr.source for attr in self.get_info().attributes
        ]
        self.genome = genome
        self.gene_models = gene_models
        self._distance = int(info.parameters.get("distance", 50))
        if self._distance < 0 or self._distance > 5000:
            logger.warning(
                "distance %s is out of range. "
                "Setting it to 50.", self._distance,
            )
            self._distance = 50
        self._mask = int(info.parameters.get("mask", 0))
        if self._mask not in [0, 1]:
            logger.warning(
                "mask %s is out of range. "
                "Setting it to 0.", self._mask,
            )
            self._mask = 0

    def close(self) -> None:
        self.genome.close()
        super().close()

    def open(self) -> Annotator:
        self.genome.open()
        self.gene_models.load()
        return super().open()

    def _not_found(self, attributes: dict[str, Any]) -> dict[str, Any]:
        attributes.update({
            "delta_score": "-",
        })
        return attributes

    def _width(self) -> int:
        return 10000 + 2 * self._distance + 1

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        result: dict = {}

        if annotatable is None:
            return self._not_found(result)
        if not isinstance(annotatable, VCFAllele):
            return self._not_found(result)
        if any(c in {".", "-", "*", ">", "<"} for c in annotatable.alt):
            return self._not_found(result)
        if len(annotatable.ref) > 2 * self._distance:
            logger.warning(
                "Skipping record (ref too long): %s", annotatable,
            )
            return self._not_found(result)

        transcripts = self.gene_models.gene_models_by_location(
            annotatable.chromosome,
            annotatable.pos,
        )
        if not transcripts:
            return self._not_found(result)

        width = self._width()
        seq = self.genome.get_sequence(
            annotatable.chromosome,
            annotatable.pos - width // 2,
            annotatable.pos + width // 2,
        )
        if len(seq) != width:
            logger.warning(
                "Skipping record (near chromosome end): %s", annotatable,
            )
            return self._not_found(result)
        ref_len = len(annotatable.ref)
        if seq[width // 2: width // 2 + ref_len] != annotatable.ref:
            logger.warning(
                "Skipping record (ref not found): %s", annotatable,
            )
            return self._not_found(result)

        delta_scores: list[str] = []
        for transcript in transcripts:
            if len(annotatable.ref) > 1 or len(annotatable.alt) > 1:
                delta_scores.append(
                    f"{annotatable.alt}|{transcript.gene}|.|.|.|.|.|.|.|.",
                )
                continue
            dist_ann = self._get_pos_data(transcript, annotatable.pos)
            assert dist_ann is not None

        return self._not_found(result)

    def _get_pos_data(
        self, transcript: TranscriptModel,
        pos: int,
    ) -> tuple:
        dist_tx_start = transcript.tx[0] - pos
        dist_tx_end = transcript.tx[1] - pos

        dist_exon_bdry = min(
            *(ex.start - pos for ex in transcript.exons),
            *(ex.stop - pos for ex in transcript.exons),
            key=abs)
        return dist_tx_start, dist_tx_end, dist_exon_bdry
