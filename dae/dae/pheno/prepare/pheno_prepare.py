from __future__ import annotations

import logging
import os
import re
import shutil
import textwrap
from collections import defaultdict
from collections.abc import Callable
from multiprocessing.pool import AsyncResult
from typing import Any, cast

import duckdb
import numpy as np
import pandas as pd
import sqlglot
from box import Box

from dae.pedigrees.loader import (
    PED_COLUMNS_REQUIRED,
    FamiliesLoader,
    PedigreeIO,
)
from dae.pheno.common import (
    ImportConfig,
    InferenceConfig,
    MeasureType,
    check_phenotype_data_config,
    dump_config,
)
from dae.pheno.db import generate_instrument_table_name, safe_db_name
from dae.pheno.prepare.measure_classifier import (
    ClassifierReport,
    MeasureClassifier,
    convert_to_numeric,
    convert_to_string,
)
from dae.task_graph.cli_tools import TaskCache, TaskGraphCli
from dae.task_graph.executor import task_graph_run_with_results
from dae.task_graph.graph import TaskGraph
from dae.utils.sql_utils import fill_query_parameters, to_duckdb_transpile
from dae.variants.attributes import Status

logger = logging.getLogger(__name__)


class PrepareCommon:
    # pylint: disable=too-few-public-methods
    PID_COLUMN: str = "$Person_ID"
    PERSON_ID = "person_id"
    PED_COLUMNS_REQUIRED = tuple(PED_COLUMNS_REQUIRED)


class PrepareBase(PrepareCommon):
    """Base class for phenotype data preparation tasks."""

    def __init__(
        self, config: ImportConfig, inference_configs: dict[str, Any],
    ) -> None:
        assert config is not None
        self.config = config
        self.inference_configs = inference_configs
        self.persons: dict[str, Any] = {}
        self.dbfile = self.config.db_filename
        self.connection = duckdb.connect(self.dbfile)
        self.parquet_dir = os.path.join(self.config.output, "parquet")

    def build_tables(self) -> None:
        """Construct all needed table connections."""
        self._build_person_tables()
        self._build_instruments_and_measures_table()
        self._build_browser()

    def _build_person_tables(self) -> None:
        create_family = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE family(
                family_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
            );
            CREATE UNIQUE INDEX family_family_id_idx
                ON family (family_id);
            """,
        ))

        create_person = sqlglot.parse(textwrap.dedent(
            f"""
            CREATE TABLE person(
                family_id VARCHAR NOT NULL,
                person_id VARCHAR NOT NULL,
                role INT NOT NULL,
                status INT NOT NULL DEFAULT {Status.unaffected.value},
                sex INT NOT NULL,
                sample_id VARCHAR,
                PRIMARY KEY (family_id, person_id)
            );
            CREATE UNIQUE INDEX person_person_id_idx
                ON person (person_id);
            """,
        ))

        queries = [
            *create_family,
            *create_person,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))

    def _build_instruments_and_measures_table(self) -> None:
        """Create tables for instruments and measures."""
        create_instrument = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE instrument(
                instrument_name VARCHAR NOT NULL PRIMARY KEY,
                table_name VARCHAR NOT NULL,
            );
            CREATE UNIQUE INDEX instrument_instrument_name_idx
                ON instrument (instrument_name);
            """,
        ))

        create_measure = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE measure(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                db_column_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                instrument_name VARCHAR NOT NULL,
                description VARCHAR,
                measure_type INT,
                individuals INT,
                default_filter VARCHAR,
                min_value FLOAT,
                max_value FLOAT,
                values_domain VARCHAR,
                rank INT,
            );
            CREATE UNIQUE INDEX measure_measure_id_idx
                ON measure (measure_id);
            CREATE INDEX measure_measure_name_idx
                ON measure (measure_name);
            CREATE INDEX measure_measure_type_idx
                ON measure (measure_type);
            """,
        ))

        queries = [
            *create_instrument,
            *create_measure,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))

    def _build_browser(self) -> None:
        create_variable_browser = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE variable_browser(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                measure_type INT NOT NULL,
                description VARCHAR,
                values_domain VARCHAR,
                figure_distribution_small VARCHAR,
                figure_distribution VARCHAR
            );
            CREATE UNIQUE INDEX variable_browser_measure_id_idx
                ON variable_browser (measure_id);
            CREATE INDEX variable_browser_instrument_name_idx
                ON variable_browser (instrument_name);
            CREATE INDEX variable_browser_measure_name_idx
                ON variable_browser (measure_name);
            """,
        ))

        create_regression = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE regression(
                regression_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR,
                measure_name VARCHAR NOT NULL,
                display_name VARCHAR,
            );
            CREATE UNIQUE INDEX regression_regression_id_idx
                ON regression (regression_id);
            """,
        ))

        create_regression_values = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE regression_values(
                regression_id VARCHAR NOT NULL,
                measure_id VARCHAR NOT NULL,
                figure_regression VARCHAR,
                figure_regression_small VARCHAR,
                pvalue_regression_male DOUBLE,
                pvalue_regression_female DOUBLE,
                PRIMARY KEY (regression_id, measure_id)
            );
            CREATE INDEX regression_values_regression_id_idx
                ON regression_values (regression_id);
            CREATE INDEX regression_values_measure_id_idx
                ON regression_values (measure_id);
            """,
        ))

        queries = [
            *create_variable_browser,
            *create_regression,
            *create_regression_values,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))


