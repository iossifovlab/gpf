import logging

from typing import List, Dict, Optional, cast

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource

from .annotatable import Annotatable, VCFAllele
from .annotator_base import Annotator, ATTRIBUTES_SCHEMA

logger = logging.getLogger(__name__)


def normalize_allele(allele: VCFAllele, genome: ReferenceGenome) -> VCFAllele:
    """
    Using algorithm defined in
    following https://genome.sph.umich.edu/wiki/Variant_Normalization
    """
    while True:
        changed = False

        if len(allele.ref) > 0 and len(allele.alt) > 0 \
                and allele.ref[-1] == allele.alt[-1]:
            allele = VCFAllele(
                allele.chrom, allele.pos, allele.ref[:-1], allele.alt[:-1])
            changed = True

        if len(allele.ref) == 0 or len(allele.alt) == 0:
            left = genome.get_sequence(
                allele.chrom, allele.pos - 1, allele.pos - 1)
            allele = VCFAllele(
                allele.chrom, allele.pos - 1,
                f"{left}{allele.ref}", f"{left}{allele.alt}")
            changed = True

        if not changed:
            break

    while len(allele.ref) >= 2 and len(allele.alt) >= 2 \
            and allele.ref[0] == allele.alt[0]:
        allele = VCFAllele(
            allele.chrom, allele.pos + 1, allele.ref[1:], allele.alt[1:])

    return allele


def build_normalize_allele_annotator(pipeline, config):
    config = NormalizeAlleleAnnotator.validate_config(config)

    assert config["annotator_type"] == "normalize_allele_annotator"

    genome_resource = pipeline.repository.get_resource(config["genome"])
    if genome_resource is None:
        raise ValueError(
            f"can't create normalize allele annotator; "
            f"can't find reference genome: "
            f"{config['genome']}"
        )
    genome = open_reference_genome_from_resource(genome_resource)
    return NormalizeAlleleAnnotator(config, genome)


class NormalizeAlleleAnnotator(Annotator):

    def __init__(self, config, genome: ReferenceGenome):
        super().__init__(config)

        self.genome = genome
        self._annotation_schema = None

    def annotator_type(self) -> str:
        return "normalize_allele_annotator"

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["normalize_allele_annotator"]
            },
            "input_annotatable": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "genome": {
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

        logger.debug(f"validating normalize allele annotator config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for normalize allele annotator: "
                f"{validator.errors}")
            raise ValueError(
                f"wrong liftover annotator config {validator.errors}")
        return cast(Dict, validator.document)

    def get_all_annotation_attributes(self) -> List[Dict]:
        return [
            {
                "name": "normalized_allele",
                "type": "object",
                "desc": "normalized allele",
            }
        ]

    def get_annotation_config(self) -> List[Dict]:
        attributes: Optional[List[Dict]] = self.config.get("attributes")
        if attributes:
            return attributes
        attributes = [
            {
                "source": "normalized_allele",
                "destination": "normalized_allele",
                "internal": True,
            }
        ]
        logger.info(
            f"using default annotation for normalized allele: "
            f"{attributes}")
        return attributes

    def _do_annotate(
            self, annotatable: Annotatable, _context: Dict) -> Dict:

        assert isinstance(annotatable, VCFAllele), annotatable
        if annotatable.type in {
                Annotatable.Type.large_deletion,
                Annotatable.Type.large_duplication}:
            logger.warning(
                f"{self.annotator_type()} not ready to annotate CNV variants: "
                f"{annotatable}")
            return {}

        normalized_allele = normalize_allele(annotatable, self.genome)
        return {"normalized_allele": normalized_allele}
