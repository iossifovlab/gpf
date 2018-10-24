from __future__ import unicode_literals
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
