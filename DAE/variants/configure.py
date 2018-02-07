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
    def from_file(filename=None, wd=None):
        if wd is None:
            from default_settings import DATA_DIR
            wd = DATA_DIR

        if filename is None:
            from default_settings import CONFIG_FILE
            filename = CONFIG_FILE

        if not os.path.exists(filename):
            filename = os.path.abspath(os.path.join(wd, filename))

        print(filename)
        assert os.path.exists(filename)

        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': DATA_DIR,
            })
        print(conf)

        return Configure(conf)

    @staticmethod
    def from_dict(data):
        return Configure(data)
