'''
Created on Feb 7, 2018

@author: lubo
'''
from box import ConfigBox
import reusables
import os


class Configure(ConfigBox):

    def __init__(self, data, **kwargs):
        super(Configure, self).__init__(data, **kwargs)

    @staticmethod
    def from_file(work_dir=None, filename=None):
        if work_dir is None:
            from default_settings import DATA_DIR
            work_dir = DATA_DIR

        if filename is None:
            from default_settings import CONFIG_FILE
            filename = CONFIG_FILE

        if not os.path.exists(filename):
            filename = os.path.abspath(os.path.join(work_dir, filename))

        assert os.path.exists(filename)

        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': work_dir,
            })

        return Configure(conf['dataset'])

    @staticmethod
    def from_dict(data):
        return Configure(data)