class PreparePersons(PrepareBase):
    """Praparation of individuals DB tables."""

    def __init__(
        self, config: ImportConfig, inference_configs: dict[str, Any],
    ) -> None:
        super().__init__(config, inference_configs)
        self.pedigree_df: pd.DataFrame | None = None

    def _save_families(self, ped_df: pd.DataFrame) -> None:  # noqa: ARG002
        # pylint: disable=unused-argument
        self.connection.execute(
            "INSERT INTO family "
            "SELECT DISTINCT family_id FROM ped_df",
        )
        family_file = f"{self.parquet_dir}/family.parquet"
        self.connection.execute(
            f"COPY family TO '{family_file}' (FORMAT PARQUET)",
        )

    @staticmethod
    def _build_sample_id(sample_id: str | float | None) -> str | None:
        if (isinstance(sample_id, float) and np.isnan(sample_id)) \
                or sample_id is None:
            return None

        return str(sample_id)

    def _save_persons(self, ped_df: pd.DataFrame) -> None:
        person_file = f"{self.parquet_dir}/person.parquet"
        ped_df["sample_id"] = ped_df["sample_id"].transform(
            self._build_sample_id,
        )
        self.connection.execute(
            "INSERT INTO person "
            "SELECT family_id, person_id, "
            "role, status, sex, sample_id FROM ped_df ",
        )
        self.connection.execute(
            f"COPY person TO '{person_file}' (FORMAT PARQUET)",
        )

    def save_pedigree(self, ped_df: pd.DataFrame) -> None:
        self._save_families(ped_df)
        self._save_persons(ped_df)

    def build_pedigree(self, pedfile: PedigreeIO) -> pd.DataFrame:
        """Import pedigree data into the pheno DB."""
        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedfile, enums_as_values=True,
        )
        self.save_pedigree(ped_df)
        self.pedigree_df = ped_df
        return ped_df


class Task(PrepareCommon):
    """Preparation task that can be run in parallel."""

    def run(self) -> Task:
        raise NotImplementedError

    def done(self) -> Any:
        raise NotImplementedError

    def __call__(self) -> Task:
        return self.run()


