from __future__ import annotations

import enum
import time
from typing import Any

import duckdb
import sqlglot
from pydantic import BaseModel, ConfigDict
from sqlglot import insert, select
from sqlglot.expressions import Table, table_

from dae.utils.sql_utils import to_duckdb_transpile

IMPORT_METADATA_TABLE = table_("import_metadata")


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


class MeasureHistogramConfigs(BaseModel):
    """Classification histogram configuration class."""
    model_config = ConfigDict(extra="forbid")

    number_config: dict = {}
    categorical_config: dict = {}


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


class InstrumentDictionaryConfig(BaseModel):
    """Pydantic model for instrument dictionary config entries."""
    model_config = ConfigDict(extra="forbid")

    path: str
    instrument: str | None = None
    delimiter: str = "\t"
    instrument_column: str = "instrumentName"
    description_column: str = "description"


class InstrumentDescriptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[InstrumentDictionaryConfig] | None = None

    dictionary: dict[str, str] | None = None


class RegressionMeasure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_name: str
    measure_names: list[str]
    jitter: float
    display_name: str


class StudyConfig(BaseModel):
    regressions: str | dict[str, RegressionMeasure] | None = None
    common_report: dict[str, Any] | None = None
    person_set_collections: dict[str, Any] | None = None


class GPFInstanceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str


class DestinationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_id: str | None = None
    storage_dir: str | None = None


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
    histogram_configs: MeasureHistogramConfigs | None = None
    data_dictionary: MeasureDescriptionsConfig | None = None
    instrument_dictionary: InstrumentDescriptionsConfig | None = None

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


class ImportManifest(BaseModel):
    """Import manifest for checking cache validity."""

    unix_timestamp: float
    import_config: PhenoImportConfig

    def is_older_than(self, other: ImportManifest) -> bool:
        if self.unix_timestamp < other.unix_timestamp:
            return True
        return self.import_config != other.import_config

    @staticmethod
    def from_row(row: tuple[str, Any, str]) -> ImportManifest:
        timestamp = float(row[0])
        import_config = PhenoImportConfig.model_validate_json(row[1])
        return ImportManifest(
            unix_timestamp=timestamp,
            import_config=import_config,
        )

    @staticmethod
    def from_table(
        connection: duckdb.DuckDBPyConnection, table: Table,
    ) -> list[ImportManifest]:
        """Read manifests from given table."""
        with connection.cursor() as cursor:
            table_row = cursor.execute(sqlglot.parse_one(
                "SELECT * FROM information_schema.tables"  # noqa: S608
                f" WHERE table_name = '{table.alias_or_name}'",
            ).sql()).fetchone()
            if table_row is None:
                return []
            rows = cursor.execute(select("*").from_(table).sql()).fetchall()
        return [ImportManifest.from_row(row) for row in rows]

    @staticmethod
    def create_table(connection: duckdb.DuckDBPyConnection, table: Table):
        """Create table for recording import manifests."""
        drop = sqlglot.parse_one(
            f"DROP TABLE IF EXISTS {table.alias_or_name}").sql()
        create = sqlglot.parse_one(
            f"CREATE TABLE {table.alias_or_name} "
            "(unix_timestamp DOUBLE, import_config VARCHAR)",
        ).sql()
        with connection.cursor() as cursor:
            cursor.execute(drop)
            cursor.execute(create)

    @staticmethod
    def write_to_db(
        connection: duckdb.DuckDBPyConnection,
        table: Table,
        import_config: PhenoImportConfig,
    ):
        """Write manifest into DB on given table."""
        config_json = import_config.model_dump_json()
        timestamp = time.time()
        query = insert(
            f"VALUES ({timestamp}, '{config_json}')", table,
        )
        with connection.cursor() as cursor:
            cursor.execute(to_duckdb_transpile(query)).fetchall()
