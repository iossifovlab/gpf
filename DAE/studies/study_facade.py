from studies.study_wrapper import StudyWrapper
from studies.study_factory import StudyFactory
from studies.study_definition import SingleFileStudiesDefinition


class StudyFacade(object):

    def __init__(self, pheno_factory, study_definition=None, study_factory=None):
        self._study_cache = {}
        self._study_wrapper_cache = {}

        if study_definition is None:
            study_definition = SingleFileStudiesDefinition()
        if study_factory is None:
            study_factory = StudyFactory()

        self.study_definition = study_definition
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
        return [
            conf.id
            for conf in
            self.study_definition.get_all_study_configs()
        ]

    def get_all_study_configs(self):
        return self.study_definition.get_all_study_configs()

    def get_study_config(self, study_id):
        return self.study_definition.get_study_config(study_id)

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
        conf = self.study_definition.get_study_config(study_id)
        if not conf:
            return

        study = self.study_factory.make_study(conf)
        self._study_cache[study_id] = study
        self._study_wrapper_cache[study_id] = StudyWrapper(study, self.pheno_factory)
