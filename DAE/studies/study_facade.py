from studies.study_wrapper import StudyWrapper
from studies.study_factory import StudyFactory
from studies.study_config_parser import StudyConfigParser


class StudyFacade(object):

    def __init__(
            self, dae_config, pheno_factory,
            study_configs=None, study_factory=None):

        self.dae_config = dae_config
        self._study_cache = {}
        self._study_wrapper_cache = {}

        if study_factory is None:
            study_factory = StudyFactory(dae_config)

        self.study_configs = {
            sc[StudyConfigParser.SECTION].id: sc for sc in study_configs
        }
        self.study_factory = study_factory
        self.pheno_factory = pheno_factory

    def get_study(self, study_id):
        self.load_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache[study_id]

    def get_study_wdae_wrapper(self, study_id):
        self.load_cache({study_id})

        if study_id not in self._study_wrapper_cache:
            return None

        return self._study_wrapper_cache[study_id]

    def get_all_studies(self):
        self.load_cache()

        return list(self._study_cache.values())

    def get_all_studies_wrapper(self):
        self.load_cache()

        return list(self._study_wrapper_cache.values())

    def get_all_study_ids(self):
        return list(self.study_configs.keys())

    def get_all_study_configs(self):
        self.load_cache()

        return [study.config for study in self._study_cache.values()]

    def get_study_config(self, study_id):
        self.load_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache.get(study_id).config

    def load_cache(self, study_ids=None):
        if study_ids is None:
            study_ids = set(self.get_all_study_ids())

        assert isinstance(study_ids, set)

        cached_ids = set(self._study_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                self._load_study_in_cache(study_id)

    def _load_study_in_cache(self, study_id):
        conf = self.study_configs.get(study_id)
        if not conf:
            return

        study = self.study_factory.make_study(conf)
        if study is None:
            return
        self._study_cache[study_id] = study
        self._study_wrapper_cache[study_id] = \
            StudyWrapper(study, self.pheno_factory)