class ClassifyMeasureTask(Task):
    """Measure classification task."""

    def __init__(
        self,
        config: InferenceConfig,
        instrument_name: str,
        instrument_table_name: str,
        measure_name: str,
        measure_desc: str | None,
        dbfile: str,
    ) -> None:
        self.config = config
        self.measure = self.create_default_measure(
            instrument_name, measure_name, measure_desc,
        )
        self.instrument_table_name = instrument_table_name
        self.rank: int | None = None
        self.classifier_report: ClassifierReport | None = None
        self.dbfile = dbfile

    @staticmethod
    def create_default_measure(
        instrument_name: str, measure_name: str, measure_desc: str | None,
    ) -> Box:
        """Create empty measrue description."""
        measure = {
            "measure_type": MeasureType.other,
            "measure_name": measure_name,
            "instrument_name": instrument_name,
            "measure_id": f"{instrument_name}.{measure_name}",
            "description": measure_desc,
            "individuals": None,
            "default_filter": None,
            "min_value": None,
            "max_value": None,
            "values_domain": None,
            "rank": None,
        }
        return Box(measure)

    def build_meta_measure(self, cursor: duckdb.DuckDBPyConnection) -> None:
        """Build measure meta data."""
        measure_type = self.measure.measure_type
        assert self.classifier_report is not None

        if measure_type in {MeasureType.continuous, MeasureType.ordinal}:
            min_value = np.min(
                cast(np.ndarray, self.classifier_report.numeric_values),
            )
            if isinstance(min_value, np.bool_):
                min_value = np.int8(min_value)
            max_value = np.max(
                cast(np.ndarray, self.classifier_report.numeric_values),
            )
            if isinstance(max_value, np.bool_):
                max_value = np.int8(max_value)
        else:
            min_value = None
            max_value = None

        distribution = self.classifier_report.calc_distribution_report(
            cursor, self.instrument_table_name,
        )

        if measure_type in {MeasureType.continuous, MeasureType.ordinal}:
            values_domain = f"[{min_value}, {max_value}]"
        else:
            unique_values = [v for (v, _) in distribution if v.strip() != ""]
            values_domain = ", ".join(sorted(unique_values))

        self.measure.min_value = min_value
        self.measure.max_value = max_value
        self.measure.values_domain = values_domain
        self.rank = self.classifier_report.count_unique_values

    def run(self) -> ClassifyMeasureTask:
        try:
            cursor = duckdb.connect(self.dbfile, read_only=True).cursor()
            table_name = self.instrument_table_name
            measure_name = self.measure.measure_name

            logging.info("classifying measure %s", self.measure.measure_id)
            if self.config.measure_type is not None:
                logging.info(
                    "Type infered as %s via config", self.config.measure_type,
                )
                self.measure.measure_type = MeasureType.from_str(
                    self.config.measure_type,
                )

                if self.measure.measure_type in {
                    MeasureType.continuous, MeasureType.ordinal,
                }:
                    result = cursor.sql(
                        f'SELECT COUNT("{measure_name}") FROM {table_name} '
                        'WHERE '
                        f'TRY_CAST("{measure_name}" AS FLOAT) != \'NaN\' AND '
                        f'"{measure_name}" IS NOT NULL',
                    ).fetchone()
                    assert result is not None
                    self.measure.individuals = result[0]

                    result = cursor.sql(
                        f'SELECT MIN("{measure_name}") FROM {table_name}'
                    ).fetchone()
                    assert result is not None
                    min_value = result[0]
                    self.measure.min_value = min_value

                    result = cursor.sql(
                        f'SELECT MAX("{measure_name}") FROM {table_name}'
                    ).fetchone()
                    assert result is not None
                    max_value = result[0]
                    self.measure.max_value = max_value
                    self.measure.values_domain = f"[{min_value}, {max_value}]"
                else:
                    self.measure.min_value = None
                    self.measure.max_value = None
                    rows = list(cursor.sql(
                        f'SELECT DISTINCT "{measure_name}" FROM {table_name}'
                        f'WHERE "{measure_name}" IS NOT NULL'
                        f'SELECT "{measure_name}", '
                        f'TRY_CAST("{measure_name}" AS FLOAT) as casted '
                        f'from {table_name} WHERE "{measure_name}" IS NOT NULL'
                        ")",
                    ).fetchall())
                    assert rows is not None
                    unique_values = [row[0] for row in rows]
                    self.measure.values_domain = ", ".join(
                        sorted(unique_values),
                    )

                return self

            classifier = MeasureClassifier(self.config)
            self.classifier_report = classifier.meta_measures(
                cursor,
                table_name,
                self.measure.measure_name,
            )
            assert self.classifier_report is not None
            self.classifier_report.set_measure(self.measure)

            self.measure.individuals = self.classifier_report.count_with_values
            self.measure.measure_type = classifier.classify(
                self.classifier_report,
            )
            self.build_meta_measure(cursor)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "problem processing measure: %s", self.measure.measure_id,
            )
        return self

    def done(self) -> Any:
        return self.measure, self.classifier_report


