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
        raise ValueError(f"The {info} requires a 'chain' parameter.")
    chain_resource = pipeline.repository.get_resource(chain_resource_id)
    if chain_resource is None:
        raise ValueError(f"The {info} points to a resource "
                         f"{chain_resource_id} that is unavailable.")
    chain = build_liftover_chain_from_resource(chain_resource)

    resource_id = info.parameters.get("target_genome")
    if resource_id is None:
        raise ValueError(
            f"The {info} requires a 'target_genome' parameter.")
    resource = pipeline.repository.get_resource(resource_id)
    if resource is None:
        raise ValueError(f"The {info} points to a resource "
                         f"{resource_id} that is "
                         "unavailable.")
    target_genome = build_reference_genome_from_resource(resource)

    resource_id = info.parameters.get("source_genome")
    if resource_id is None:
        raise ValueError(
            f"The {info} requires a 'source_genome' parameter.")
    resource = pipeline.repository.get_resource(resource_id)
    if resource is None:
        raise ValueError(f"The {info} points to a resource "
                         f"{resource_id} that is "
                         "unavailable.")
    source_genome = build_reference_genome_from_resource(resource)
    basic_liftover = info.parameters.get("basic_liftover", False)
    return LiftOverAnnotator(
        pipeline, info,
        chain, source_genome, target_genome,
        basic_liftover=basic_liftover,
    )


class LiftOverAnnotator(AnnotatorBase):
    """Liftovver annotator class."""

    def __init__(
        self, pipeline: Optional[AnnotationPipeline],
        info: AnnotatorInfo,
        chain: LiftoverChain,
        source_genome: ReferenceGenome,
        target_genome: ReferenceGenome,
        *,
        basic_liftover: bool = False,
    ):

        info.resources += [
            chain.resource, source_genome.resource, target_genome.resource]
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
        self.source_genome = source_genome
        self.target_genome = target_genome
        self.basic_liftover = basic_liftover

    def close(self) -> None:
        self.target_genome.close()
        self.chain.close()
        super().close()

    def open(self) -> Annotator:
        self.source_genome.open()
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
            if self.basic_liftover:
                lo_allele = basic_liftover_allele(
                    allele.chrom, allele.position,
                    allele.reference, allele.alternative,
                    self.chain, self.target_genome,
                )
            else:
                lo_allele = liftover_allele(
                    allele.chrom, allele.position,
                    allele.reference, allele.alternative,
                    self.chain, self.source_genome, self.target_genome,
                )

            if lo_allele is None:
                return None

            lo_chrom, lo_pos, lo_ref, lo_alt = lo_allele
            result = VCFAllele(lo_chrom, lo_pos, lo_ref, lo_alt)

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


def _liftover_snp_simple(
    lo_coordinates: tuple[str, int, str, int],
    nref: str,
    nalt: str,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, str]]:
    tchrom, tpos, tstrand, _ = lo_coordinates
    tseq = target_genome.get_sequence(tchrom, tpos, tpos)
    if tstrand == "-":
        tseq = reverse_complement(tseq)
    if tseq == nref:
        tref = tseq
        talt = nalt
    elif tseq == nalt:
        tref = tseq
        talt = nref
    else:
        return None
    nchrom, npos, nref, nalts = normalize_variant(
        tchrom, tpos, tref, [talt], target_genome)
    return nchrom, npos, nref, nalts[0]


_LO_LENGTH_CHANGE_CUTOFF = 10


def _liftover_sequence(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    liftover_chain: LiftoverChain,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, str]]:
    slen = len(ref)
    anchor_5prime = pos
    anchor_3prime = pos + slen - 1
    lo_anchor_5prime = liftover_chain.convert_coordinate(chrom, anchor_5prime)
    lo_anchor_3prime = liftover_chain.convert_coordinate(chrom, anchor_3prime)
    if lo_anchor_5prime is None or lo_anchor_3prime is None:
        logger.debug(
            "liftover anchors not found: %s:%d-%d",
            chrom, anchor_5prime, anchor_3prime,
        )
        return None

    # check if the anchors are on the same chromosome and strand
    if lo_anchor_5prime[0] != lo_anchor_3prime[0] or \
            lo_anchor_5prime[2] != lo_anchor_3prime[2]:
        logger.debug(
            "liftover anchors are on different chromosomes or strands: "
            "%s:%d-%d %s:%d %s:%d", chrom, anchor_5prime, anchor_3prime,
            lo_anchor_5prime[0], lo_anchor_5prime[1],
            lo_anchor_3prime[0], lo_anchor_3prime[1],
        )
        return None
    tchrom = lo_anchor_5prime[0]
    tpos = min(lo_anchor_5prime[1], lo_anchor_3prime[1])
    tend = max(lo_anchor_5prime[1], lo_anchor_3prime[1])

    if lo_anchor_5prime[2] == "-":
        assert lo_anchor_3prime[2] == "-"
        ref = reverse_complement(ref)
        alt = reverse_complement(alt)
    tlen = tend - tpos + 1
    if tlen > _LO_LENGTH_CHANGE_CUTOFF * slen:
        logger.debug(
            "liftover allele length changed too much: %s:%d %s>%s; "
            "source length: %d, target length: %d",
            chrom, pos, ref, alt, slen, tlen)
        return None

    tseq = target_genome.get_sequence(tchrom, tpos, tend)

    if tseq == ref:
        tref = ref
        talt = alt
        return tchrom, tpos, tref, talt
    if tseq == alt:
        tref = tseq
        talt = ref
        return tchrom, tpos, tref, talt

    return None


