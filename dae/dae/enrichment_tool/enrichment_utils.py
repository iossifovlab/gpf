import os
from typing import cast

from box import Box

from dae.studies.study import GenotypeData

EnrichmentEventCounts = dict[str, dict[str, dict[str, dict[str, int]]]]


def get_enrichment_config(
    genotype_data: GenotypeData,
) -> Box | None:
    return cast(
        Box | None,
        genotype_data.config.get("enrichment"),
    )


def get_enrichment_cache_path(study: GenotypeData) -> str:
    return os.path.join(study.config_dir, "enrichment_cache.json")
