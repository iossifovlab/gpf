from __future__ import annotations

import logging

from typing import List, Dict, cast
from dae.genomic_resources.vcf_info_resource import VcfInfoResource
from dae.genomic_resources.repository import GenomicResource
from dae.annotation.annotator_base import Annotator, ATTRIBUTES_SCHEMA
from dae.annotation.annotatable import Annotatable

logger = logging.getLogger(__name__)


def build_vcf_info_annotator(pipeline, config):
    """Construct a VCF INFO field annotator."""
    config = VcfInfoAnnotator.validate_config(config)

    assert config["annotator_type"] == "vcf_info_annotator"

    vcf_info_resource = pipeline.repository.get_resource(
        config["resource_id"]
    )
    if vcf_info_resource is None:
        raise ValueError(
            f"can't create VCF INFO annotator; "
            f"can't find VCF INFO resource {config['resource_id']}")

    return VcfInfoAnnotator(config, vcf_info_resource)


class VcfInfoAnnotator(Annotator):
    """Class for VCF INFO field annotator."""

    ATTRIBUTE_TYPE_MAP = {
        "String": "str",
        "Float": "float",
        "Integer": "int",
    }

    def __init__(self, config: dict, resource: GenomicResource):
        super().__init__(config)

        self.resource = resource
        self.vcf_info = VcfInfoResource(resource)

    def annotator_type(self) -> str:
        return "vcf_info"

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = []
        for attr in self.vcf_info.get_header_info().values():
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
                "allowed": ["vcf_info_annotator"]
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

        logger.debug("validating vcf info annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for vcf_info annotator: %s",
                "validator.errors"
            )
            raise ValueError(
                f"wrong vcf info annotator config {validator.errors}")
        return cast(Dict, validator.document)

    def close(self):
        self.vcf_info.close()

    def is_open(self):
        return self.vcf_info.is_open()

    def open(self) -> VcfInfoAnnotator:
        if self.is_open():
            return self
        self.vcf_info.open()
        return self

    def _do_annotate(self, annotatable: Annotatable, _context: Dict):
        return self.vcf_info.get_variant_info(
            annotatable.chrom, annotatable.pos)
