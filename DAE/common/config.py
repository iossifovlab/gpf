from collections import OrderedDict


def _section_tree(section, config):
    section_tree = OrderedDict()
    for option in config.options(section):
        option_leaf = section_tree
        option_tokens = option.split('.')
        for token in option_tokens[0:-1]:
            option_leaf = option_leaf.setdefault(token, OrderedDict())
        option_leaf[option_tokens[-1]] = config.get(section, option)
    return section_tree


def to_dict(config):
    result = OrderedDict()
    for section in config.sections():
        result[section] = _section_tree(section, config)
    return result


def flatten_dict(input_dict, sep='.'):
    res = {}
    for key, value in input_dict.items():
        if type(value) is dict and len(value):
            for key_2, value_2 in flatten_dict(value).items():
                res[key + sep + key_2] = value_2
        else:
            res[key] = value
    return res
