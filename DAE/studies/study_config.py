from __future__ import unicode_literals

import os

from studies.genotype_browser_config import GenotypeBrowserConfig
from studies.study_wdae_config import StudyWdaeMixin
from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class StudyConfigBase(ConfigurableEntityConfig, StudyWdaeMixin):

    SPLIT_STR_SETS = (
        'phenotypes',
    )

    CAST_TO_BOOL = (
        'hasComplex',
        'hasCNV',
        'hasDenovo',
        'hasTransmitted',
        'phenotypeBrowser',
        'phenotypeGenotypeTool',
        'enrichmentTool',
        'genotypeBrowser',
        'commonReport'
    )

    SPLIT_STR_LISTS = [
        'authorizedGroups'
    ]

    NEW_KEYS_NAMES = {
        'phenoGenoTool': 'phenotypeGenotypeTool'
    }

    def __init__(
            self, section_config, study_config, genotype_browser_config=None,
            *args, **kwargs):
        super(StudyConfigBase, self).__init__(section_config, *args, **kwargs)

        assert self.id

        if section_config.get('name') is None:
            self.name = self.id

        assert self.name
        assert 'description' in self
        assert self.work_dir

        self.study_config = study_config

        if genotype_browser_config is not None:
            self.genotypeBrowserConfig = genotype_browser_config


class StudyConfig(StudyConfigBase):

    def __init__(self, config, *args, **kwargs):
        super(StudyConfig, self).__init__(config, *args, **kwargs)

        assert self.name
        assert self.prefix
        # assert self.pedigree_file
        assert self.file_format
        assert self.work_dir
        # assert self.phenotypes
        assert 'studyType' in self
        assert 'hasComplex' in self
        assert 'hasCNV' in self
        assert 'hasDenovo' in self
        assert 'hasTransmitted' in self
        self.make_prefix_absolute_path()

    def make_prefix_absolute_path(self):

        if not os.path.isabs(self.prefix):
            config_filename = self.config.study_config.config_file
            dirname = os.path.dirname(config_filename)
            self.prefix = os.path.abspath(
                os.path.join(dirname, self.prefix))

    @property
    def years(self):
        return [self.year] if self.year else []

    @property
    def pub_meds(self):
        return [self.pub_med] if self.pub_med else []

    @property
    def study_types(self):
        return {self.study_type} if self.study_type else set()

    @property
    def ids(self):
        return [self.id]

    @property
    def names(self):
        return [self.name]

    @classmethod
    def from_config(cls, config):
        config_section = config['study']
        config_section = cls.parse(config_section)

        if 'enabled' in config_section:
            if config_section['enabled'] == 'false':
                return None

        cls._fill_wdae_config(config_section)
        genotype_browser_config = None
        if config.get('genotypeBrowser', None) is not None and \
                config_section.get('genotypeBrowser', False) is True:
            genotype_browser_config = GenotypeBrowserConfig.from_config(config)

        config_section['authorizedGroups'] = config_section.get(
            'authorizedGroups', [config_section.get('id', '')])

        # config_section['studies'] = [config_section['id']]

        return StudyConfig(
            config_section, config,
            genotype_browser_config=genotype_browser_config
        )
