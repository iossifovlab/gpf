import functools
from studies.study_config import StudyConfigBase


def _set_union_attribute(studies_configs, option_name):
    return functools.reduce(
        lambda acc, st: acc | getattr(st, option_name),
        studies_configs,
        set())


def _boolean_and_attribute(studies_configs, option_name):
    return functools.reduce(
        lambda acc, st: acc and getattr(st, option_name),
        studies_configs,
        True)


def _boolean_or_attribute(studies_configs, option_name):
    print([st.id for st in studies_configs], option_name)
    print([getattr(st, option_name) for st in studies_configs])

    return functools.reduce(
        lambda acc, st: acc or getattr(st, option_name),
        studies_configs,
        False)


class DatasetConfig(StudyConfigBase):

    SPLIT_STR_LISTS = StudyConfigBase.SPLIT_STR_LISTS + [
        'studies',
    ]

    COMPOSITE_ATTRIBUTES = {
        'phenotypes': _set_union_attribute,

        'phenotypeGenotypeTool': _boolean_and_attribute,
        'phenotypeBrowser': _boolean_and_attribute,

        'phenotype_genotype_tool': _boolean_and_attribute,
        'phenotype_browser': _boolean_and_attribute,

        'hasTransmitted': _boolean_or_attribute,
        'hasDenovo': _boolean_or_attribute,

        'has_transmitted': _boolean_or_attribute,
        'has_denovo': _boolean_or_attribute,
    }

    def __init__(self, config, *args, **kwargs):
        super(DatasetConfig, self).__init__(config, *args, **kwargs)

        assert self.studies
        self.studies_configs = []

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

    def __getattr__(self, option_name):
        if option_name in self:
            return super(DatasetConfig, self).__getattr__(option_name)
        return self._combine_studies_attributes(option_name)

    def __getitem__(self, option_name):
        if option_name in self:
            return super(DatasetConfig, self).__getitem__(option_name)
        return self._combine_studies_attributes(option_name)

    def _combine_studies_attributes(self, option_name):
        assert len(self.studies) == len(self.studies_configs)
        assert all([st.id in self.studies for st in self.studies_configs])
        print(self.studies_configs)

        assert all([
            (option_name in st) or hasattr(st, option_name)
            for st in self.studies_configs
        ])
        if option_name not in self.COMPOSITE_ATTRIBUTES:
            return None

        combiner = self.COMPOSITE_ATTRIBUTES[option_name]
        return combiner(self.studies_configs, option_name)
