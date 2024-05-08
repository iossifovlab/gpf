"""Provides a lift over annotator and helpers."""

import logging
from typing import Any, Optional

from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.genomic_resources.liftover_chain import (
    LiftoverChain,
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.variant_utils import (
    maximally_extend_variant,
    normalize_variant,
)
from dae.utils.variant_utils import reverse_complement, trim_str_left

from .annotatable import Annotatable, CNVAllele, Position, Region, VCFAllele
from .annotator_base import AnnotatorBase

logger = logging.getLogger(__name__)


def build_liftover_annotator(pipeline: AnnotationPipeline,
                             info: AnnotatorInfo) -> Annotator:
    """Create a liftover annotator."""
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
    """Liftovver annotator class."""

    def __init__(self, pipeline: Optional[AnnotationPipeline],
                 info: AnnotatorInfo,
                 chain: LiftoverChain, target_genome: ReferenceGenome):

        info.resources += [chain.resource, target_genome.resource]
        if not info.attributes:
            info.attributes = [AttributeInfo(
                "liftover_annotatable",
                "liftover_annotatable",
                True,  # noqa FTB003
                {},
            )]
        super().__init__(pipeline, info, {
            "liftover_annotatable": ("annotatable", "Lifted over allele."),
        })
        self.chain = chain
        self.target_genome = target_genome

    def close(self) -> None:
        self.target_genome.close()
        self.chain.close()
        super().close()

    def open(self) -> Annotator:
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

    def liftover_allele(self, allele: VCFAllele) -> Optional[VCFAllele]:
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
                pass
            elif lo_strand == "-":
                lo_pos -= len(allele.reference)

            _tr_pos, tr_ref, tr_alt = trim_str_left(
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
                    "allele %s mapped to no variant: %s; liftover strand: %s;",
                    allele, result, lo_strand)
                return None

        except BaseException as ex:  # noqa BLE001 pylint: disable=broad-except
            logger.warning(
                "problem in variant %s liftover: %s",
                allele, ex, exc_info=True)
            return None

        return result

    def liftover_position(
        self, position: Annotatable,
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
        self, region: Annotatable,
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
            logger.error(
                "unable to liftover start or end of the region: %s", region)
            return None

        if lo_start[0] != lo_end[0]:
            logger.error(
                "lifted over region spans multiple chroms: %s -> (%s, %s)",
                region, lo_start[0], lo_end[0])
            return None

        return Region(
            lo_start[0],
            min(lo_start[1], lo_end[1]),
            max(lo_start[1], lo_end[1]))

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


def liftover_allele(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    liftover_chain: LiftoverChain,
    source_genome: ReferenceGenome,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, list[str]]]:
    """Liftover a variant."""
    nchrom, npos, nref, nalts = normalize_variant(
        chrom, pos, ref, [alt], source_genome)
    assert len(nalts) == 1

    if len(nref) == 1 and len(nalts[0]) == 1:
        # liftover substitution
        lo_coordinates = liftover_chain.convert_coordinate(nchrom, npos)
        if lo_coordinates is not None:
            tchrom, tpos, tstrand, _ = lo_coordinates
            tref = target_genome.get_sequence(tchrom, tpos, tpos)
            if tstrand == "-":
                tref = reverse_complement(tref)
            if tref == nref:
                talt = nalts[0]
            elif tref == nalts[0]:
                talt = nref
            return normalize_variant(tchrom, tpos, tref, [talt], target_genome)

    mchrom, mpos, mref, malts = maximally_extend_variant(
        nchrom, npos, nref, nalts, source_genome)
    malt = malts[0]

    anchor_5prime = mpos
    anchor_3prime = mpos + max(len(mref), len(malts[0])) - 1
    lo_anchor_5prime = liftover_chain.convert_coordinate(mchrom, anchor_5prime)
    lo_anchor_3prime = liftover_chain.convert_coordinate(mchrom, anchor_3prime)
    if lo_anchor_5prime is None or lo_anchor_3prime is None:
        return None
    if lo_anchor_5prime[0] != lo_anchor_3prime[0]:
        return None
    tchrom = lo_anchor_5prime[0]
    tpos = min(lo_anchor_5prime[1], lo_anchor_3prime[1])
    tend = max(lo_anchor_5prime[1], lo_anchor_3prime[1])

    tstrand = "+"
    if lo_anchor_5prime[2] == "-":
        assert lo_anchor_3prime[2] == "-"
        tstrand = "-"
        mref = reverse_complement(mref)
        malt = reverse_complement(malt)

    tseq = target_genome.get_sequence(tchrom, tpos, tend)

    mlength = min(len(mref), len(malt))
    mdiff = max(len(mref), len(malt)) - mlength

    if mref in tseq:
        talt = malt
        if tstrand == "+":
            tref = tseq[:mlength]
        else:
            tref = tseq[mdiff:]
            tpos += mdiff
    elif malt in tseq:
        talt = mref
        if tstrand == "+":
            tref = tseq[:mlength]
        else:
            tref = tseq[mdiff:]
            tpos += mdiff
    else:
        return None

    return normalize_variant(tchrom, tpos, tref, [talt], target_genome)
