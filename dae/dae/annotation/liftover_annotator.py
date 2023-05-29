"""Provides a lift over annotator and helpers."""

import logging

from typing import Any, Optional
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.annotation_pipeline import AttributeInfo

from dae.genomic_resources.reference_genome import \
    ReferenceGenome, build_reference_genome_from_resource
from dae.genomic_resources.liftover_resource import \
    LiftoverChain, build_liftover_chain_from_resource

from dae.utils.variant_utils import trim_str_left
from dae.utils.variant_utils import reverse_complement

from .annotatable import Annotatable, VCFAllele, Region, Position, CNVAllele
from .annotator_base import AnnotatorBase


logger = logging.getLogger(__name__)


def build_liftover_annotator(pipeline: AnnotationPipeline,
                             info: AnnotatorInfo) -> Annotator:
    chain_resource_id = info.parameters.get("chain")
    if chain_resource_id is None:
        raise ValueError("The {into} requires a 'chain' parameter.")
    chain_resource = pipeline.repository.get_resource(chain_resource_id)
    if chain_resource is None:
        raise ValueError(f"The {info} points to a resource "
                         f"{chain_resource_id} that is unavailable.")
    chain = build_liftover_chain_from_resource(chain_resource)

    target_genome_resrouce_id = info.parameters.get("target_genome")
    if target_genome_resrouce_id is None:
        raise ValueError(
            "The {into} requires a 'target_genome' parameter.")
    resource = pipeline.repository.get_resource(target_genome_resrouce_id)
    if resource is None:
        raise ValueError(f"The {info} points to a resource "
                         f"{target_genome_resrouce_id} that is "
                         "unavailable.")
    target_genome = build_reference_genome_from_resource(resource)

    return LiftOverAnnotator(pipeline, info, chain, target_genome)


class LiftOverAnnotator(AnnotatorBase):
    def __init__(self, pipeline: Optional[AnnotationPipeline],
                 info: AnnotatorInfo,
                 chain: LiftoverChain, target_genome: ReferenceGenome):

        info.resources += [chain.resource, target_genome.resource]
        if not info.attributes:
            info.attributes = [AttributeInfo("liftover_annotatable",
                                             "liftover_annotatable", True, {})]
        super().__init__(pipeline, info, {
            "liftover_annotatable": ("object", "Lifted over allele.")
        })
        self.chain = chain
        self.target_genome = target_genome

    def close(self):
        self.target_genome.close()
        self.chain.close()
        super().close()

    def open(self):
        self.target_genome.open()
        self.chain.open()
        return super().open()

    def _do_annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:
        assert annotatable is not None

        if annotatable.type == Annotatable.Type.POSITION:
            value = self.liftover_position(annotatable)
        elif annotatable.type == Annotatable.Type.REGION:
            value = self.liftover_region(annotatable)
        elif annotatable.type in {
                Annotatable.Type.LARGE_DELETION,
                Annotatable.Type.LARGE_DUPLICATION}:
            value = self.liftover_cnv(annotatable)
        else:
            assert isinstance(annotatable, VCFAllele)
            value = self.liftover_allele(annotatable)

        if value is None:
            logger.debug("unable to liftover allele: %s", annotatable)

        return {"liftover_annotatable": value}

    def liftover_allele(self, allele: VCFAllele):
        """Liftover an allele."""
        if not isinstance(allele, VCFAllele):
            return None

        try:
            lo_coordinates = self.chain.convert_coordinate(
                allele.chrom, allele.position,
            )

            if lo_coordinates is None:
                return None

            lo_chrom, lo_pos, lo_strand, _ = lo_coordinates

            if lo_strand == "+" or \
                    len(allele.reference) == len(allele.alternative):
                lo_pos += 1
            elif lo_strand == "-":
                lo_pos -= len(allele.reference)
                lo_pos -= 1

            _, tr_ref, tr_alt = trim_str_left(
                allele.position, allele.reference, allele.alternative)

            lo_ref = self.target_genome.get_sequence(
                lo_chrom, lo_pos, lo_pos + len(allele.reference) - 1)
            if lo_ref is None:
                logger.warning(
                    "can't find genomic sequence for %s:%s", lo_chrom, lo_pos)
                return None

            lo_alt = allele.alternative
            if lo_strand == "-":
                if not tr_alt:
                    lo_alt = f"{lo_ref[0]}"
                else:
                    lo_alt = reverse_complement(tr_alt)
                    if not tr_ref:
                        lo_alt = f"{lo_ref[0]}{lo_alt}"

            result = VCFAllele(lo_chrom, lo_pos, lo_ref, lo_alt)
            if lo_ref == lo_alt:
                logger.warning(
                    "allele %s mapped to no variant: %s", allele, result)
                return None

            return result
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(
                "problem in variant %s liftover: %s",
                allele, ex, exc_info=True)
            return None

    def liftover_position(
        self, position: Annotatable
    ) -> Optional[Annotatable]:
        """Liftover position annotatable."""
        assert isinstance(position, Position)
        lo_coord = self.chain.convert_coordinate(
            position.chrom, position.position,
        )
        if lo_coord is None:
            return None
        return Position(lo_coord[0], lo_coord[1])

    def _do_liftover_region(
        self, region: Annotatable
    ) -> Optional[Annotatable]:
        """Liftover region annotatable."""
        assert isinstance(region, (Region, CNVAllele))
        lo_start = self.chain.convert_coordinate(
            region.chrom, region.position,
        )
        lo_end = self.chain.convert_coordinate(
            region.chrom, region.end_position,
        )

        if lo_start is None or lo_end is None:
            return None
        if lo_start[0] != lo_end[0]:
            return None
        result = Region(
            lo_start[0],
            min(lo_start[1], lo_end[1]),
            max(lo_start[1], lo_end[1]))
        return result

    def liftover_region(self, region: Annotatable) -> Optional[Annotatable]:
        """Liftover region annotatable."""
        assert isinstance(region, Region)
        return self._do_liftover_region(region)

    def liftover_cnv(self, cnv_allele: Annotatable) -> Optional[Annotatable]:
        """Liftover CNV allele annotatable."""
        assert isinstance(cnv_allele, CNVAllele)
        region = self._do_liftover_region(cnv_allele)
        if region is None:
            return None
        return CNVAllele(
            region.chrom, region.pos, region.pos_end, cnv_allele.type)
