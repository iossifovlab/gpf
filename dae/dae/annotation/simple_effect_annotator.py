import logging
from typing import Any

from dae.annotation.annotatable import Annotatable
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
from dae.utils.regions import Region

logger = logging.getLogger(__name__)


def build_simple_effect_annotator(pipeline: AnnotationPipeline,
                                  info: AnnotatorInfo) -> Annotator:
    return SimpleEffectAnnotator(pipeline, info)


class SimpleEffectAnnotator(AnnotatorBase):
    """Simple effect annotator class."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        gene_models_resrouce_id = info.parameters.get("gene_models")
        if gene_models_resrouce_id is None:
            gene_models = get_genomic_context().get_gene_models()
            if gene_models is None:
                raise ValueError(f"Can't create {info.type}: "
                                 "gene model resource are missing in config "
                                 "and context")
        else:
            resource = pipeline.repository.get_resource(
                gene_models_resrouce_id)
            gene_models = build_gene_models_from_resource(resource)
        assert isinstance(gene_models, GeneModels)

        info.resources.append(gene_models.resource)
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                ["effect", "genes"])
        super().__init__(pipeline, info, {
            "effect": ("str", "The worst effect."),
            "genes": ("str", "The affected genes."),
            "gene_list": ("objects", "List of all genes."),
        })

        self.gene_models = gene_models

    def open(self) -> Annotator:
        self.gene_models.load()
        return super().open()

    def _do_annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()

        effect, gene_list = self.run_annotate(
            annotatable.chrom,
            annotatable.position,
            annotatable.end_position)
        genes = ",".join(gene_list)

        return {
            "effect": effect,
            "genes": genes,
            "gene_list": gene_list,
        }

    def cds_intron_regions(
        self, transcript: TranscriptModel,
    ) -> list[Region]:
        """Return whether region is CDS intron."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region
        for index in range(len(transcript.exons) - 1):
            beg = transcript.exons[index].stop + 1
            end = transcript.exons[index + 1].start + 1
            if beg > transcript.cds[0] and end < transcript.cds[1]:
                region.append(Region(transcript.chrom, beg, end))
        return region

    def utr_regions(self, transcript: TranscriptModel) -> list[Region]:
        """Return whether the region is classified as UTR."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        utr5_regions = transcript.utr5_regions()
        utr3_regions = transcript.utr3_regions()
        utr3_regions.extend(utr3_regions)
        return utr5_regions

    def peripheral_regions(self, transcript: TranscriptModel) -> list[Region]:
        """Return whether the region is peripheral."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        if transcript.cds[0] > transcript.tx[0]:
            region.append(
                Region(transcript.chrom, transcript.tx[0],
                       transcript.cds[0] - 1))

        if transcript.cds[1] < transcript.tx[1]:
            region.append(
                Region(transcript.chrom, transcript.cds[1] + 1,
                       transcript.tx[1]))

        return region

    def noncoding_regions(self, transcript: TranscriptModel) -> list[Region]:
        """Return whether the region is noncoding."""
        region: list[Region] = []
        if transcript.is_coding():
            return region

        region.append(
            Region(transcript.chrom, transcript.tx[0],
                   transcript.tx[1]))
        return region

    def call_region(
        self, chrom: str, beg: int, end: int,
        transcripts: list[TranscriptModel],
        func_name: str, classification: str,
    ) -> tuple[str, set[str]] | None:
        """Call a region with a specific classification."""
        genes = set()
        for transcript in transcripts:
            if transcript.gene in genes:
                continue

            regions = []
            if func_name == "CDS_regions":
                regions = transcript.cds_regions()
            else:
                regions = getattr(self, func_name)(transcript)

            for region in regions:
                assert region.chrom == chrom
                if region.stop >= beg and region.start <= end:
                    genes.add(transcript.gene)
                    break
        if genes:
            return classification, genes
        return None

    def run_annotate(
        self, chrom: str, beg: int, end: int,
    ) -> tuple[str, set[str]]:
        """Return classification with a set of affected genes."""
        assert self.gene_models.utr_models is not None
        assert self.gene_models.utr_models[chrom] is not None

        for (start, stop), tms in self.gene_models.utr_models[chrom].items():
            if (beg <= stop and end >= start):

                result = self.call_region(
                    chrom, beg, end, tms, "CDS_regions", "coding")

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "utr_regions", "peripheral")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "cds_intron_regions",
                        "inter-coding_intronic")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "peripheral_regions",
                        "peripheral")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "noncoding_regions", "noncoding")
                else:
                    return result

        return "intergenic", set()