class MeasureValuesTask(Task):
    """Task to prepare measure values."""

    def __init__(self, measure: Box, mdf: pd.DataFrame) -> None:
        self.measure = measure
        self.mdf = mdf
        self.values: dict[tuple[int, int], Any] | None = None

    def run(self) -> MeasureValuesTask:
        measure_id = self.measure.db_id
        measure = self.measure

        values: dict[tuple[int, int], Any] = {}
        measure_values = self.mdf.to_dict(orient="records")
        for record in measure_values:
            person_id = int(record[self.PID_COLUMN])
            assert person_id, measure.measure_id
            k = (person_id, measure_id)
            value = record["value"]
            if MeasureType.is_text(measure.measure_type):
                value = convert_to_string(value)
                if value is None:
                    continue
                assert isinstance(value, str), record["value"]
            elif MeasureType.is_numeric(measure.measure_type):
                value = convert_to_numeric(value)
                if np.isnan(value):
                    continue
            else:
                raise ValueError(
                    f"measure type {measure.measure_type.name} "
                    f"on measure {measure.db_id} is not supported",
                )
            v = {
                self.PERSON_ID: person_id,
                "measure_id": measure_id,
                "value": value,
            }

            if k in values:
                logger.info(
                    "updating measure %s for person %s value %s with %s",
                    measure.measure_id,
                    record["person_id"], values[k]["value"], value)
            values[k] = v
        self.values = values
        return self

    def done(self) -> Any:
        return self.measure, self.values


class TaskQueue:
    """Queue of preparation tasks."""

    def __init__(self) -> None:
        self.queue: list[AsyncResult] = []

    def put(self, task: AsyncResult) -> None:
        self.queue.append(task)

    def empty(self) -> bool:
        return len(self.queue) == 0

    def get(self) -> AsyncResult:
        return self.queue.pop(0)


