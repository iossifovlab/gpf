import enum
from box import Box  # type: ignore
from pprint import pprint
from collections import OrderedDict
from copy import deepcopy
from dae.variants.attributes import Role


class MeasureType(enum.Enum):
    continuous = 1
    ordinal = 2
    categorical = 3
    text = 4
    raw = 5
    other = 100
    skipped = 1000

    @staticmethod
    def from_str(measure_type):
        if measure_type in MeasureType.__members__:
            return MeasureType[measure_type]
        else:
            raise ValueError("unexpected measure type", measure_type)

    @staticmethod
    def is_numeric(measure_type):
        return (
            measure_type == MeasureType.continuous
            or measure_type == MeasureType.ordinal
        )

    @staticmethod
    def is_text(measure_type):
        return not MeasureType.is_numeric(measure_type)


class RoleMapping(object):
    SPARK = {
        "Mother": Role.mom,
        "Father": Role.dad,
        "Proband": Role.prb,
        "Sibling": Role.sib,
        "Maternal_Uncle": Role.maternal_uncle,
        "Paternal_Grandfather": Role.paternal_grandfather,
        "Paternal_Grandmother": Role.paternal_grandmother,
        "Maternal_Aunt": Role.maternal_aunt,
        "Maternal_Grandfather": Role.maternal_grandfather,
        "Maternal_Grandmother": Role.maternal_grandmother,
        "Paternal_Half_Sibling": Role.paternal_half_sibling,
        "Maternal_Half_Sibling": Role.maternal_half_sibling,
    }

    SSC = {
        "mom": Role.mom,
        "dad": Role.dad,
        "prb": Role.prb,
        "sib": Role.sib,
    }

    INTERNAL = {key: value for key, value in list(Role.__members__.items())}

    VIP = {
        "Mother": Role.mom,
        "Father": Role.dad,
        "Initially identified proband": Role.prb,
        "Sibling": Role.sib,
        "Uncle": Role.maternal_uncle,
        "Cousin": Role.maternal_cousin,
        "Grandfather": Role.maternal_grandfather,
        "Grandmother": Role.maternal_grandmother,
        "Half sibling": Role.maternal_half_sibling,
        "Aunt": Role.maternal_aunt,
    }


ROLES_GRAPHS_DEFINITION = OrderedDict(
    [
        ("probands", [Role.prb]),
        ("siblings", [Role.sib]),
        ("parents", [Role.mom, Role.dad]),
        (
            "grandparents",
            [
                Role.paternal_grandfather,
                Role.paternal_grandmother,
                Role.maternal_grandfather,
                Role.maternal_grandmother,
            ],
        ),
        (
            "parental siblings",
            [
                Role.paternal_uncle,
                Role.paternal_aunt,
                Role.maternal_uncle,
                Role.maternal_aunt,
            ],
        ),
        ("step parents", [Role.step_mom, Role.step_dad]),
        (
            "half siblings",
            [Role.paternal_half_sibling, Role.maternal_half_sibling],
        ),
        ("children", [Role.child]),
    ]
)


ROLES_FILTER_DEFINITION = deepcopy(ROLES_GRAPHS_DEFINITION)
ROLES_FILTER_DEFAULT_ROLES = ["probands", "siblings", "parents"]


def default_config():
    config = {
        "report_only": False,
        "parallel": 4,
        "family": {"composite_key": False},
        "instruments": {"tab_separated": False, "dir": "."},
        "person": {
            "role": {
                "type": "column",
                "column": "role",
                "mapping": "INTERNAL",
            },
            "column": None,
        },
        "db": {"filename": "pheno.db"},
        "skip": {"measures": []},
        "classification": {
            "min_individuals": 1,
            "non_numeric_cutoff": 0.06,
            "value_max_len": 32,
            "continuous": {"min_rank": 10},
            "ordinal": {"min_rank": 1},
            "categorical": {"min_rank": 1, "max_rank": 15},
        },
    }

    return Box(config)


def check_phenotype_data_config(config):
    categorical = config.classification.categorical.min_rank
    if categorical < 1:
        print("categorical min rank expected to be > 0")
        return False
    ordinal = config.classification.ordinal.min_rank
    if ordinal < categorical:
        print("ordinal min rank expected to be >= categorical min rank")
        return False
    continuous = config.classification.continuous.min_rank
    if continuous < ordinal:
        print("continuous min rank expected to be >= ordinal min rank")
        return False

    individuals = config.classification.min_individuals
    if individuals < 1:
        print("minimal number of individuals expected to be >= 1")
        return False

    return True


def dump_config(config):
    print("--------------------------------------------------------")
    print("CLASSIFICATION BOUNDARIES:")
    print("--------------------------------------------------------")
    pprint(config.to_dict())
    print("--------------------------------------------------------")
