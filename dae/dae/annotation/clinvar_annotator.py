"""Provides ClinVar annotator."""
from __future__ import annotations

import logging

from typing import List, Dict, cast
from dae.genomic_resources.clinvar import ClinVarVcf
from dae.genomic_resources.repository import GenomicResource
from dae.annotation.annotator_base import Annotator, ATTRIBUTES_SCHEMA
from dae.annotation.annotatable import Annotatable

logger = logging.getLogger(__name__)


def build_clinvar_annotator(pipeline, config):
    """Construct a ClinVar annotator."""
    config = ClinVarAnnotator.validate_config(config)

    assert config["annotator_type"] == "clinvar_annotator"

    clinvar_resource = pipeline.repository.get_resource(
        config["resource_id"]
    )
    if clinvar_resource is None:
        raise ValueError(
            f"can't create ClinVar annotator; "
            f"can't find clinvar resource {config['resource_id']}")

    return ClinVarAnnotator(config, clinvar_resource)


class ClinVarAnnotator(Annotator):
    """
    Class for ClinVar annotator.

    Uses a ClinVarVcf with a ClinVar resource to annotate with data from
    https://ftp.ncbi.nlm.nih.gov/pub/clinvar/
    """

    ATTRIBUTE_TYPE_MAP = {
        "String": "str",
        "Float": "float",
        "Integer": "int",
    }

    def __init__(self, config: dict, resource: GenomicResource):
        super().__init__(config)

        self.resource = resource
        self.clinvar_vcf = ClinVarVcf(resource)

    def annotator_type(self) -> str:
        return "clinvar_annotator"

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = []
        for attr in self.clinvar_vcf.get_header_info().values():
            attr_type = "object"
            if attr["number"] == 1:
                attr_type = self.ATTRIBUTE_TYPE_MAP[cast(str, attr["type"])]
            result.append({
                "name": attr["name"],
                "type": attr_type,
                "desc": attr["description"]
            })
        return result

    def get_annotation_config(self) -> List[Dict]:
        attributes: List[dict] = self.config.get("attributes", [])

        return attributes

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["clinvar_annotator"]
            },
            "input_annotatable": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "resource_id": {"type": "string"},
            "attributes": {
                "type": "list",
                "schema": ATTRIBUTES_SCHEMA
            }
        }

        validator = cls.ConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug("validating clinvar annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for clinvar annotator: %s",
                "validator.errors"
            )
            raise ValueError(
                f"wrong clinvar annotator config {validator.errors}")
        return cast(Dict, validator.document)

    def close(self):
        self.clinvar_vcf.close()

    def is_open(self):
        return self.clinvar_vcf.is_open()

    def open(self) -> ClinVarAnnotator:
        if self.is_open():
            return self
        self.clinvar_vcf.open()
        return self

    def _do_annotate(self, annotatable: Annotatable, _context: Dict):
        return self.clinvar_vcf.get_variant_info(
            annotatable.chrom, annotatable.pos)
