"""Provides a lift over annotator and helpers."""

import logging
import copy

from typing import Optional, cast
from dae.genomic_resources.reference_genome import \
    ReferenceGenome, build_reference_genome_from_resource
from dae.genomic_resources.liftover_resource import \
    LiftoverChain, build_liftover_chain_from_resource

from dae.utils.variant_utils import trim_str_left, reverse_complement

from .annotatable import Annotatable, VCFAllele, Region, Position, CNVAllele
from .annotator_base import AnnotatorBase, ATTRIBUTES_SCHEMA


logger = logging.getLogger(__name__)


def build_liftover_annotator(pipeline, config):
    """Construct a liftover annotator."""
    config = LiftOverAnnotator.validate_config(config)

    assert config["annotator_type"] == "liftover_annotator"

    chain_resource = pipeline.repository.get_resource(config["chain"])
    if chain_resource is None:
        raise ValueError(
            f"can't create liftover annotator; "
            f"can't find liftover chain {config.chain}")

    resource = pipeline.repository.get_resource(
        config["target_genome"])
    if resource is None:
        raise ValueError(
            f"can't create liftover annotator; "
            f"can't find liftover target genome: "
            f"{config.target_genome}")
    target_genome: ReferenceGenome = \
        build_reference_genome_from_resource(resource)
    liftover_chain: LiftoverChain = \
        build_liftover_chain_from_resource(chain_resource)
    return LiftOverAnnotator(config, liftover_chain, target_genome)


class LiftOverAnnotator(AnnotatorBase):
    """Defines a Lift Over annotator."""

    def __init__(
            self, config: dict,
            chain: LiftoverChain, target_genome: ReferenceGenome):
        super().__init__(config)

        self.chain: LiftoverChain = chain
        self.target_genome: ReferenceGenome = target_genome
        self._annotation_schema = None

    def annotator_type(self) -> str:
        return "liftover_annotator"

    def close(self):
        # FIXME: consider using weekrefs
        # self.target_genome.close()
        # self.chain.close()
        pass

    def open(self):
        self.target_genome.open()
        self.chain.open()
        return self

    def is_open(self):
        return self.target_genome.is_open() and self.chain.is_open()

    DEFAULT_ANNOTATION = {
        "attributes": [
            {
                "source": "liftover_annotatable",
                "destination": "liftover_annotatable",
                "internal": True,
            },
        ]
    }

    def get_all_annotation_attributes(self) -> list[dict]:
        return [
            {
                "name": "liftover_annotatable",
                "type": "object",
                "desc": "liftover allele",
            }
        ]

    @property
    def resources(self):
        return {
            self.chain.resource.resource_id,
            self.target_genome.resource_id
        }

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["liftover_annotator"]
            },
            "input_annotatable": {
                "type": "string",
                "nullable": True,
                "default": None,
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

        logger.debug("validating liftover annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for liftover annotator: %s",
                validator.errors)
            raise ValueError(
                f"wrong liftover annotator config {validator.errors}")
        return cast(dict, validator.document)

    def get_annotation_config(self) -> list[dict]:
        attributes: Optional[list[dict]] = self.config.get("attributes")
        if attributes:
            return attributes
        attributes = copy.deepcopy(self.DEFAULT_ANNOTATION["attributes"])
        return attributes

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

    def _do_annotate(self, annotatable: Annotatable, _context: dict):
        assert annotatable is not None
        if annotatable.type == Annotatable.Type.POSITION:
            return {
                "liftover_annotatable": self.liftover_position(annotatable)
            }
        if annotatable.type == Annotatable.Type.REGION:
            return {
                "liftover_annotatable": self.liftover_region(annotatable)
            }
        if annotatable.type in {
                Annotatable.Type.LARGE_DELETION,
                Annotatable.Type.LARGE_DUPLICATION}:
            return {
                "liftover_annotatable": self.liftover_cnv(annotatable)}

        lo_allele = self.liftover_allele(cast(VCFAllele, annotatable))
        if lo_allele is None:
            logger.debug(
                "unable to liftover allele: %s", annotatable)
            return {"liftover_annotatable": None}

        return {"liftover_annotatable": lo_allele}
