from dae.enrichment_tool.config import EnrichmentConfig
from dae.enrichment_tool.background import BackgroundBase


class BackgroundFacade(object):

    def __init__(self, variants_db):
        self._background_cache = {}
        self._enrichment_config_cache = {}

        self.variants_db = variants_db

    def get_study_background(self, study_id, background_id):
        self.load_cache({study_id})

        if study_id not in self._background_cache or \
                background_id not in self._background_cache[study_id]:
            return None

        return self._background_cache[study_id][background_id]

    def get_all_study_backgrounds(self, study_id):
        self.load_cache({study_id})

        if study_id not in self._background_cache:
            return None

        return self._background_cache[study_id]

    def get_study_enrichment_config(self, study_id):
        self.load_cache({study_id})

        if study_id not in self._enrichment_config_cache:
            return None

        return self._enrichment_config_cache[study_id]

    def get_all_study_ids(self):
        self.load_cache()

        return list(self._background_cache.keys())

    def has_background(self, study_id, background_id):
        self.load_cache({study_id})

        if study_id not in self._background_cache or \
                background_id not in self._background_cache[study_id]:
            return False
        return True

    def load_cache(self, study_ids=None):
        if study_ids is None:
            study_ids = set(self.variants_db.get_all_ids())

        assert isinstance(study_ids, set)

        cached_ids = set(self._enrichment_config_cache.keys()) & \
            set(self._background_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                self._load_enrichment_config_in_cache(study_id)
                for background_id in BackgroundBase.backgrounds().keys():
                    self._load_background_in_cache(study_id, background_id)

    def _load_enrichment_config_in_cache(self, study_id):
        enrichment_config = EnrichmentConfig.from_config(
            self.variants_db.get_config(study_id))
        if enrichment_config is None:
            return

        self._enrichment_config_cache[study_id] = enrichment_config

    def _load_background_in_cache(self, study_id, background_id):
        self._load_enrichment_config_in_cache(study_id)

        if study_id not in self._enrichment_config_cache or \
                background_id not in BackgroundBase.backgrounds():
            return

        if study_id not in self._background_cache or \
                self._background_cache[study_id] is None:
            self._background_cache[study_id] = {}

        enrichment_config = self._enrichment_config_cache[study_id]

        self._background_cache[study_id][background_id] = \
            BackgroundBase.backgrounds()[background_id](
                enrichment_config, self.variants_db)
