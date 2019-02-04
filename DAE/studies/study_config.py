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
        'genotypeBrowser.hasDenovo',
        'genotypeBrowser.hasPedigreeSelector', 
        'genotypeBrowser.hasCNV',
        'genotypeBrowser.hasFamilyFilters',
        'genotypeBrowser.hasStudyTypes',
        'genotypeBrowser.hasStudyFilters',
        'genotypeBrowser.hasTransmitted',
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

    def __init__(self, config, *args, **kwargs):
        super(StudyConfigBase, self).__init__(config, *args, **kwargs)

        assert self.id
        assert self.name
        assert 'description' in self
        assert self.work_dir

    @classmethod
    def get_default_values(cls):
        return {
            'description': None,
            'order': 0,

            'genotypeBrowser.genotype.columns':
                'family,phenotype,variant,best,fromparent,inchild,genotype,'
                'effect,count,geneeffect,effectdetails,weights,freq',
            'genotypeBrowser.previewColumns':
                'family,variant,genotype,effect,weights,freq,studyName,'
                'location,pedigree,inChS,fromParentS,effects,'
                'requestedGeneEffects,genes,worstEffect',
            'genotypeBrowser.downloadColumns':
                'family,phenotype,variant,best,fromparent,inchild,effect,'
                'count,geneeffect,effectdetails,weights,freq',
        }


class StudyConfig(StudyConfigBase):

    def __init__(self, config, *args, **kwargs):
        super(StudyConfig, self).__init__(config, *args, **kwargs)

        assert 'prefix' in self
        assert self.name

        assert self.file_format
        assert self.work_dir
        assert self.phenotypes
        assert 'studyType' in self
        assert 'hasComplex' in self
        assert 'hasCNV' in self
        assert 'hasDenovo' in self
        assert 'hasTransmitted' in self
        self.make_prefix_absolute_path()

    def make_prefix_absolute_path(self):
        if not os.path.isabs(self.prefix):
            self.prefix = os.path.abspath(
                os.path.join(self.work_dir, self.id, self.prefix))

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
    def from_config(cls, config_section):
        if 'enabled' in config_section:
            if config_section['enabled'] == 'false':
                return None

        cls._fill_wdae_config(config_section)

        config_section['authorizedGroups'] = config_section.get(
            'authorizedGroups', [config_section['id']])

        return StudyConfig(config_section)

    @classmethod
    def get_default_values(cls):
        defaults = super(StudyConfig, cls).get_default_values()
        defaults.update({
            'studyType': 'WE',
            'year': '',
            'pubMed': '',
            'hasDenovo': 'yes',
            'hasTransmitted': 'no',
            'hasComplex': 'no',
            'hasCNV': 'no',
            'studyType': 'WE',
            'phenotypes': None,
            'phenoDB': None,
            'genotypeBrowser.genesBlockShowAll': 'yes',
            'genotypeBrowser.hasFamilyFilters': 'yes',
            'genotypeBrowser.hasStudyFilters': 'yes',
            'genotypeBrowser.phenoFilters': '',
            'genotypeBrowser.hasPresentInChild': 'yes',
            'genotypeBrowser.hasPresentInParent': 'yes',
            'genotypeBrowser.hasPedigreeSelector': 'no',
            'genotypeBrowser.mainForm': 'default',
            'genotypeBrowser.pheno.columns': None,
            'genotypeBrowser.familyFilters': None,
            'phenoFilters': '',
            'phenotypeBrowser': False,
            'phenotypeGenotypeTool': False,
        })
        return defaults
