from __future__ import annotations

import enum
from pprint import pprint

from box import Box
from pydantic import BaseModel, ConfigDict


class RankRange(BaseModel):
    min_rank: int | None = None
    max_rank: int | None = None


class InferenceConfig(BaseModel):
    """Classification inference configuration class."""
    model_config = ConfigDict(extra="forbid")

    min_individuals: int = 1
    non_numeric_cutoff: float = 0.06
    value_max_len: int = 32
    continuous: RankRange = RankRange(min_rank=10)
    ordinal: RankRange = RankRange(min_rank=1)
    categorical: RankRange = RankRange(min_rank=1, max_rank=15)
    skip: bool = False
    measure_type: str | None = None


class ImportConfig(BaseModel):
    """Pheno import tool configuration."""
    model_config = ConfigDict(extra="forbid")

    report_only: bool = False
    instruments_tab_separated: bool = False
    person_column: str = "personId"
    db_filename: str = "pheno.db"
    default_inference: InferenceConfig = InferenceConfig()
    output: str = "output"
    verbose: int = 0
    instruments_dir: str = ""
    pedigree: str = ""


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
    def from_str(measure_type: str) -> MeasureType:
        if measure_type in MeasureType.__members__:
            return MeasureType[measure_type]

        raise ValueError("unexpected measure type", measure_type)

    @staticmethod
    def is_numeric(measure_type: MeasureType) -> bool:
        return measure_type in {MeasureType.continuous, MeasureType.ordinal}

    @staticmethod
    def is_text(measure_type: MeasureType) -> bool:
        return not MeasureType.is_numeric(measure_type)


def default_config() -> Box:
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
        "output": "output",
    }

    return Box(config)


def check_phenotype_data_config(config: InferenceConfig) -> bool:
    """Check phenotype database preparation config for consistency."""
    categorical = config.categorical.min_rank
    if categorical and categorical < 1:
        print("categorical min rank expected to be > 0")
        return False
    ordinal = config.ordinal.min_rank
    if ordinal and categorical and ordinal < categorical:
        print("ordinal min rank expected to be >= categorical min rank")
        return False
    continuous = config.continuous.min_rank
    if continuous and ordinal and continuous < ordinal:
        print("continuous min rank expected to be >= ordinal min rank")
        return False

    individuals = config.min_individuals
    if individuals < 1:
        print("minimal number of individuals expected to be >= 1")
        return False

    return True


def dump_config(config: InferenceConfig) -> None:
    """Print phenotype database preparation configuration."""
    print("--------------------------------------------------------")
    print("CLASSIFICATION BOUNDARIES:")
    print("--------------------------------------------------------")
    pprint(config.dict())  # noqa: T203
    print("--------------------------------------------------------")
