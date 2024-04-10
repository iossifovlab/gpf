from __future__ import annotations
import os
import re
import logging
from collections import defaultdict
from typing import Union, Dict, Any, Tuple, Optional, cast, Callable

from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
import numpy as np
import pandas as pd
import duckdb

from box import Box

from dae.pheno.db import generate_instrument_table_name, safe_db_name
from dae.pheno.common import MeasureType
from dae.pedigrees.loader import FamiliesLoader, PED_COLUMNS_REQUIRED, \
    PedigreeIO
from dae.pheno.prepare.measure_classifier import (
    MeasureClassifier,
    convert_to_string,
    convert_to_numeric,
    ClassifierReport,
)

logger = logging.getLogger(__name__)


class PrepareCommon:
    # pylint: disable=too-few-public-methods
    PID_COLUMN: str = "$Person_ID"
    PERSON_ID = "person_id"
    PED_COLUMNS_REQUIRED = tuple(PED_COLUMNS_REQUIRED)


class PrepareBase(PrepareCommon):
    """Base class for phenotype data preparation tasks."""

    def __init__(self, config: Box) -> None:
        assert config is not None
        self.config = config
        self.persons: dict[str, Any] = {}
        self.dbfile = self.config.db.filename
        self.connection = duckdb.connect(self.dbfile)
        self.parquet_dir = os.path.join(self.config.output, "parquet")

    def get_persons(self, force: bool = False) -> Optional[dict[str, Any]]:
        """Return dictionary of all people in the pheno DB."""
        if not self.persons or len(self.persons) == 0 or force:
            self.persons = {}
            result = self.connection.sql(
                "SELECT person_id, family_id, role, status, sex FROM person"
            )
            for row in result.fetchall():
                self.persons[row[0]] = {
                    "person_id": row[0],
                    "family_id": row[1],
                    "role": row[2],
                    "status": row[3],
                    "sex": row[4],
                }
        return self.persons


class PreparePersons(PrepareBase):
    """Praparation of individuals DB tables."""

    def __init__(self, config: Box) -> None:
        super().__init__(config)
        self.pedigree_df: Optional[pd.DataFrame] = None

    def _save_families(self, ped_df: pd.DataFrame) -> None:
        # pylint: disable=unused-argument
        self.connection.sql(
            "CREATE TABLE family AS "
            "SELECT DISTINCT family_id FROM ped_df"
        )
        family_file = f"{self.parquet_dir}/family.parquet"
        self.connection.sql(
            f"COPY family TO '{family_file}' (FORMAT PARQUET)"
        )

    @staticmethod
    def _build_sample_id(sample_id: Union[str, float, None]) -> Optional[str]:
        if (isinstance(sample_id, float) and np.isnan(sample_id)) \
                or sample_id is None:
            return None

        return str(sample_id)

    def _save_persons(self, ped_df: pd.DataFrame) -> None:
        person_file = f"{self.parquet_dir}/person.parquet"
        ped_df["sample_id"] = ped_df["sample_id"].transform(
            self._build_sample_id
        )
        self.connection.sql(
            "CREATE TABLE person AS "
            "SELECT family_id, person_id, "
            "role, status, sex, sample_id FROM ped_df "
        )
        self.connection.sql(
            f"COPY person TO '{person_file}' (FORMAT PARQUET)"
        )

    def save_pedigree(self, ped_df: pd.DataFrame) -> None:
        self._save_families(ped_df)
        self._save_persons(ped_df)

    def build_pedigree(self, pedfile: PedigreeIO) -> pd.DataFrame:
        """Import pedigree data into the pheno DB."""
        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedfile, enums_as_values=True
        )
        # ped_df = self.prepare_pedigree(ped_df)
        self.save_pedigree(ped_df)
        self.pedigree_df = ped_df
        return ped_df


class Task(PrepareCommon):
    """Preparation task that can be run in parallel."""

    def run(self) -> Task:
        raise NotImplementedError()

    def done(self) -> Any:
        raise NotImplementedError()

    def __call__(self) -> Task:
        return self.run()


