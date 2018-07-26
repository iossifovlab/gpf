import os
import reusables
from box import ConfigBox


class StudyConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(StudyConfig, self).__init__(*args, **kwargs)
        assert self.prefix
        assert self.study_name

    @staticmethod
    def list_from_config(path='studies.conf', work_dir=None):
        if work_dir is None:
            pass
            # FIXME: is this necessary?
            # from default_settings import DATA_DIR
            # work_dir = DATA_DIR
        if not os.path.exists(path):
            path = os.path.join(work_dir, path)
        assert os.path.exists(path), path

        config = reusables.config_dict(
            path,
            auto_find=False,
            verify=True,
            defaults={
                'wd': work_dir,
            }
        )

        result = list()
        for section in config.keys():
            if 'study_name' not in config[section]:
                config[section]['study_name'] = section

            result.append(StudyConfig(config[section]))

        return result
