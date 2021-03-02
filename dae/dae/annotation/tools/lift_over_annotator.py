#!/usr/bin/env python
import gzip

import os
import logging

from pyliftover import LiftOver

from dae.variants.attributes import VariantType
from dae.variants.variant import SummaryAllele
from dae.utils.variant_utils import liftover_variant

from dae.annotation.tools.annotator_base import VariantAnnotatorBase
from dae.genome.genome_access import open_ref


logger = logging.getLogger(__name__)


class LiftOverAnnotator(VariantAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(LiftOverAnnotator, self).__init__(config, genomes_db)

        assert self.config.options.liftover
        self.liftover_id = self.config.options.liftover

        self.liftover = self.load_liftover_chain(
            self.config.options.chain_file)
        self.target_genome = self.load_target_genome(
            self.config.options.target_genome)

        logger.debug(
            f"creating liftover annotation: {self.config.options.chain_file}")

    @staticmethod
    def load_liftover_chain(chain_filename):
        assert chain_filename is not None
        assert os.path.exists(chain_filename)

        with gzip.open(chain_filename, "r") as chain_file:
            return LiftOver(chain_file)

    @staticmethod
    def load_target_genome(genome_filename):
        assert genome_filename is not None
        assert os.path.exists(genome_filename)

        return open_ref(genome_filename)

    def liftover_variant(self, variant):
        assert isinstance(variant, SummaryAllele)
        if VariantType.is_cnv(variant.variant_type):
            return
        lo_variant = liftover_variant(
            variant.chrom, variant.position,
            variant.reference, variant.alternative,
            self.liftover, self.target_genome)

        if lo_variant is None:
            return

        lo_chrom, lo_pos, lo_ref, lo_alt = lo_variant
        result = SummaryAllele(lo_chrom, lo_pos, lo_ref, lo_alt)

        return result

    def do_annotate(self, _, variant, liftover_variants):
        assert self.liftover_id not in liftover_variants, \
            (self.liftover_id, liftover_variants)
        assert variant is not None

        lo_variant = self.liftover_variant(variant)
        if lo_variant is None:
            logger.info(
                f"can not liftover variant: {variant}")
            return
        liftover_variants[self.liftover_id] = lo_variant
