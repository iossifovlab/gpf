'''
Created on Aug 23, 2016

@author: lubo
'''
import os

from dae.configuration.dae_config_parser import ConfigParserBase


class PhenoConfigParser(ConfigParserBase):

    @staticmethod
    def _assert_pheno_paths(configs):
        for _, config in configs.items():
            if config.dbfile is not None:
                assert os.path.isfile(config.dbfile), config.dbfile
            if config.browser_dbfile is not None:
                assert os.path.isfile(config.browser_dbfile), \
                    config.browser_dbfile
            if config.browser_images_dir is not None:
                assert os.path.isdir(config.browser_images_dir), \
                    config.browser_images_dir

    @classmethod
    def read_directory_configurations(
            cls, configurations_dir, work_dir=None, defaults=None,
            fail_silently=False):
        config_files = [
            (conf_path, os.path.dirname(conf_path))
            for conf_path in cls._collect_config_paths(configurations_dir)
        ]

        configs = [
            cls.read_file_configuration(config_file, work_dir)
            for config_file, work_dir in config_files
        ]
        configs = {
            config.name: config for config in configs if config
        }

        cls._assert_pheno_paths(configs)

        return configs

    @classmethod
    def read_file_configuration(cls, config_file, work_dir, defaults=None):
        config = super(PhenoConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults=None)
        if not config or not config.pheno_db:
            return None

        config = config.pheno_db

        cls._assert_pheno_paths({config.name: config})

        return config
