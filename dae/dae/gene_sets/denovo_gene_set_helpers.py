import logging
import os

import box

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class DenovoGeneSetHelpers:
    """Helper functions for creation of denovo gene sets."""

    @staticmethod
    def denovo_gene_set_cache_file(
        config: box.Box,
        person_set_collection_id: str = "",
    ) -> str:
        """Return the path to the cache file for a person set collection."""
        return os.path.join(
            config.conf_dir,
            "denovo-cache-" + person_set_collection_id + ".json",
        )

    @classmethod
    def load_collection(
        cls,
        study: GenotypeData,
    ) -> DenovoGeneSetCollection | None:
        """Load a denovo gene set collection for a given study."""
        dgsc = DenovoGeneSetCollection.create_empty_collection(study)
        if dgsc is None:
            logger.info(
                "No denovo gene set collection for %s", study.study_id)
            return None
        cache_dir = study.config.conf_dir
        dgsc.load(cache_dir)
        return dgsc

    @classmethod
    def build_collection(
        cls, genotype_data_study: GenotypeData,
    ) -> None:
        """Build a denovo gene set collection for a study and save it."""
        dgsc = DenovoGeneSetCollection.build_collection(
            genotype_data_study,
        )
        if dgsc is None:
            return
        cache_dir = genotype_data_study.config.conf_dir
        dgsc.save(cache_dir)