class ClassifyMeasureTask(Task):
    """Measure classification task."""

    def __init__(
        self,
        config: Box,
        instrument_name: str,
        instrument_table_name: str,
        measure_name: str,
        measure_desc: str,
        dbfile: str
    ) -> None:
        self.config = config
        self.measure = self.create_default_measure(
            instrument_name, measure_name, measure_desc
        )
        self.instrument_table_name = instrument_table_name
        self.rank: Optional[int] = None
        self.classifier_report: Optional[ClassifierReport] = None
        self.dbfile = dbfile

    @staticmethod
    def create_default_measure(
        instrument_name: str, measure_name: str, measure_desc: str
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
        measure = Box(measure)
        return measure

    def build_meta_measure(self, cursor: duckdb.DuckDBPyConnection) -> None:
        """Build measure meta data."""
        measure_type = self.measure.measure_type
        assert self.classifier_report is not None

        if measure_type in set([MeasureType.continuous, MeasureType.ordinal]):
            min_value = np.min(
                cast(np.ndarray, self.classifier_report.numeric_values)
            )
            if isinstance(min_value, np.bool_):
                min_value = np.int8(min_value)
            max_value = np.max(
                cast(np.ndarray, self.classifier_report.numeric_values)
            )
            if isinstance(max_value, np.bool_):
                max_value = np.int8(max_value)
        else:
            min_value = None
            max_value = None

        distribution = self.classifier_report.calc_distribution_report(
            cursor, self.instrument_table_name
        )

        if measure_type in set([MeasureType.continuous, MeasureType.ordinal]):
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
            logging.info("classifying measure %s", self.measure.measure_id)
            classifier = MeasureClassifier(self.config)
            cursor = duckdb.connect(self.dbfile).cursor()
            self.classifier_report = classifier.meta_measures(
                cursor,
                self.instrument_table_name,
                self.measure.measure_name
            )
            assert self.classifier_report is not None
            self.classifier_report.set_measure(self.measure)

            self.measure.individuals = self.classifier_report.count_with_values
            self.measure.measure_type = classifier.classify(
                self.classifier_report
            )
            self.build_meta_measure(cursor)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem processing measure: %s", self.measure.measure_id,
                exc_info=True)
        return self

    def done(self) -> Any:
        return self.measure, self.classifier_report


