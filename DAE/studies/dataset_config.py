import functools
from studies.study_config import StudyConfigBase
import traceback


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
    return functools.reduce(
        lambda acc, st: acc or getattr(st, option_name),
        studies_configs,
        False)


def _same_value_attribute(studies_configs, option_name):
    res = getattr(studies_configs[0], option_name)
    for check_config in studies_configs[1:]:
        check = getattr(check_config, option_name)
        assert res == check, "{} == {}".format(res, check)
    return res


def _list_extend_attribute(studies_configs, option_name):
    return functools.reduce(
        lambda acc, st: acc + getattr(st, option_name),
        studies_configs,
        [])


def _strings_join_attribute(studies_configs, option_name):
    res = filter(
        lambda r: r != '',
        [getattr(st, option_name) for st in studies_configs])
    return ','.join(res)


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

        'people_group': _same_value_attribute,
        'peopleGroup': _same_value_attribute,
        'pedigree_selectors': _same_value_attribute,
        'pedigreeSelectors': _same_value_attribute,

        'genotypeBrowser': _same_value_attribute,
        'genotype_browser': _same_value_attribute,

        'enrichmentTool': _same_value_attribute,
        'enrichment_tool': _same_value_attribute,

        'authorizedGroups': _same_value_attribute,
        'authorized_groups': _same_value_attribute,

        'years': _list_extend_attribute,
        'pub_meds': _list_extend_attribute,
        'names': _list_extend_attribute,
        'ids': _list_extend_attribute,

        'study_types': _set_union_attribute,

        'year': _strings_join_attribute,
        'pub_med': _strings_join_attribute,
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
        cls._fill_wdae_config(config_section)
        return DatasetConfig(config_section)

    def __getattr__(self, option_name):
        try:
            return super(DatasetConfig, self).__getattr__(option_name)
        except AttributeError:
            return self._combine_studies_attributes(option_name)

    def __getitem__(self, option_name):
        try:
            return super(DatasetConfig, self).__getitem__(option_name)
        except Exception:
            return self._combine_studies_attributes(option_name)

    def _combine_studies_attributes(self, option_name):
        # assert len(self.studies) == len(self.studies_configs)
        # assert all([st.id in self.studies for st in self.studies_configs])
        # assert all([
        #     (option_name in st) or hasattr(st, option_name)
        #     for st in self.studies_configs
        # ]), option_name

        if option_name not in self.COMPOSITE_ATTRIBUTES:
            return None

        combiner = self.COMPOSITE_ATTRIBUTES[option_name]
        return combiner(self.studies_configs, option_name)
