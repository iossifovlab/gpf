from enrichment_tool.config import EnrichmentConfig
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.background import SynonymousBackground, \
    CodingLenBackground, SamochaBackground
from enrichment_tool.event_counters import EventsCounter, GeneEventsCounter


class EnrichmentFacade(object):
    BACKGROUNDS = {
        'synonymousBackgroundModel': SynonymousBackground,
        'codingLenBackgroundModel': CodingLenBackground,
        'samochaBackgroundModel': SamochaBackground
    }

    COUNTING = {
        'enrichmentEventsCounting': EventsCounter,
        'enrichmentGeneCounting': GeneEventsCounter
    }

    def __init__(self, variants_db):
        self._background_cache = {}
        self._counting_cache = {}
        self._enrichment_cache = {}

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

    def get_study_counter(self, study_id, counting_id):
        self.load_cache({study_id})

        if study_id not in self._counting_cache or \
                counting_id not in self._counting_cache[study_id]:
            return None

        return self._counting_cache[study_id][counting_id]

    def get_all_study_counters(self, study_id):
        self.load_cache({study_id})

        if study_id not in self._counting_cache:
            return None

        return self._counting_cache[study_id]

    def get_enrichment_tool(self, study_id, background_id, couting_id):
        self.load_cache({study_id})

        if study_id not in self._enrichment_cache or \
                background_id not in self._enrichment_cache[study_id] or \
                couting_id not in \
                self._enrichment_cache[study_id][background_id]:
            return None

        return self._enrichment_cache[study_id][background_id][couting_id]

    def get_study_enrichment_config(self, study_id, background_id):
        self.load_cache({study_id})

        if study_id not in self._enrichment_config_cache or \
                background_id not in self._enrichment_config_cache[study_id]:
            return None

        return self._enrichment_config_cache[study_id][background_id]

    def get_all_study_enrichment_configs(self, study_id):
        self.load_cache({study_id})

        if study_id not in self._enrichment_config_cache:
            return None

        return self._enrichment_config_cache[study_id]

    def get_all_study_ids(self, study_id):
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

                for background_id in self.BACKGROUNDS.keys():
                    self._load_background_in_cache(study_id, background_id)
                for counting_id in self.COUNTING.keys():
                    self._load_counting_in_cache(study_id, counting_id)
                for background_id in self.BACKGROUNDS.keys():
                    for counting_id in self.COUNTING.keys():
                        self._load_enrichment_in_cache(
                            study_id, background_id, counting_id)

    def _load_enrichment_config_in_cache(self, study_id):
        enrichment_config = EnrichmentConfig.from_config(
            self.variants_db.get_config(study_id))
        if enrichment_config is None:
            return

        self._enrichment_config_cache[study_id] = enrichment_config

    def _load_background_in_cache(self, study_id, background_id):
        self._load_enrichment_config_in_cache(study_id)

        if study_id not in self._enrichment_config_cache or \
                background_id not in self.BACKGROUNDS:
            return

        if study_id not in self._background_cache or \
                self._background_cache[study_id] is None:
            self._background_cache[study_id] = {}

        enrichment_config = self._enrichment_config_cache[study_id]

        self._background_cache[study_id][background_id] = \
            self.BACKGROUNDS[background_id](enrichment_config, use_cache=True)

    def _load_counting_in_cache(self, study_id, counting_id):
        self._load_enrichment_config_in_cache(study_id)

        if study_id not in self._enrichment_config_cache or \
                counting_id not in self.COUNTING:
            return

        if study_id not in self._counting_cache or \
                self._counting_cache[study_id] is None:
            self._counting_cache[study_id] = {}

        self._counting_cache[study_id][counting_id] = \
            self.COUNTING[counting_id]()

    def _load_enrichment_in_cache(self, study_id, background_id, counting_id):
        self._load_enrichment_config_in_cache(study_id)

        if study_id not in self._enrichment_config_cache:
            return

        background = self.get_study_background(study_id, background_id)
        counting = self.get_study_counter(study_id, counting_id)

        if background is None or counting is None:
            return

        if study_id not in self._enrichment_cache or \
                self._enrichment_cache[study_id] is None:
            self._enrichment_cache[study_id] = {}

        if background_id not in self._enrichment_cache[study_id] or \
                self._enrichment_cache[study_id][background_id] is None:
            self._enrichment_cache[study_id][background_id] = {}

        enrichment_config = self._enrichment_config_cache[study_id]

        self._enrichment_cache[study_id][background_id][counting_id] = \
            EnrichmentTool(enrichment_config, background, counting)
