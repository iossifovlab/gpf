import os
import reusables
from box import ConfigBox


class StudyGroupConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(StudyGroupConfig, self).__init__(*args, **kwargs)
        assert 'phenotype' in self
        assert self.enabled
        assert self.studies

    @classmethod
    def dict_from_config(cls, path='study_groups.conf'):
        assert os.path.exists(path), path

        config = reusables.config_dict(
            path,
            auto_find=False,
            verify=True
        )

        result = {}
        for section in config.keys():
            study_group_config = config[section]
            if 'phenotype' not in study_group_config:
                study_group_config['phenotype'] = None
            if 'enabled' not in study_group_config:
                study_group_config['enabled'] = True

            study_group_config['studies'] = study_group_config['studies'] \
                .split(',')

            result[section] = StudyGroupConfig(study_group_config)

        return result
