import enum
from pprint import pprint

from box import Box


class MeasureType(enum.Enum):
    """Definition of measure types."""

    # pylint: disable=invalid-name
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


def default_config():
    """Construct phenotype database preparation configuration."""
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
    """Check phenotype database preparation config for consistency."""
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
    """Print phenotype database preparation configuration."""
    print("--------------------------------------------------------")
    print("CLASSIFICATION BOUNDARIES:")
    print("--------------------------------------------------------")
    pprint(config.to_dict())
    print("--------------------------------------------------------")
