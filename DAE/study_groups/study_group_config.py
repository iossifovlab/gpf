from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class StudyGroupConfig(ConfigurableEntityConfig):

    def __init__(self, config, *args, **kwargs):
        super(StudyGroupConfig, self).__init__(config, *args, **kwargs)
        assert self.name
        assert self.enabled
        assert self.studies
        assert 'description' in self
        self.studies = self.list('studies')

    @classmethod
    def from_config(cls, config_section, section):
        study_group_config = config_section
        if 'name' not in study_group_config:
            study_group_config['name'] = section

        if 'enabled' not in study_group_config:
            study_group_config['enabled'] = True

        return StudyGroupConfig(study_group_config)

    @staticmethod
    def get_default_values():
        return {
            'description': '',
        }
