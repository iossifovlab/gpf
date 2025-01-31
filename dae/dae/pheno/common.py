from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict


class RankRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    value_type: str | None = None
    histogram_type: str | None = None


class DataDictionaryConfig(BaseModel):
    """Pydantic model for data dictionary config entries."""
    model_config = ConfigDict(extra="forbid")

    path: str
    instrument: str | None = None
    delimiter: str = "\t"
    instrument_column: str = "instrumentName"
    measure_column: str = "measureName"
    description_column: str = "description"


class MeasureDescriptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[DataDictionaryConfig] | None = None

    # {Instrument -> {Measure -> Description}}
    dictionary: dict[str, dict[str, str]] | None = None


class RegressionMeasure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_name: str
    measure_names: list[str]
    jitter: float
    display_name: str


class StudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regressions: str | dict[str, RegressionMeasure] | None = None


class GPFInstanceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str


class DestinationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_id: str


class InstrumentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    instrument: str | None = None
    delimiter: str | None = None
    person_column: str | None = None


class PhenoImportConfig(BaseModel):
    """Pheno import config."""
    model_config = ConfigDict(extra="forbid")

    id: str
    input_dir: str
    work_dir: str
    instrument_files: list[str | InstrumentConfig]
    pedigree: str
    person_column: str
    delimiter: str = ","
    destination: DestinationConfig | None = None
    gpf_instance: GPFInstanceConfig | None = None
    skip_pedigree_measures: bool = False
    inference_config: str | dict[str, InferenceConfig] | None = None
    data_dictionary: MeasureDescriptionsConfig | None = None
    study_config: StudyConfig | None = None


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
