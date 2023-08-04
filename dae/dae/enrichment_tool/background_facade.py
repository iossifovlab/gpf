from typing import Optional, cast
from collections import defaultdict

from box import Box

from dae.enrichment_tool.background import BackgroundBase
from dae.studies.variants_db import VariantsDb


class BackgroundFacade:
    """Facade to create and find enrichment background."""

    def __init__(self, variants_db: VariantsDb):
        self._background_cache: dict[str, dict[str, BackgroundBase]] = \
            defaultdict(dict)
        self._enrichment_config_cache: dict[str, Box] = {}

        self.variants_db = variants_db

    def load_cache(self, study_ids: Optional[set[str]] = None) -> None:
        """Load all enrichment background into an in-memory cache."""
        if study_ids is None:
            study_ids = set(self.variants_db.get_all_ids())

        cached_ids = set(self._enrichment_config_cache.keys()) & set(
            self._background_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                enrichment_config = self._load_enrichment_config_in_cache(
                    study_id
                )
                if enrichment_config is None:
                    continue
                for background_id in enrichment_config.\
                        selected_background_values:
                    self._load_background_in_cache(study_id, background_id)

    def _load_enrichment_config_in_cache(self, study_id: str) -> Optional[Box]:
        if study_id in self._enrichment_config_cache:
            return self._enrichment_config_cache[study_id]

        genotype_data_config = self.variants_db.get_config(study_id)
        if genotype_data_config is None \
                or genotype_data_config.enrichment is None:
            return None

        if not genotype_data_config.enrichment.enabled:
            return None

        self._enrichment_config_cache[study_id] = \
            genotype_data_config.enrichment

        return cast(Box, genotype_data_config.enrichment)

    def _load_background_in_cache(
            self, study_id: str, background_id: str) -> None:
        enrichment_config = self._load_enrichment_config_in_cache(study_id)
        if enrichment_config is None:
            return
        if background_id not in enrichment_config.selected_background_values:
            return
        background_config = getattr(
            enrichment_config.background, background_id
        )

        self._background_cache[study_id][
            background_id
        ] = BackgroundBase.build_background(
            background_config.kind, enrichment_config
        )

    def get_study_background(
            self, study_id: str,
            background_id: str) -> Optional[BackgroundBase]:
        """Load and return an enrichment background."""
        self.load_cache({study_id})

        if study_id not in self._background_cache or \
                background_id not in self._background_cache[study_id]:
            return None

        return self._background_cache[study_id][background_id]

    def get_all_study_backgrounds(
        self, study_id: str
    ) -> Optional[dict[str, BackgroundBase]]:
        """Return all enrichment backgrounds for a given study."""
        self.load_cache({study_id})

        if study_id not in self._background_cache:
            return None

        return self._background_cache[study_id]

    def get_study_enrichment_config(self, study_id: str) -> Optional[Box]:
        """Get enrichment config for a study."""
        self.load_cache({study_id})

        if study_id not in self._enrichment_config_cache:
            return None

        return self._enrichment_config_cache[study_id]

    def get_all_study_ids(self) -> list[str]:
        self.load_cache()

        return list(self._background_cache.keys())

    def has_background(self, study_id: str, background_id: str) -> bool:
        self.load_cache({study_id})

        if study_id not in self._background_cache or \
                background_id not in self._background_cache[study_id]:
            return False
        return True
