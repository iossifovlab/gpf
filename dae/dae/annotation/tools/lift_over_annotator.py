#!/usr/bin/env python

import logging
import pyarrow as pa

from dae.variants.core import Allele
from dae.utils.variant_utils import trim_str_front, reverse_complement

from dae.annotation.tools.annotator_base import Annotator


logger = logging.getLogger(__name__)


class LiftOverAnnotator(Annotator):
    def __init__(
        self, chain_resource, genome_resource,
        liftover, override=None
    ):
        super().__init__(liftover, override)

        self.chain = chain_resource
        self.target_genome = genome_resource
        self._annotation_schema = pa.schema([])
        # TODO do somewhere else
        self.chain.open()
        self.target_genome.open()

    def liftover_allele(self, allele):
        assert isinstance(allele, Allele)
        if Allele.Type.cnv & allele.allele_type:
            return
        try:
            lo_coordinates = self.chain.convert_coordinate(
                allele.chrom, allele.position,
            )

            if lo_coordinates is None:
                return

            lo_chrom, lo_pos, lo_strand, _ = lo_coordinates
            pos = allele.position
            ref = allele.reference
            alt = allele.alternative

            if lo_strand == "+" or len(ref) == len(alt):
                lo_pos += 1
            elif lo_strand == "-":
                lo_pos -= len(ref)
                lo_pos -= 1

            _, tr_ref, tr_alt = trim_str_front(pos, ref, alt)

            lo_ref = self.target_genome.get_sequence(
                lo_chrom, lo_pos, lo_pos + len(ref) - 1)
            if lo_ref is None:
                logger.warning(
                    f"can't find genomic sequence for {lo_chrom}:{lo_pos}")
                return None

            lo_alt = alt
            if lo_strand == "-":
                if not tr_alt:
                    lo_alt = f"{lo_ref[0]}"
                else:
                    lo_alt = reverse_complement(tr_alt)
                    if not tr_ref:
                        lo_alt = f"{lo_ref[0]}{lo_alt}"

            print("==")
            print(lo_chrom)
            print(lo_pos)
            print(lo_ref)
            print(lo_alt)
            result = Allele.build_vcf_allele(lo_chrom, lo_pos, lo_ref, lo_alt)

            return result
        except Exception as ex:
            logger.warning(
                f"problem in variant {allele} liftover: {ex}", exc_info=True)

    def _do_annotate_allele(self, _, allele, liftover_context):
        assert self.liftover not in liftover_context, \
            (self.liftover, liftover_context)
        assert allele is not None

        lo_allele = self.liftover_allele(allele)
        if lo_allele is None:
            logger.info(
                f"unable to liftover allele: {allele}")
            return
        liftover_context[self.liftover] = lo_allele

    def get_default_annotation(self):
        return []

    @property
    def annotation_schema(self) -> pa.Schema:
        return self._annotation_schema
