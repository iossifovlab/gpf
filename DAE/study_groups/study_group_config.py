from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class StudyGroupConfig(ConfigurableEntityConfig):

    def __init__(self, *args, **kwargs):
        super(StudyGroupConfig, self).__init__(*args, **kwargs)
        assert 'phenotype' in self
        assert self.enabled
        assert self.studies

    @classmethod
    def from_config(cls, config_section, section):
        study_group_config = config_section
        study_group_config['studies'] = study_group_config['studies'].split(',')
        if 'name' not in study_group_config:
            study_group_config['name'] = section

        if 'phenotype' not in study_group_config:
            study_group_config['phenotype'] = None

        if 'enabled' not in study_group_config:
            study_group_config['enabled'] = True

        return StudyGroupConfig(study_group_config)
