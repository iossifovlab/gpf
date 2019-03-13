from __future__ import unicode_literals

import os

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig
from .study_wdae_config import StudyWdaeMixin


class StudyConfigBase(ConfigurableEntityConfig, StudyWdaeMixin):

    SPLIT_STR_SETS = (
        'phenotypes',
    )

    CAST_TO_BOOL = (
        'hasComplex', 'hasCNV', 'hasDenovo', 'hasTransmitted',
        'phenotypeBrowser', 'phenotypeGenotypeTool', 'enrichmentTool',
        'genotypeBrowser', 'genotypeBrowser.genesBlockShowAll',
        'genotypeBrowser.hasPresentInParent',
        'genotypeBrowser.hasComplex',
        'genotypeBrowser.hasPresentInChild',
        'genotypeBrowser.hasPedigreeSelector',
        'genotypeBrowser.hasCNV',
        'genotypeBrowser.hasFamilyFilters',
        'genotypeBrowser.hasStudyTypes',
        'genotypeBrowser.hasStudyFilters',
    )

    SPLIT_STR_LISTS = [
        'authorizedGroups',
        'genotypeBrowser.phenoFilters',
        'genotypeBrowser.baseColumns',
        'genotypeBrowser.basePreviewColumns',
        'genotypeBrowser.baseDownloadColumns',
        'genotypeBrowser.previewColumns',
        'genotypeBrowser.downloadColumns',
        'genotypeBrowser.pheno.columns',
        'genotypeBrowser.familyStudyFilters',
        'genotypeBrowser.phenoFilters.filters',
        'genotypeBrowser.genotype.columns',
        'genotypeBrowser.peopleGroup.columns',
    ]

    NEW_KEYS_NAMES = {
        'phenoGenoTool': 'phenotypeGenotypeTool',
        'genotypeBrowser.familyFilters': 'genotypeBrowser.familyStudyFilters',
    }

    def __init__(self, section_config, study_config, *args, **kwargs):
        super(StudyConfigBase, self).__init__(section_config, *args, **kwargs)

        assert self.id

        if section_config.get('name') is None:
            self.name = self.id

        assert self.name
        assert 'description' in self
        assert self.work_dir

        self.study_config = study_config


class StudyConfig(StudyConfigBase):

    def __init__(self, config, *args, **kwargs):
        super(StudyConfig, self).__init__(config, *args, **kwargs)

        assert self.name
        assert self.prefix
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

        config_section['authorizedGroups'] = config_section.get(
            'authorizedGroups', [config_section.get('id', '')])

        return StudyConfig(config_section, config)
