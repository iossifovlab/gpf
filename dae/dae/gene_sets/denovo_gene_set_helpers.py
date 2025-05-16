import logging

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class DenovoGeneSetHelpers:
    """Helper functions for creation of denovo gene sets."""

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
    def load_collection_from_dict(
        cls,
        study: GenotypeData,
        cache: dict,
    ) -> DenovoGeneSetCollection | None:
        """Load a denovo gene set collection for a given study."""
        dgsc = DenovoGeneSetCollection.create_empty_collection(study)
        if dgsc is None:
            logger.info(
                "No denovo gene set collection for %s", study.study_id)
            return None
        dgsc.cache = cache
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
