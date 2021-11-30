#!/usr/bin/env python

import logging

from typing import Dict

from .annotatable import Annotatable, VCFAllele
from dae.utils.variant_utils import trim_str_left, reverse_complement

from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
from .schema import Schema


logger = logging.getLogger(__name__)


class LiftOverAnnotator(Annotator):
    def __init__(self, config, chain_resource, target_genome):
        super().__init__(config)

        self.chain = chain_resource
        self.target_genome = target_genome

        if self.id is None:
            raise ValueError(
                f"can't create liftover annotator: {self.config}")
        self._annotation_schema = Schema()
        # TODO do somewhere else
        self.chain.open()
        self.target_genome.open()

    @staticmethod
    def annotator_type():
        return "liftover_annotator"

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["liftover_annotator"]
            },
            "id": {
                "type": "string",
                "required": True,
            },
            "chain": {
                "type": "string",
                "required": True,
            },
            "target_genome": {
                "type": "string",
                "required": True,
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_SCHEMA
            }
        }

        validator = cls.ConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug(f"validating effect annotator config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for effect annotator: "
                f"{validator.errors}")
            raise ValueError(
                f"wrong effect annotator config {validator.errors}")
        return validator.document

    def liftover_allele(self, allele: VCFAllele):
        if not isinstance(allele, VCFAllele):
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

            _, tr_ref, tr_alt = trim_str_left(pos, ref, alt)

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

            result = VCFAllele(lo_chrom, lo_pos, lo_ref, lo_alt)

            return result
        except Exception as ex:
            logger.warning(
                f"problem in variant {allele} liftover: {ex}", exc_info=True)

    def _do_annotate(self, _, annotatable: Annotatable, context: Dict):
        assert self.id not in context, \
            (self.id, context)
        assert annotatable is not None

        lo_allele = self.liftover_allele(annotatable)
        if lo_allele is None:
            logger.info(
                f"unable to liftover allele: {annotatable}")
            return
        context[self.id] = lo_allele

    def get_annotation_config(self):
        return []

    @property
    def annotation_schema(self):
        return self._annotation_schema
