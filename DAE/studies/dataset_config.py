from studies.study_config import StudyConfigBase


class DatasetConfig(StudyConfigBase):

    ELEMENTS_TO_COPY = {
        # 'dataset_id': 'id', 'dataset_name': 'name'
    }

    SPLIT_STR_LISTS = StudyConfigBase.SPLIT_STR_LISTS + [
        'studies',
    ]

    def __init__(self, config, *args, **kwargs):
        super(DatasetConfig, self).__init__(config, *args, **kwargs)

        assert self.studies

    @classmethod
    def from_config(cls, config_section):
        if 'enabled' in config_section:
            if config_section['enabled'] == 'false':
                return None

        config_section['pedigreeSelectors'] =\
            cls._get_pedigree_selectors(config_section, 'peopleGroup')
        config_section['genotypeBrowser.pedigreeColumns'] =\
            cls._get_pedigree_selector_columns(
                config_section, 'genotypeBrowser', 'peopleGroup')
        config_section['genotypeBrowser.phenoFilters'] =\
            cls._get_genotype_browser_pheno_filters(config_section)
        config_section['genotypeBrowser.phenoColumns'] =\
            cls._get_genotype_browser_pheno_columns(config_section)
        config_section['genotypeBrowser.genotypeColumns'] =\
            cls._get_genotype_browser_genotype_columns(config_section) + \
            config_section['genotypeBrowser.pedigreeColumns'] + \
            config_section['genotypeBrowser.phenoColumns']
        config_section = cls._combine_dict_options(config_section)

        config_section['authorizedGroups'] = config_section.get(
            'authorizedGroups', [config_section['id']])

        return DatasetConfig(config_section)
