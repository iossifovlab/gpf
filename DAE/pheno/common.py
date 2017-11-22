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
    unknown = 0
    mom = 10
    dad = 20
    step_mom = 23
    step_dad = 13
    parent = 1
    prb = 30
    sib = 40
    child = 50
    spouse = 2
    maternal_cousin = 14
    paternal_cousin = 24
    maternal_uncle = 11
    maternal_aunt = 12
    paternal_uncle = 21
    paternal_aunt = 22
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
    text = 4
    other = 100
    skipped = 1000

    @staticmethod
    def from_str(measure_type):
        if measure_type == MeasureType.continuous.name:
            return MeasureType.continuous
        elif measure_type == MeasureType.ordinal.name:
            return MeasureType.ordinal
        elif measure_type == MeasureType.categorical.name:
            return MeasureType.categorical
        elif measure_type == MeasureType.other.name:
            return MeasureType.other
        elif measure_type == measure_type.text.name:
            return MeasureType.text
        elif measure_type == MeasureType.skipped.name:
            return MeasureType.skipped
        else:
            assert ValueError("unexpected measure type"), measure_type

    @staticmethod
    def is_numeric(measure_type):
        return measure_type == MeasureType.continuous or \
            measure_type == MeasureType.ordinal

    @staticmethod
    def is_text(measure_type):
        return not MeasureType.is_numeric(measure_type)


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

    SSC = {
        'mom': Role.mom,
        'dad': Role.dad,
        'prb': Role.prb,
        'sib': Role.sib,
    }

    INTERNAL = {
        key: value for key, value in Role.__members__.items()
    }

    VIP = {
        'Mother': Role.mom,
        'Father': Role.dad,
        'Initially identified proband': Role.prb,
        'Sibling': Role.sib,
        'Uncle': Role.maternal_uncle,
        'Cousin': Role.maternal_cousin,
        'Grandfather': Role.maternal_grandfather,
        'Grandmother': Role.maternal_grandmother,
        'Half sibling': Role.maternal_half_sibling,
        'Aunt': Role.maternal_aunt,
    }


def default_config():
    config = {
        'report_only': False,
        'family': {
            'composite_key': False,
        },
        'instruments': {
            'tab_separated': False,
            'dir': '.',
        },
        'person': {
            'role': {
                'type': 'column',
                'column': 'role',
                'mapping': 'INTERNAL'
            },
            'column': None,
        },
        'db': {
            'filename': 'pheno.db'
        },
        'skip': {
            'measures': [
            ]
        },
        'classification': {
            'min_individuals': 10,
            'non_numeric_cutoff': 0.06,
            'value_max_len': 32,
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
