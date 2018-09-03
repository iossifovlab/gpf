from study_groups.study_group_factory import StudyGroupFactory
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition


class StudyGroupFacade(object):

    _study_group_cache = {}

    def __init__(self, study_group_definition=None, study_group_factory=None):
        if study_group_definition is None:
            study_group_definition = SingleFileStudiesGroupDefinition()
        if study_group_factory is None:
            study_group_factory = StudyGroupFactory()

        self.study_group_definition = study_group_definition
        self.study_group_factory = study_group_factory

    def get_study_group(self, study_group_id):
        self.load_cache({study_group_id})

        return self._study_group_cache[study_group_id]

    def get_all_study_groups(self):
        self.load_cache()

        return list(self._study_group_cache.values())

    def get_all_study_group_ids(self):
        return [
            conf.name
            for conf in
            self.study_group_definition.get_all_study_group_configs()
        ]

    def get_all_study_group_configs(self):
        return self.study_group_definition.get_all_study_group_configs()

    def load_cache(self, study_group_ids=None):
        if study_group_ids is None:
            study_group_ids = set(self.get_all_study_group_ids())

        assert isinstance(study_group_ids, set)

        cached_ids = set(self._study_group_cache.keys())
        if study_group_ids != cached_ids:
            to_load = study_group_ids - cached_ids
            for study_group_id in to_load:
                self._load_study_group_in_cache(study_group_id)

    def _load_study_group_in_cache(self, study_group_id):
        conf = self.study_group_definition.get_study_group_config(study_group_id)
        if not conf:
            return

        self._study_group_cache[study_group_id] = \
            self.study_group_factory.get_study_group(conf)

