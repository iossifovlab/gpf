import logging
import copy

from typing import Dict, List
from box import Box

from .annotatable import Annotatable, VCFAllele
from dae.utils.variant_utils import trim_str_left, reverse_complement

from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
from .schema import Schema


logger = logging.getLogger(__name__)


def build_liftover_annotator(pipeline, config):
    config = LiftOverAnnotator.validate_config(config)

    assert config.annotator_type == "liftover_annotator"

    chain = pipeline.repository.get_resource(config.chain)
    if chain is None:
        raise ValueError(
            f"can't create liftover annotator; "
            f"can't find liftover chain {config.chain}")

    target_genome = pipeline.repository.get_resource(config.target_genome)
    if target_genome is None:
        raise ValueError(
            f"can't create liftover annotator; "
            f"can't find liftover target genome: "
            f"{config.target_genome}")

    return LiftOverAnnotator(config, chain, target_genome)


class LiftOverAnnotator(Annotator):

    def __init__(self, config, chain_resource, target_genome):
        super().__init__(config)

        self.chain = chain_resource
        self.target_genome = target_genome

        # TODO do somewhere else
        self.chain.open()
        self.target_genome.open()
        self._annotation_schema = None

    @staticmethod
    def annotator_type():
        return "liftover_annotator"

    DEFAULT_ANNOTATION = Box({
        "attributes": [
            {
                "source": "liftover_annotatable",
                "destination": "liftover_annotatable",
                "internal": True,
            },
        ]
    })

    def get_all_annotation_attributes(self) -> List[Dict]:
        return [
            {
                "source": "liftover_annotatable",
                "type": "object",
                "desc": "liftover annotatable"
            }
        ]

    class LiftoverSource(Schema.Source):
        def __init__(
                self, chain: str, target_genome: str):
            super().__init__("liftover_annotator", chain)
            self.target_genome = target_genome

        def __repr__(self):
            repr = [super().__repr__(), self.target_genome]
            return "; ".join(repr)

    @property
    def annotation_schema(self):
        if self._annotation_schema is None:
            schema = Schema()
            for attr in self.get_annotation_config():
                source = LiftOverAnnotator.LiftoverSource(
                    self.chain.resource_id, self.target_genome.resource_id)
                schema.create_field(
                    attr.destination,
                    "object",
                    attr.get("internal", False),
                    source
                )
            self._annotation_schema = schema
        return self._annotation_schema

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
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

        logger.debug(f"validating effect annotator config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for effect annotator: "
                f"{validator.errors}")
            raise ValueError(
                f"wrong effect annotator config {validator.errors}")
        return validator.document

    def get_annotation_config(self) -> List[Dict]:
        attributes = self.config.get("attributes")
        if attributes:
            return attributes
        attributes = copy.deepcopy(self.DEFAULT_ANNOTATION.attributes)
        logger.info(
            f"using default annotation for liftover "
            f"{self.config.get('chain')}: "
            f"{attributes}")
        return attributes

    def liftover_allele(self, allele: VCFAllele):
        if not isinstance(allele, VCFAllele):
            return

        try:
            lo_coordinates = self.chain.convert_coordinate(
                allele.chrom, allele.position,
            )

            if lo_coordinates is None:
                return {}

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
                return {}

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

    def _do_annotate(self, annotatable: Annotatable, _context: Dict):
        assert annotatable is not None

        lo_allele = self.liftover_allele(annotatable)
        if lo_allele is None:
            logger.info(
                f"unable to liftover allele: {annotatable}")
            return {}

        return {"liftover_annotatable": lo_allele}
