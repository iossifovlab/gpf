#!/usr/bin/env python

import logging
import pyarrow as pa

from dae.variants.attributes import VariantType
from dae.variants.variant import SummaryAllele
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

    def liftover_variant(self, variant):
        assert isinstance(variant, SummaryAllele)
        if VariantType.is_cnv(variant.variant_type):
            return
        try:
            lo_coordinates = self.chain.convert_coordinate(
                variant.chrom, variant.position,
            )

            if lo_coordinates is None:
                return

            lo_chrom, lo_pos, lo_strand, _ = lo_coordinates
            pos = variant.position
            ref = variant.reference
            alt = variant.alternative

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
            result = SummaryAllele(lo_chrom, lo_pos, lo_ref, lo_alt)
            result.variant_type

            return result
        except Exception as ex:
            logger.warning(f"problem in variant {variant} liftover: {ex}")

    def _do_annotate(self, _, variant, liftover_variants):
        assert self.liftover not in liftover_variants, \
            (self.liftover, liftover_variants)
        assert variant is not None

        lo_variant = self.liftover_variant(variant)
        print(lo_variant)
        if lo_variant is None:
            logger.info(
                f"unable to liftover variant: {variant}")
            return
        liftover_variants[self.liftover] = lo_variant

    def get_default_annotation(self):
        return []

    @property
    def annotation_schema(self) -> pa.Schema:
        return self._annotation_schema