def liftover_allele(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    liftover_chain: LiftoverChain,
    source_genome: ReferenceGenome,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, str]]:
    """Liftover a variant."""
    nchrom, npos, nref, nalts = normalize_variant(
        chrom, pos, ref, [alt], source_genome)
    assert len(nalts) == 1

    if len(nref) == 1 and len(nalts[0]) == 1:
        # liftover substitution
        lo_coordinates = liftover_chain.convert_coordinate(nchrom, npos)
        if lo_coordinates is not None:
            return _liftover_snp_simple(
                lo_coordinates, nref, nalts[0], target_genome)

    mchrom, mpos, mref, malts = maximally_extend_variant(
        nchrom, npos, nref, nalts, source_genome)
    malt = malts[0]

    lo_variant = _liftover_sequence(
        mchrom, mpos, mref, malt, liftover_chain, target_genome)
    if lo_variant is None:
        lo_variant = _liftover_sequence(
            mchrom, mpos, malt, mref, liftover_chain, target_genome)
        if lo_variant is None:
            return None
    tchrom, tpos, tref, talt = lo_variant
    nchrom, npos, nref, nalts = normalize_variant(
        tchrom, tpos, tref, [talt], target_genome)
    return nchrom, npos, nref, nalts[0]


def liftover_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    liftover_chain: LiftoverChain,
    source_genome: ReferenceGenome,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, list[str]]]:
    """Liftover a variant."""
    lo_alleles: list[tuple[str, int, str, str]] = []
    for alt in alts:
        lo_allele = liftover_allele(
            chrom, pos, ref, alt,
            liftover_chain, source_genome, target_genome,
        )
        if lo_allele is None:
            return None
        lo_alleles.append(lo_allele)
    if not all(
            chrom == lo_alleles[0][0] for chrom, _, _, _ in lo_alleles):
        return None

    if not all(
            pos == lo_alleles[0][1] for _, pos, _, _ in lo_alleles):
        return None

    max_ref = max(len(ref) for _, _, ref, _ in lo_alleles)
    r_alleles: list[tuple[str, int, str, str]] = []
    for allele in lo_alleles:
        if len(allele[2]) == max_ref:
            r_alleles.append(allele)
            continue
        chrom, pos, ref, alt = allele
        fill_start = pos + len(ref)
        fill_end = pos + max_ref - 1
        fill_seq = target_genome.get_sequence(chrom, fill_start, fill_end)
        fill_ref = f"{ref}{fill_seq}"
        fill_alt = f"{alt}{fill_seq}"
        assert len(fill_ref) == max_ref
        r_alleles.append((chrom, pos, fill_ref, fill_alt))
    assert all(ref == r_alleles[0][2] for _, _, ref, _ in r_alleles)
    chrom, pos, ref, _ = r_alleles[0]
    return chrom, pos, ref, [alt for _, _, _, alt in r_alleles]


def basic_liftover_allele(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    liftover_chain: LiftoverChain,
    target_genome: ReferenceGenome,
) -> Optional[tuple[str, int, str, str]]:
    """Basic liftover an allele."""

    lo_coordinates = liftover_chain.convert_coordinate(
        chrom, pos,
    )

    if lo_coordinates is None:
        return None

    lo_chrom, lo_pos, lo_strand, _ = lo_coordinates

    if lo_strand == "+" or \
            len(ref) == len(alt):
        lo_pos += 1
    elif lo_strand == "-":
        lo_pos -= len(ref)
        lo_pos -= 1

    _, tr_ref, tr_alt = trim_str_left(pos, ref, alt)

    lo_ref = target_genome.get_sequence(
        lo_chrom, lo_pos, lo_pos + len(ref) - 1)
    if lo_ref is None:
        logger.warning(
            "can't find genomic sequence for %s:%s", lo_chrom, lo_pos)
        return None

    lo_alt = alt
    if lo_strand == "-":
        if not tr_alt:
            lo_alt = f"{lo_ref[0]}"
        else:
            lo_alt = reverse_complement(tr_alt)
            if not tr_ref:
                lo_alt = f"{lo_ref[0]}{lo_alt}"

    if lo_ref == lo_alt:
        logger.warning(
            "allele %s:%d %s>%s mapped to no variant: %s:%d %s>%s",
            chrom, pos, ref, alt,
            lo_chrom, lo_pos, lo_ref, lo_alt)
        return None

    return lo_chrom, lo_pos, lo_ref, lo_alt
