import functools
from box import BoxList

from studies.study_config_parser import StudyConfigParserBase


def _set_union_attribute(studies_configs, option_name):
    return functools.reduce(
        lambda acc, st: acc | frozenset(getattr(st, option_name)),
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
        assert res.to_json() == check.to_json(), "{} == {}".format(res, check)
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


class DatasetConfigParser(StudyConfigParserBase):

    SECTION = 'dataset'

    SPLIT_STR_LISTS = StudyConfigParserBase.SPLIT_STR_LISTS + [
        'studies',
    ]

    COMPOSITE_ATTRIBUTES = {
        # 'phenotypes': _set_union_attribute,

        'genotypeBrowser': _boolean_and_attribute,
        'genotype_browser': _boolean_and_attribute,

        'phenotypeTool': _boolean_and_attribute,
        'phenotypeBrowser': _boolean_and_attribute,

        'phenotype_tool': _boolean_and_attribute,
        'phenotype_browser': _boolean_and_attribute,

        'hasTransmitted': _boolean_or_attribute,
        'hasDenovo': _boolean_or_attribute,

        'has_transmitted': _boolean_or_attribute,
        'has_denovo': _boolean_or_attribute,

        'genotypeBrowserConfig': _same_value_attribute,
        'genotype_browser_config': _same_value_attribute,

        'peopleGroupConfig': _same_value_attribute,
        'people_group_config': _same_value_attribute,

        'enrichmentTool': _boolean_and_attribute,
        'enrichment_tool': _boolean_and_attribute,

        'authorizedGroups': _set_union_attribute,
        'authorized_groups': _set_union_attribute,

        'years': _list_extend_attribute,
        'pub_meds': _list_extend_attribute,
        'names': _list_extend_attribute,
        'ids': _list_extend_attribute,

        'study_types': _set_union_attribute,

        'year': _strings_join_attribute,
        'pub_med': _strings_join_attribute,
    }

    @classmethod
    def parse(cls, config, study_configs):
        config = super(DatasetConfigParser, cls).parse(config)
        if config is None:
            return None

        config = cls._combine_studies_attributes(config, study_configs)

        config.authorizedGroups = BoxList(config.get(
            'authorizedGroups', [config.get('id', '')]))

        assert config.studies

        return config

    @classmethod
    def _combine_studies_attributes(cls, config, study_configs):
        assert len(config.studies) == len(study_configs)
        assert all([st.id in config.studies for st in study_configs])

        study_config_keys = [
            set(study_config.keys()) for study_config in study_configs
        ]
        option_names = set.intersection(*study_config_keys)

        for option_name in option_names:
            if option_name in config:
                continue

            if option_name not in cls.COMPOSITE_ATTRIBUTES:
                continue

            combiner = cls.COMPOSITE_ATTRIBUTES[option_name]
            config[option_name] = combiner(study_configs, option_name)

        return config
