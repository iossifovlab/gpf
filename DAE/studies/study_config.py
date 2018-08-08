import os
import reusables
from box import ConfigBox

from studies.study_factory import StudyFactory


class StudyConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(StudyConfig, self).__init__(*args, **kwargs)
        assert self.prefix
        assert self.study_name
        assert self.type
        assert self.type in StudyFactory.STUDY_TYPES.keys()
        assert self.work_dir
        self.make_vcf_prefix_absolute_path()

    @classmethod
    def list_from_config(cls, config_file='studies.conf', work_dir=None):
        if work_dir is None:
            pass
            # FIXME: is this necessary?
            # from default_settings import DATA_DIR
            # work_dir = DATA_DIR
        if not os.path.exists(config_file):
            config_file = os.path.join(work_dir, config_file)
        assert os.path.exists(config_file), config_file

        config = reusables.config_dict(
            config_file,
            auto_find=False,
            verify=True,
            defaults={
                'work_dir': work_dir,
            }
        )

        result = list()
        for section in config.keys():
            cls.add_default_study_name_from_section(config, section)

            result.append(StudyConfig(config[section]))

        return result

    @classmethod
    def add_default_study_name_from_section(cls, config, section):
        if 'study_name' not in config[section]:
            config[section]['study_name'] = section

    def make_vcf_prefix_absolute_path(self):
        if not os.path.isabs(self.prefix):
            self.prefix = os.path.abspath(
                os.path.join(self.work_dir, self.study_name, self.prefix))

