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
        cls, study: GenotypeData, *,
        force: bool = False,
    ) -> DenovoGeneSetCollection | None:
        """Build a denovo gene set collection for a study and save it."""
        dgsc = DenovoGeneSetCollection.create_empty_collection(study)
        if dgsc is None:
            logger.info(
                "no denovo gene set collection defined for %s", study.study_id)
            return None

        cache_dir = study.config.conf_dir
        if dgsc.is_cached(cache_dir) and not force:
            logger.info(
                "denovo gene set collection for %s already cached",
                study.study_id,
            )
            return dgsc.load(cache_dir)

        dgsc = DenovoGeneSetCollection.build_collection(study)
        if dgsc is None:
            return None
        dgsc.save(cache_dir)
        return dgsc
