from __future__ import annotations

import logging

from dae.annotation.score_annotator import AlleleScoreAnnotator

logger = logging.getLogger(__name__)


def build_vcf_info_annotator(pipeline, config):
    """Construct a VCF INFO field annotator."""
    config = VcfInfoAnnotator.validate_config(config)

    assert config["annotator_type"] == "vcf_info"

    resource = pipeline.repository.get_resource(
        config["resource_id"]
    )
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.vcf_info_score import VcfInfoScore
    vcf_info_score = VcfInfoScore(resource)
    return VcfInfoAnnotator(config, vcf_info_score)


class VcfInfoAnnotator(AlleleScoreAnnotator):
    """Class for VCF INFO field annotator."""

    def annotator_type(self) -> str:
        return "vcf_info"