class PrepareVariables(PreparePersons):
    """Supports preparation of measurements."""

    def __init__(
        self, config: ImportConfig, inference_configs: dict[str, Any],
    ) -> None:
        super().__init__(config, inference_configs)
        self.sample_ids = None

    def _get_person_column_name(self, df: pd.DataFrame) -> str:
        if self.config.person_column:
            person_id = self.config.person_column
        else:
            person_id = df.columns[0]
        logger.debug("Person ID: %s", person_id)
        return person_id

    @staticmethod
    def _check_for_rejects(
        connection: duckdb.DuckDBPyConnection | None = None,
    ) -> bool:
        if connection is None:
            connection = duckdb.cursor()
        tables = connection.execute("SHOW TABLES")
        for table_row in tables.fetchall():
            if table_row[0] == "rejects":
                result = \
                    connection.execute(
                        "SELECT COUNT(*) from rejects",
                    ).fetchone()
                return not (result and result[0] == 0)
        return False

    def load_instrument(
        self, instrument_name: str, filenames: list[str],
    ) -> None:
        """Load all measures in an instrument."""
        assert filenames
        assert all(os.path.exists(f) for f in filenames)

        sep = ","

        if self.config.instruments_tab_separated:
            sep = "\t"

        table_name = self._instrument_tmp_table_name(instrument_name)

        filenames = [f"'{filename}'" for filename in filenames]

        filenames_list = f"[{', '.join(filenames)}]"

        # This print should be kept until the import build is stable
        # Some files when loaded with the next SQL query can cause a
        # segmentation fault due to faulty formatting
        print(f"{table_name} - {filenames_list}")

        self.connection.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM "  # noqa: S608
            f"read_csv({filenames_list}, delim='{sep}', header=true, "
            "ignore_errors=true, rejects_table='rejects')",
        )
        if self._check_for_rejects(self.connection):
            describe = self.connection.execute(f"DESCRIBE {table_name}")
            columns = {}
            for row in describe.fetchall():
                columns[row[0]] = row[1]
            reject_columns = self.connection.execute(
                "SELECT DISTINCT column_name FROM rejects",
            )
            for row in reject_columns.fetchall():
                columns[row[0].strip('"')] = "VARCHAR"
            self.connection.execute(f"DROP TABLE {table_name}")
            columns_string = ", ".join([
                f"'{k}': '{v}'" for k, v in columns.items()
            ])
            columns_string = "{" + columns_string + "}"
            self.connection.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM "  # noqa: S608
                f"read_csv({filenames_list}, delim='{sep}', "
                f"columns={columns_string})",
            )
        self.connection.execute("DROP TABLE rejects")

        self._clean_missing_person_ids(instrument_name)

    def _adjust_instrument_measure_name(
        self, instrument_name: str, measure_name: str,
    ) -> str:
        parts = [p.strip() for p in measure_name.split(".")]
        parts = [p for p in parts if p != instrument_name]
        return ".".join(parts)

    @property
    def log_filename(self) -> str:
        """Construct a filename to use for logging work on phenotype data."""
        db_filename = self.config.db_filename
        if self.config.report_only:
            filename = cast(str, self.config.report_only)
            assert db_filename == "memory"
            return filename

        filename, _ext = os.path.splitext(db_filename)
        return filename + "_report_log.tsv"

    def log_header(self) -> None:
        with open(self.log_filename, "w", encoding="utf8") as log:
            log.write(ClassifierReport.header_line())
            log.write("\n")

    def log_measure(
        self, measure: Box,
        classifier_report: ClassifierReport | None,
    ) -> None:
        """Log measure classification."""
        if classifier_report is None:
            return
        classifier_report.set_measure(measure)
        logging.info(classifier_report.log_line(short=True))

        with open(self.log_filename, "a", encoding="utf8") as log:
            log.write(classifier_report.log_line(short=True))
            log.write("\n")

    @staticmethod
    def _collect_instruments(dirname: str) -> dict[str, Any]:
        regexp = re.compile("(?P<instrument>.*)(?P<ext>\\.csv.*)")
        instruments = defaultdict(list)
        for root, _dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                basename = os.path.basename(filename)
                basename = basename.lower()
                res = regexp.match(basename)
                if not res:
                    logger.debug(
                        "filename %s is not an instrument; skipping...",
                        basename)
                    continue
                logger.debug(
                    "instrument matched: %s; file extension: %s",
                    res.group("instrument"), res.group("ext"))
                instruments[res.group("instrument")].append(
                    os.path.abspath(os.path.join(root, filename)),
                )
        return instruments

    def build_variables(
        self,
        instruments_dirname: str,
        description_path: str,
        **kwargs: Any,
    ) -> None:
        """Build and store phenotype data into an sqlite database."""
        self.log_header()

        instruments = self._collect_instruments(instruments_dirname)
        descriptions = PrepareVariables.load_descriptions(description_path)

        for instrument_name, instrument_filenames in list(instruments.items()):
            assert instrument_name is not None
            self.load_instrument(instrument_name, instrument_filenames)

        if not kwargs.get("skip_pheno_common"):
            self.prepare_pheno_common_data()

        self.connection.execute("CHECKPOINT")

        temp_dbfile_name = os.path.join(
            cast(str, kwargs["output"]), "tempdb.duckdb",
        )
        shutil.copyfile(self.dbfile, temp_dbfile_name)

        if not kwargs.get("skip_pheno_common"):
            self.build_pheno_common(temp_dbfile_name, **kwargs)

        for instrument_name in list(instruments.keys()):
            table_name = self._instrument_tmp_table_name(instrument_name)
            out = self.connection.execute(
                f"SELECT * FROM {table_name} LIMIT 1",  # noqa: S608
            )
            if len(out.fetchall()) == 0:
                logger.info(
                    "instrument %s is empty; skipping", instrument_name)
                continue
            self.build_instrument(
                instrument_name,
                temp_dbfile_name,
                descriptions=descriptions,
                **kwargs,
            )
            self.connection.execute(f"DROP TABLE {table_name}")

        instrument_file = f"{self.parquet_dir}/instrument.parquet"
        self.connection.execute(
            f"COPY instrument TO '{instrument_file}' (FORMAT PARQUET)",
        )
        measure_file = f"{self.parquet_dir}/measure.parquet"
        self.connection.execute(
            f"COPY measure TO '{measure_file}' (FORMAT PARQUET)",
        )

    def _instrument_tmp_table_name(self, instrument_name: str) -> str:
        return safe_db_name(f"{instrument_name}_data")

    def _clean_missing_person_ids(self, instrument_name: str) -> None:

        table_name = self._instrument_tmp_table_name(instrument_name)

        self.connection.execute(
            f"DELETE FROM {table_name} "  # noqa: S608
            f"WHERE {self.config.person_column} NOT IN "
            "(SELECT person_id from person)",
        )

    def prepare_pheno_common_data(self) -> None:
        """Prepare data table for pheno common."""
        assert self.pedigree_df is not None

        pheno_common_measures = set(self.pedigree_df.columns) - (
            set(self.PED_COLUMNS_REQUIRED) | {
                "sampleId", "role", "generated", "not_sequenced",
            }
        )
        pheno_common_measures = set(filter(
            lambda m: not m.startswith("tag"), pheno_common_measures,
        ))

        df = self.pedigree_df.copy(deep=True)
        assert "person_id" in df.columns
        df = df.rename(
            columns={"person_id": self.config.person_column},
        )

        pheno_common_columns = [
            self.config.person_column,
        ]
        pheno_common_columns.extend(pheno_common_measures)

        pheno_common_df = df[pheno_common_columns]
        assert pheno_common_df is not None
        tmp_table_name = self._instrument_tmp_table_name("pheno_common")
        with self.connection.cursor() as cursor:
            cursor.execute("SET GLOBAL pandas_analyze_sample=100000")
            query = sqlglot.parse_one(
                "CREATE TABLE ? AS "
                "SELECT * FROM pheno_common_df",
            )
            fill_query_parameters(query, [tmp_table_name])
            cursor.execute(to_duckdb_transpile(query))

    def build_pheno_common(
        self, temp_dbfile: str, **kwargs: dict[str, Any],
    ) -> None:
        """Build a pheno common instrument."""

        self.build_instrument(
            "pheno_common", temp_dbfile,
            descriptions=None,
            inference_configs={},
            **kwargs,
        )
        self._clean_missing_person_ids("pheno_common")
        tmp_table_name = self._instrument_tmp_table_name("pheno_common")
        self.connection.execute(
            f"DROP TABLE {tmp_table_name}",
        )

    @staticmethod
    def merge_inference_configs(
        inference_configs: dict[str, Any],
        instrument_name: str,
        measure_name: str,
    ) -> InferenceConfig:
        inference_config = InferenceConfig()
        current_config = inference_config.dict()

        if "*.*" in inference_configs:
            update_config = inference_configs["*.*"]
            current_config.update(update_config)

        if f"{instrument_name}.*" in inference_configs:
            update_config = inference_configs[f"{instrument_name}.*"]
            current_config.update(update_config)

        if f"*.{measure_name}" in inference_configs:
            update_config = inference_configs[f"*.{measure_name}"]
            current_config.update(update_config)

        if f"{instrument_name}.{measure_name}" in inference_configs:
            update_config = inference_configs[
                f"{instrument_name}.{measure_name}"
            ]
            current_config.update(update_config)

        return InferenceConfig.parse_obj(current_config)

    def insert_measures(
        self, cursor: duckdb.DuckDBPyConnection,
        instrument_name: str, measures: list[Any],
        measure_col_names: dict[str, str],
    ) -> dict[str, str]:
        """Insert classified measures into the DB."""
        output_table_cols = {
            "person_id": "VARCHAR",
            "family_id": "VARCHAR",
            "role": "INT",
            "status": "INT",
            "sex": "INT",
        }
        for measure in measures:
            db_name = measure_col_names[measure.measure_id]

            if MeasureType.is_numeric(measure.measure_type):
                output_table_cols[db_name] = "FLOAT"
            else:
                output_table_cols[db_name] = "VARCHAR"

            description = measure.description
            if isinstance(description, str):
                description = description.replace("'", "''")

            m_name = self._adjust_instrument_measure_name(
                instrument_name, measure.measure_name,
            )

            values = [
                measure.measure_id,
                m_name,
                measure.instrument_name,
                db_name,
                description,
                measure.measure_type.value,
                measure.individuals,
                measure.default_filter,
                measure.min_value,
                measure.max_value,
                measure.values_domain.replace("'", "''"),
                measure.rank,
            ]
            values = [
                f"{val}" if val is not None else None for val in values
            ]

            cursor.execute(
                "INSERT INTO measure VALUES ("
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                ")",
                parameters=[*values],
            )

        return output_table_cols

    def build_instrument(
        self, instrument_name: str,
        temp_dbfile: str,
        *,
        descriptions: Callable | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Build and store all measures in an instrument."""
        task_graph = TaskGraph()
        measures: list[Box] = []
        measure_col_names: dict[str, str] = {}
        output_table_name = generate_instrument_table_name(instrument_name)
        tmp_table_name = self._instrument_tmp_table_name(instrument_name)

        cursor = self.connection.cursor()

        def run_classify_task(classify_task: ClassifyMeasureTask) -> Any:
            classify_task.run()
            return classify_task.done()

        columns_to_exclude = {
            self.PID_COLUMN, self.PERSON_ID, self.config.person_column,
        }
        measures_in_data = [
            row[0]
            for row in cursor.execute(f"DESCRIBE {tmp_table_name}").fetchall()
            if row[0] not in columns_to_exclude
        ]

        for measure_name in measures_in_data:
            measure_desc = None

            if descriptions:
                measure_desc = descriptions(instrument_name, measure_name)

            inference_config = self.merge_inference_configs(
                self.inference_configs,
                instrument_name,
                measure_name,
            )

            print(f"Classifying {instrument_name}.{measure_name}")
            dump_config(inference_config)
            check_phenotype_data_config(inference_config)

            if inference_config.skip:
                continue

            classify_task = ClassifyMeasureTask(
                inference_config,
                instrument_name,
                tmp_table_name,
                measure_name,
                measure_desc,
                temp_dbfile,
            )
            task_graph.create_task(
                f"{instrument_name}_{measure_name}_classify",
                run_classify_task,
                [classify_task],
                [],
            )

        task_cache = TaskCache.create(
            force=cast(bool | None, kwargs.get("force")),
            cache_dir=cast(str | None, kwargs.get("task_status_dir")),
        )

        seen_measure_names: dict[str, int] = {}
        with TaskGraphCli.create_executor(task_cache, **kwargs) as xtor:
            try:
                for result in task_graph_run_with_results(task_graph, xtor):
                    measure, classifier_report = result

                    self.log_measure(measure, classifier_report)
                    if measure.measure_type == MeasureType.skipped:
                        logging.info(
                            "skip saving measure: %s; measurings: %s",
                            measure.measure_id,
                            classifier_report.count_with_values)
                        continue

                    measures.append(measure)

                    m_name = self._adjust_instrument_measure_name(
                        instrument_name, measure.measure_name,
                    )

                    db_name = safe_db_name(m_name)
                    if db_name.lower() in seen_measure_names:
                        seen_measure_names[db_name.lower()] += 1
                        db_name = \
                            f"{db_name}_{seen_measure_names[db_name.lower()]}"
                    else:
                        seen_measure_names[db_name.lower()] = 1
                    measure_col_names[measure.measure_id] = db_name
            except Exception:
                logger.exception("Failed to create images")

        if self.config.report_only:
            return

        cursor.execute(
            "INSERT INTO instrument VALUES "
            "(?, ?)",
            parameters=[instrument_name, output_table_name],
        )

        output_table_cols = self.insert_measures(
            cursor, instrument_name, measures, measure_col_names,
        )

        select_measures = []
        for measure in measures:
            db_name = measure_col_names[measure.measure_id]
            if output_table_cols[db_name] == "FLOAT":
                select_measures.append(
                        f'TRY_CAST(i."{measure.measure_name}" as FLOAT) '
                        f"as {db_name}",
                )
            else:
                select_measures.append(
                    f'i."{measure.measure_name}" as {db_name}',
                )

        cursor.execute(
            f"CREATE TABLE {output_table_name} AS FROM ("  # noqa: S608
            f'SELECT i."{self.config.person_column}" as person_id, '
            "p.family_id, p.role, p.status, p.sex, "
            f'{", ".join(select_measures)} '
            f"FROM {tmp_table_name} AS i JOIN person AS p "
            f'ON i."{self.config.person_column}" = p.person_id'
            ")",
        )
        instruments_dir = os.path.join(self.parquet_dir, "instruments")
        os.makedirs(instruments_dir, exist_ok=True)
        output_file = f"{instruments_dir}/{output_table_name}.parquet"
        self.connection.execute(
            f"COPY {output_table_name} TO '{output_file}' (FORMAT PARQUET)",
        )

    @staticmethod
    def create_default_measure(
        instrument_name: str, measure_name: str,
    ) -> Box:
        """Create default measure description."""
        measure = {
            "measure_type": MeasureType.other,
            "measure_name": measure_name,
            "instrument_name": instrument_name,
            "measure_id": f"{instrument_name}.{measure_name}",
            "individuals": None,
            "default_filter": None,
        }
        return Box(measure)

    @staticmethod
    def load_descriptions(
        description_path: str | None,
    ) -> Callable | None:
        """Load measure descriptions."""
        if not description_path:
            return None
        assert os.path.exists(
            os.path.abspath(description_path),
        ), description_path

        data = pd.read_csv(description_path, sep="\t")

        class DescriptionDf:
            """Phenotype database support for measure descriptions."""

            def __init__(self, desc_df: pd.DataFrame):
                self.desc_df = desc_df
                assert all(
                    col in list(desc_df)
                    for col in [
                        "instrumentName",
                        "measureName",
                        "measureId",
                        "description",
                    ]
                ), list(desc_df)

            def __call__(self, iname: str, mname: str) -> str | None:
                if (
                    f"{iname}.{mname}"
                    not in self.desc_df["measureId"].to_numpy()
                ):
                    return None
                row = self.desc_df.query(

                        "(instrumentName == @iname) and "
                        "(measureName == @mname)",

                )
                return cast(str, row.iloc[0]["description"])

        return DescriptionDf(data)