class MeasureValuesTask(Task):
    """Task to prepare measure values."""

    def __init__(self, measure: Box, mdf: pd.DataFrame) -> None:
        self.measure = measure
        self.mdf = mdf
        self.values: Optional[dict[tuple[int, int], Any]] = None

    def run(self) -> MeasureValuesTask:
        measure_id = self.measure.db_id
        measure = self.measure

        values: Dict[Tuple[int, int], Any] = {}
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
                assert False, measure.measure_type.name
            v = {
                self.PERSON_ID: person_id,
                "measure_id": measure_id,
                "value": value
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

    def __init__(self, config: Box) -> None:
        super().__init__(config)
        self.sample_ids = None
        self.classifier = MeasureClassifier(config)

    def _get_person_column_name(self, df: pd.DataFrame) -> str:
        if self.config.person.column:
            person_id = self.config.person.column
        else:
            person_id = df.columns[0]
        logger.debug("Person ID: %s", person_id)
        return cast(str, person_id)

    @staticmethod
    def _check_for_rejects(
        connection: Optional[duckdb.DuckDBPyConnection] = None
    ) -> bool:
        if connection is None:
            connection = duckdb.cursor()
        tables = connection.sql("SHOW TABLES")
        for table_row in tables.fetchall():
            if table_row[0] == "rejects":
                result = \
                    connection.sql("SELECT COUNT(*) from rejects").fetchone()
                if result and result[0] == 0:
                    return False
                return True
        return False

    def load_instrument(
        self, instrument_name: str, filenames: list[str]
    ) -> None:
        """Load all measures in an instrument."""
        assert filenames
        assert all(os.path.exists(f) for f in filenames)

        sep = ","

        if self.config.instruments.tab_separated:
            sep = "\t"

        table_name = self._instrument_tmp_table_name(instrument_name)

        filenames = [f"'{filename}'" for filename in filenames]

        filenames_list = f"[{', '.join(filenames)}]"

        self.connection.sql(
            f"CREATE TABLE {table_name} AS SELECT * FROM "
            f"read_csv({filenames_list}, delim='{sep}', header=true, "
            "ignore_errors=true, rejects_table='rejects')"
        )
        if self._check_for_rejects(self.connection):
            describe = self.connection.sql(f"DESCRIBE {table_name}")
            columns = {}
            for row in describe.fetchall():
                columns[row[0]] = row[1]
            reject_columns = self.connection.sql(
                "SELECT DISTINCT column_name FROM rejects"
            )
            for row in reject_columns.fetchall():
                columns[row[0].strip('"')] = "VARCHAR"
            self.connection.sql(f"DROP TABLE {table_name}")
            columns_string = ", ".join([
                f"'{k}': '{v}'" for k, v in columns.items()
            ])
            columns_string = "{" + columns_string + "}"
            self.connection.sql(
                f"CREATE TABLE {table_name} AS SELECT * FROM "
                f"read_csv({filenames_list}, delim='{sep}', "
                f"columns={columns_string})"
            )
        self.connection.sql("DROP TABLE rejects")

        self._clean_missing_person_ids(instrument_name)

    def _adjust_instrument_measure_name(
        self, instrument_name: str, measure_name: str
    ) -> str:
        parts = [p.strip() for p in measure_name.split(".")]
        parts = [p for p in parts if p != instrument_name]
        return ".".join(parts)

    @property
    def log_filename(self) -> str:
        """Construct a filename to use for logging work on phenotype data."""
        db_filename = self.config.db.filename
        if self.config.report_only:
            filename = cast(str, self.config.report_only)
            assert db_filename == "memory"
            return filename

        filename, _ext = os.path.splitext(db_filename)
        filename = filename + "_report_log.tsv"
        return filename

    def log_header(self) -> None:
        with open(self.log_filename, "w", encoding="utf8") as log:
            log.write(ClassifierReport.header_line())
            log.write("\n")

    def log_measure(
        self, measure: Box,
        classifier_report: ClassifierReport
    ) -> None:
        """Log measure classification."""
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
                    os.path.abspath(os.path.join(root, filename))
                )
        return instruments

    def build_variables(
        self, instruments_dirname: str, description_path: str
    ) -> None:
        """Build and store phenotype data into an sqlite database."""
        self.log_header()

        instruments = self._collect_instruments(instruments_dirname)
        descriptions = PrepareVariables.load_descriptions(description_path)
        self.connection.sql(
            "CREATE TABLE instrument ("
            "instrument_name VARCHAR, "
            "table_name VARCHAR"
            ")"
        )
        self.connection.sql(
            "CREATE TABLE measure ("
            "measure_id VARCHAR, "
            "measure_name VARCHAR, "
            "instrument_name VARCHAR, "
            "db_column_name VARCHAR, "
            "description VARCHAR, "
            "measure_type INT, "
            "individuals INT, "
            "default_filter VARCHAR, "
            "min_value FLOAT, "
            "max_value FLOAT, "
            "values_domain VARCHAR, "
            "rank INTEGER"
            ")"
        )

        self.build_pheno_common()

        for instrument_name, instrument_filenames in list(instruments.items()):
            assert instrument_name is not None
            self.load_instrument(instrument_name, instrument_filenames)
            table_name = self._instrument_tmp_table_name(instrument_name)
            out = self.connection.sql(f"SELECT * FROM {table_name} LIMIT 1")
            if len(out.fetchall()) == 0:
                logger.info(
                    "instrument %s is empty; skipping", instrument_name)
                continue
            self.build_instrument(instrument_name, descriptions)
            self.connection.sql(f"DROP TABLE {table_name}")

        instrument_file = f"{self.parquet_dir}/instrument.parquet"
        self.connection.sql(
            f"COPY instrument TO '{instrument_file}' (FORMAT PARQUET)"
        )
        measure_file = f"{self.parquet_dir}/measure.parquet"
        self.connection.sql(
            f"COPY measure TO '{measure_file}' (FORMAT PARQUET)"
        )

    def _instrument_tmp_table_name(self, instrument_name: str) -> str:
        return safe_db_name(f"{instrument_name}_data")

    def _clean_missing_person_ids(self, instrument_name: str) -> None:

        table_name = self._instrument_tmp_table_name(instrument_name)

        self.connection.sql(
            f"DELETE FROM {table_name} "
            f'WHERE "{self.config.person.column}" NOT IN '
            "(SELECT person_id from person)"
        )

    def build_pheno_common(self) -> None:
        """Build a pheno common instrument."""
        assert self.pedigree_df is not None

        pheno_common_measures = set(self.pedigree_df.columns) - (
            set(self.PED_COLUMNS_REQUIRED) | set(
                ["sampleId", "role", "generated", "not_sequenced"]
            )
        )
        pheno_common_measures = set(filter(
            lambda m: not m.startswith("tag"), pheno_common_measures
        ))

        df = self.pedigree_df.copy(deep=True)
        assert "person_id" in df.columns
        df.rename(
            columns={"person_id": self.config.person.column}, inplace=True
        )

        pheno_common_columns = [
            self.config.person.column,
        ]
        pheno_common_columns.extend(pheno_common_measures)

        pheno_common_df = df[pheno_common_columns]
        assert pheno_common_df is not None
        tmp_table_name = self._instrument_tmp_table_name("pheno_common")
        cursor = self.connection.cursor()

        cursor.sql(
            f"CREATE TABLE {tmp_table_name} AS "
            "SELECT * FROM pheno_common_df"
        )

        self.build_instrument("pheno_common")
        self._clean_missing_person_ids("pheno_common")
        self.connection.sql(
            f"DROP TABLE {tmp_table_name}"
        )

    def build_instrument(
        self, instrument_name: str,
        descriptions: Optional[Callable] = None
    ) -> None:
        """Build and store all measures in an instrument."""
        classify_queue = TaskQueue()
        measures: list[Box] = []
        measure_reports: dict[str, ClassifierReport] = {}
        measure_col_names: dict[str, str] = {}
        output_table_name = generate_instrument_table_name(instrument_name)
        tmp_table_name = self._instrument_tmp_table_name(instrument_name)

        cursor = self.connection.cursor()

        with Pool(processes=self.config.parallel) as pool:
            data_measures = []
            for row in cursor.sql(f"DESCRIBE {tmp_table_name}").fetchall():
                if row[0] not in {self.PID_COLUMN, self.PERSON_ID}:
                    data_measures.append(row[0])
            for measure_name in data_measures:

                if descriptions:
                    measure_desc = descriptions(instrument_name, measure_name)
                else:
                    measure_desc = None

                classify_task = ClassifyMeasureTask(
                    self.config,
                    instrument_name,
                    tmp_table_name,
                    measure_name,
                    measure_desc,
                    self.dbfile
                )
                fut = pool.apply_async(classify_task)
                classify_queue.put(fut)

            seen_measure_names: dict[str, int] = {}
            while not classify_queue.empty():
                res = classify_queue.get()
                task = res.get()
                measure, classifier_report = task.done()
                self.log_measure(measure, classifier_report)
                if measure.measure_type == MeasureType.skipped:
                    logging.info(
                        "skip saving measure: %s; measurings: %s",
                        measure.measure_id,
                        classifier_report.count_with_values)
                    continue

                measures.append(measure)

                measure_reports[measure.measure_id] = classifier_report

                m_name = self._adjust_instrument_measure_name(
                    instrument_name, measure.measure_name
                )

                db_name = safe_db_name(m_name)
                if db_name.lower() in seen_measure_names:
                    seen_measure_names[db_name.lower()] += 1
                    db_name = \
                        f"{db_name}_{seen_measure_names[db_name.lower()]}"
                else:
                    seen_measure_names[db_name.lower()] = 1
                measure_col_names[measure.measure_id] = db_name

        if self.config.report_only:
            return

        cursor.sql(
            "INSERT INTO instrument VALUES "
            f"('{instrument_name}', '{output_table_name}')"
        )

        output_table_cols = {
            "person_id": "VARCHAR",
            "family_id": "VARCHAR",
            "role": "INT",
            "status": "INT",
            "sex": "INT"
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
                instrument_name, measure.measure_name
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
                measure.rank
            ]
            values = [
                f"'{val}'" if val is not None else "NULL" for val in values
            ]
            columns = ", ".join(values)

            cursor.sql(
                "INSERT INTO measure VALUES ("
                f"{columns}"
                ")"
            )

        select_measures = []
        for measure in measures:
            db_name = measure_col_names[measure.measure_id]
            col_type = output_table_cols[db_name]
            m_name = measure.measure_name
            if col_type == "FLOAT":
                select_measures.append(
                    f'TRY_CAST(i."{m_name}" as FLOAT) as {db_name}'
                )
            else:
                select_measures.append(f'i."{m_name}" as {db_name}')

        select_measure_cols = ", ".join(select_measures)

        cursor.sql(
            f"CREATE TABLE {output_table_name} AS FROM ("
            f'SELECT i."{self.config.person.column}" as person_id, '
            "p.family_id, p.role, p.status, p.sex, "
            f"{select_measure_cols} "
            f"FROM {tmp_table_name} AS i JOIN person AS p "
            f'ON i."{self.config.person.column}" = p.person_id'
            ")"
        )
        instruments_dir = os.path.join(self.parquet_dir, "instruments")
        os.makedirs(instruments_dir, exist_ok=True)
        output_file = f"{instruments_dir}/{output_table_name}.parquet"
        self.connection.sql(
            f"COPY {output_table_name} TO '{output_file}' (FORMAT PARQUET)"
        )

    @staticmethod
    def create_default_measure(
        instrument_name: str, measure_name: str
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
        measure = Box(measure)
        return measure

    @staticmethod
    def load_descriptions(
        description_path: Optional[str]
    ) -> Optional[Callable]:
        """Load measure descriptions."""
        if not description_path:
            return None
        assert os.path.exists(
            os.path.abspath(description_path)
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

            def __call__(self, iname: str, mname: str) -> Optional[str]:
                if (
                    f"{iname}.{mname}"
                    not in self.desc_df["measureId"].values
                ):
                    return None
                row = self.desc_df.query(
                    (
                        "(instrumentName == @iname) and "
                        "(measureName == @mname)"
                    )
                )
                return cast(str, row.iloc[0]["description"])

        return DescriptionDf(data)
