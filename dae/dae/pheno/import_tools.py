from pydantic import BaseModel, DirectoryPath, FilePath

from dae.pheno.common import InferenceConfig


class _DataDictionary(BaseModel):
    file: str
    instrument_files: list[FilePath]

    # {Instrument -> {Measure -> Description}}
    dictionary: dict[str, dict[str, str]]


class RegressionMeasure(BaseModel):
    instrument_name: str
    measure_name: str
    jitter: float
    display_name: str


class PhenoImportConfig(BaseModel):
    """Pheno import config."""
    id: str
    input_dir: DirectoryPath
    output_dir: DirectoryPath
    pedigree: FilePath
    skip_pedigree_measures: bool
    instrument_files: list[FilePath | DirectoryPath]
    person_column: str
    inference_config: FilePath | dict[str, InferenceConfig]
    data_dictionary: _DataDictionary
    regression_config: FilePath | dict[str, RegressionMeasure]
