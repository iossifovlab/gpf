'''
Created on May 24, 2017

@author: lubo
'''
import enum
from box import Box
from pprint import pprint


class Gender(enum.Enum):
    M = 1
    F = 2


class Status(enum.Enum):
    affected = 2
    unaffected = 1


class Role(enum.Enum):
    mom = 10
    dad = 22
    prb = 30
    sib = 40
    maternal_uncle = 11
    maternal_aunt = 12
    maternal_half_sibling = 41
    paternal_half_sibling = 42
    maternal_grandmother = -11
    maternal_grandfather = -12
    paternal_grandmother = -21
    paternal_grandfather = -22


class MeasureType(enum.Enum):
    continuous = 1
    ordinal = 2
    categorical = 3
    other = 4


class RoleMapping(object):
    SPARK = {
        'Mother': Role.mom,
        'Father': Role.dad,
        'Proband': Role.prb,
        'Sibling': Role.sib,
        'Maternal_Uncle': Role.maternal_uncle,
        'Paternal_Grandfather': Role.paternal_grandfather,
        'Paternal_Grandmother': Role.paternal_grandmother,
        'Maternal_Aunt': Role.maternal_aunt,
        'Maternal_Grandfather': Role.maternal_grandfather,
        'Maternal_Grandmother': Role.maternal_grandmother,
        'Paternal_Half_Sibling': Role.paternal_half_sibling,
        'Maternal_Half_Sibling': Role.maternal_half_sibling,
    }


def default_config():
    config = {
        'family': {
            'composite_key': False,
        },
        'person': {
            'role': {
                'type': 'column',
                'column': 'role',
                'mapping': 'SPARK'
            },
        },
        'db': {
            'filename': 'pheno.db'
        },
        'skip': {
            'measures': [
            ]
        },
        'classification': {
            'min_individuals': 20,
            'continuous': {
                'min_rank': 15
            },
            'ordinal': {
                'min_rank': 5
            },
            'categorical': {
                'min_rank': 2
            }
        },
    }

    return Box(config)


def check_config_pheno_db(config):
    categorical = config.classification.categorical.min_rank
    if categorical < 1:
        print('categorical min rank expected to be > 0')
        return False
    ordinal = config.classification.ordinal.min_rank
    if ordinal < categorical:
        print('ordianl min rank expected to be >= categorical min rank')
        return False
    continuous = config.classification.continuous.min_rank
    if continuous < ordinal:
        print('continuous min rank expected to be >= ordinal min rank')
        return False

    individuals = config.classification.min_individuals
    if individuals < 1:
        print('minimal number of individuals expected to be >= 1')
        return False

    return True


def dump_config(config):
    print("--------------------------------------------------------")
    print("CLASSIFICATION BOUNDARIES:")
    print("--------------------------------------------------------")
    pprint(config.to_dict())
    print("--------------------------------------------------------")
