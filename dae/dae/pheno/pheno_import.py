import argparse
import csv
import glob
import gzip
import logging
import os
import sys
import textwrap
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO, cast

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import sqlglot
import yaml
from pydantic import BaseModel
from sqlglot.expressions import (
    Table,
    insert,
    select,
    table_,
)

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    NumberHistogram,
)
from dae.pedigrees.family import ALL_FAMILY_TAG_LABELS
from dae.pedigrees.loader import (
    FamiliesLoader,
)
from dae.pheno.common import (
    DataDictionaryConfig,
    InferenceConfig,
    InstrumentConfig,
    MeasureDescriptionsConfig,
    MeasureType,
    PhenoImportConfig,
)
from dae.pheno.db import safe_db_name
from dae.pheno.pheno_data import PhenotypeData, PhenotypeGroup, PhenotypeStudy
from dae.pheno.prepare.measure_classifier import (
    InferenceReport,
    determine_histogram_type,
    inference_reference_impl,
)
from dae.task_graph.cli_tools import TaskCache, TaskGraphCli
from dae.task_graph.executor import task_graph_run_with_results
from dae.task_graph.graph import TaskGraph
from dae.utils.sql_utils import to_duckdb_transpile
from dae.variants.attributes import Status

logger = logging.getLogger(__name__)


# ruff: noqa: S608


IMPORT_METADATA_TABLE = table_("import_metadata")


@dataclass
class ImportInstrument:
    files: list[Path]
    name: str
    delimiter: str
    person_column: str


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype database import tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        help="Set the verbosity level. [default: %(default)s]",
    )

    parser.add_argument(
        "-i",
        "--instruments",
        dest="instruments",
        help="The directory where all instruments are located.",
        metavar="<instruments dir>",
    )

    parser.add_argument("--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
    )

    parser.add_argument("--skip-pheno-common",
        dest="skip_pheno_common",
        action="store_true",
        help="Flag for skipping the building of the pheno common instrument.",
    )

    parser.add_argument("--inference-config",
        dest="inference_config",
        help="Measure classification type inference configuration",
    )

    parser.add_argument(
        "-p",
        "--pedigree",
        dest="pedigree",
        help="The pedigree file where families descriptions are located.",
        metavar="<pedigree file>",
    )

    parser.add_argument(
        "--data-dictionary",
        dest="data_dictionary",
        help="The tab separated file that contains descriptions of measures.",
        metavar="<data dictionary file>",
    )

    parser.add_argument(
        "-o", "--output", dest="output",
        help="The output directory.", default="./output",
    )

    parser.add_argument(
        "--pheno-id", dest="pheno_name", help="output pheno database name.",
    )

    parser.add_argument(
        "--regression",
        help="absolute path to a regression configuration file",
    )
    parser.add_argument(
        "--person-column",
        dest="person_column",
        default="person_id",
        help="The column in instruments files containing the person ID.",
        metavar="<person column>",
    )

    TaskGraphCli.add_arguments(parser, use_commands=False)

    return parser


def verify_phenotype_data_name(input_name: str) -> str:
    phenotype_data_name = os.path.normpath(input_name)
    # check that the given pheno name is not a directory path
    split_path = os.path.split(phenotype_data_name)
    assert not split_path[0], f"'{phenotype_data_name}' is a directory path!"
    return phenotype_data_name


def generate_phenotype_data_config(
    pheno_name: str,
    pheno_db_filename: str,
    regressions: Any,
) -> str:
    """Construct phenotype data configuration from command line arguments."""
    dbfile = os.path.join("%(wd)s", os.path.basename(pheno_db_filename))
    config = {
        "vars": {"wd": "."},
        "type": "study",
        "name": pheno_name,
        "dbfile": dbfile,
        "browser_images_url": "static/images/",
    }
    if regressions:
        regressions_dict = regressions.to_dict()
        for reg in regressions_dict["regression"].values():
            if "measure_name" in reg and reg["measure_name"] is None:
                del reg["measure_name"]
            if "measure_names" in reg and reg["measure_names"] is None:
                del reg["measure_names"]
        config["regression"] = regressions_dict["regression"]
    return yaml.dump(config)


def transform_cli_args(args: argparse.Namespace) -> PhenoImportConfig:
    """Create a pheno import config instance from CLI arguments."""
    result = {}

    result["id"] = args.pheno_name
    delattr(args, "pheno_name")

    result["input_dir"] = os.getcwd()

    result["output_dir"] = args.output
    delattr(args, "output")

    result["instrument_files"] = [args.instruments]
    delattr(args, "instruments")

    result["pedigree"] = args.pedigree
    delattr(args, "pedigree")

    result["delimiter"] = "\t" if args.tab_separated else ","
    delattr(args, "tab_separated")

    result["skip_pedigree_measures"] = args.skip_pheno_common
    delattr(args, "skip_pheno_common")

    result["inference_config"] = args.inference_config
    delattr(args, "inference_config")

    result["data_dictionary"] = {
        "file": args.data_dictionary,
    }
    delattr(args, "data_dictionary")

    if args.regression:
        result["study_config"] = {"regressions": args.regression}
        delattr(args, "regression")

    result["person_column"] = args.person_column
    delattr(args, "person_column")

    return PhenoImportConfig.model_validate(result)


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

        # Setup argument parser

    parser = pheno_cli_parser()
    args = parser.parse_args(argv)
    if args.instruments is None:
        raise ValueError("missing instruments directory parameter")
    if args.pedigree is None:
        raise ValueError("missing pedigree filename")
    if args.pheno_name is None:
        raise ValueError("missing pheno db name")

    try:
        import_config = transform_cli_args(args)
        import_pheno_data(import_config, args)
    except KeyboardInterrupt:
        return 0
    except ValueError as e:
        traceback.print_exc()

        program_name = "pheno_import.py"
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

    return 0


def get_output_parquet_files_dir(import_config: PhenoImportConfig) -> Path:
    parquet_dir = Path(import_config.output_dir) / "parquet"
    parquet_dir.mkdir(exist_ok=True)
    return parquet_dir


def import_pheno_data(
    config: PhenoImportConfig,
    task_graph_args: argparse.Namespace,
    *,
    force: bool = False,
) -> None:
    """Import pheno data into DuckDB."""
    os.makedirs(config.output_dir, exist_ok=True)

    pheno_db_filename = os.path.join(config.output_dir, f"{config.id}.db")

    if os.path.exists(pheno_db_filename):
        if not force:
            print(
                f"Pheno DB already exists at {pheno_db_filename}!\n"
                "Use --force or specify another directory.",
            )
            sys.exit(1)
        os.remove(pheno_db_filename)

    # INFERENCE CONFIGS
    inference_configs: dict[str, Any] = {}
    if config.inference_config is not None:
        if isinstance(config.inference_config, str):
            inference_configs = load_inference_configs(
                config.input_dir, config.inference_config)
        else:
            inference_configs = config.inference_config
    add_pheno_common_inference(inference_configs)

    connection = duckdb.connect(pheno_db_filename)
    create_tables(connection)

    print("READING PEDIGREE")
    start = time.time()

    ped_df = read_pedigree(connection, config.input_dir, config.pedigree)

    print(f"DONE {time.time() - start}")

    print("READING COLUMNS FROM INSTRUMENT FILE")
    start = time.time()

    instruments = collect_instruments(config)

    if not config.skip_pedigree_measures:
        instruments.append(ImportInstrument(
            [Path(config.input_dir, config.pedigree).absolute()],
            "pheno_common",
            "\t",
            config.person_column,
        ))

    instrument_measure_names = read_instrument_measure_names(instruments)

    print(f"DONE {time.time() - start}")

    print("READING AND CLASSIFYING INSTRUMENTS")
    start = time.time()

    task_graph = TaskGraph()

    task_cache = TaskCache.create(
        force=task_graph_args.force,
        cache_dir=task_graph_args.task_status_dir,
    )

    create_import_tasks(
        task_graph, instruments,
        instrument_measure_names,
        inference_configs,
        config,
    )

    start = time.time()

    instrument_pq_files = handle_measure_inference_tasks(
        connection, config, task_graph, task_cache, task_graph_args,
    )

    print(f"DONE {time.time() - start}")
    print("WRITING RESULTS")

    write_results(connection, instrument_pq_files, ped_df)

    print(f"DONE {time.time() - start}")

    ImportManifest.create_table(connection, IMPORT_METADATA_TABLE)

    ImportManifest.write_to_db(connection, IMPORT_METADATA_TABLE, config)

    connection.close()

    regressions = None
    regression_config = None
    if config.study_config is not None:
        regression_config = config.study_config.regressions

    if regression_config is not None:
        if isinstance(regression_config, str):
            regressions = GPFConfigParser.load_config(
                str(Path(config.input_dir, regression_config)),
                regression_conf_schema,
            )
        else:
            regressions = regression_config

    output_config = generate_phenotype_data_config(
        config.id, pheno_db_filename, regressions)

    pheno_conf_path = Path(config.output_dir, f"{config.id}.yaml")
    pheno_conf_path.write_text(output_config)


def handle_measure_inference_tasks(
    connection: duckdb.DuckDBPyConnection,
    config: PhenoImportConfig,
    task_graph: TaskGraph,
    task_cache: TaskCache,
    task_graph_args: argparse.Namespace,
) -> dict[str, Path]:
    """Read the output of the measure inference tasks into dictionaries."""

    instrument_pq_files: dict[str, Path] = {}
    descriptions = load_descriptions(
        config.input_dir, config.data_dictionary)
    with TaskGraphCli.create_executor(
        task_cache, **vars(task_graph_args),
    ) as xtor:
        try:
            task_results = task_graph_run_with_results(task_graph, xtor)
            for (filepath, reports) in task_results:
                current_instrument = None
                for report in reports.values():
                    if current_instrument is None:
                        current_instrument = report.instrument_name
                        instrument_pq_files[current_instrument] = filepath

                    assert report.instrument_name == current_instrument
                    m_id = f"{report.instrument_name}.{report.measure_name}"
                    description = descriptions.get(m_id, "")

                    value_type = report.inference_report.value_type.__name__
                    histogram_type = \
                        report.inference_report.histogram_type.__name__

                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO measure VALUES ("
                            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                            ")",
                            parameters=[
                                m_id,
                                report.db_name,
                                report.measure_name.strip(),
                                report.instrument_name.strip(),
                                description,
                                report.measure_type.value,
                                value_type,
                                histogram_type,
                                report.inference_report.count_with_values,
                                "",
                                report.inference_report.min_value,
                                report.inference_report.max_value,
                                report.inference_report.values_domain.replace(
                                    "'", "''",
                                ),
                                report.inference_report.count_unique_values,
                            ],
                        )

        except Exception:
            logger.exception("Failed to classify measure")

    return instrument_pq_files


def collect_instruments(
    import_config: PhenoImportConfig,
) -> list[ImportInstrument]:
    """Collect all instrument files for a given import config."""

    all_instruments: dict[str, ImportInstrument] = {}

    def handle_path(raw_path: str):
        path = Path(import_config.input_dir, raw_path)
        matched_paths: list[Path] = []
        if "*" in raw_path:
            matched_paths.extend(
                Path(res).absolute()
                for res in glob.glob(str(path), recursive=True))
        elif path.is_file():
            matched_paths.append(path.absolute())
        elif path.is_dir():
            for root, _, filenames in os.walk(path):
                matched_paths.extend(Path(root, filename).absolute()
                                    for filename in filenames)

        matched_paths = list(filter(lambda m: m.suffixes[0] in (".csv", ".txt"),
                                    matched_paths))

        for match in matched_paths:
            logger.debug("instrument matched: %s", match.name)
            instrument_name = match.name.split(".")[0]
            if instrument_name not in all_instruments:
                all_instruments[instrument_name] = ImportInstrument(
                    [],
                    instrument_name,
                    import_config.delimiter,
                    import_config.person_column,
                )
            all_instruments[instrument_name].files.append(match)

    def handle_conf(conf: InstrumentConfig):
        path = Path(import_config.input_dir, conf.path).absolute()
        instrument = conf.instrument \
            if conf.instrument is not None \
            else path.name.split(".")[0]
        delimiter = conf.delimiter \
            if conf.delimiter is not None \
            else import_config.delimiter
        person_column = conf.person_column \
            if conf.person_column is not None \
            else import_config.person_column
        if conf.instrument not in all_instruments:
            all_instruments[instrument] = ImportInstrument(
                [], instrument, delimiter, person_column,
            )
        all_instruments[instrument].files.append(path)

    for config in import_config.instrument_files:
        if isinstance(config, str):
            handle_path(config)
        elif isinstance(config, InstrumentConfig):
            handle_conf(config)
        else:
            raise TypeError(f"Encountered invalid type while processing"
                            f"instrument configurations - {type(config)}")

    return list(all_instruments.values())


def _transform_value(val: str | bool) -> str | None:  # noqa: FBT001
    if val == "":
        return None
    if val == "True":
        return "1.0"
    if val == "False":
        return "0.0"
    if isinstance(val, bool):
        return str(int(val))
    return val


class MeasureReport(BaseModel):
    measure_name: str
    instrument_name: str
    db_name: str
    measure_type: MeasureType
    inference_report: InferenceReport


def read_and_classify_measure(
    instrument: ImportInstrument,
    group_measure_names: list[str],
    import_config: PhenoImportConfig,
    group_db_name: list[str],
    group_inf_configs: list[InferenceConfig],
) -> tuple[Path, dict[str, MeasureReport]]:
    """Read a measure's values and classify from an instrument file."""

    person_id_column = import_config.person_column
    transformed_measures = defaultdict(dict)
    seen_person_ids = set()
    person_ids = []

    if instrument.name == "pheno_common":
        person_id_column = "personId"

    for instrument_filepath in instrument.files:
        delimiter = instrument.delimiter
        if instrument.name == "pheno_common":
            delimiter = "\t"

        with open_file(instrument_filepath) as csvfile:
            reader = csv.DictReader(
                filter(lambda x: x.strip() != "", csvfile),
                delimiter=delimiter,
            )

            for row in reader:
                person_id = row[person_id_column]
                if person_id not in seen_person_ids:
                    person_ids.append(person_id)
                seen_person_ids.add(person_id)
                for measure_name in group_measure_names:
                    transformed_measures[measure_name][person_id] = \
                        _transform_value(row[measure_name])

    m_zip = zip(group_measure_names,
                group_db_name,
                group_inf_configs,
                strict=True)

    output_table = {"person_id": person_ids}
    reports = {}

    for (m_name, m_dbname, m_infconf) in m_zip:
        m_values = list(transformed_measures[m_name].values())
        values, inference_report = inference_reference_impl(
            m_values, m_infconf,
        )

        inference_report.histogram_type = \
            determine_histogram_type(inference_report, m_infconf)
        m_type: MeasureType = MeasureType.raw
        if inference_report.histogram_type == NumberHistogram:
            m_type = MeasureType.continuous
        elif inference_report.histogram_type == CategoricalHistogram:
            if inference_report.value_type is str:
                m_type = MeasureType.categorical
            else:
                m_type = MeasureType.ordinal

        report = MeasureReport.model_validate({
            "measure_name": instrument.name,
            "instrument_name": m_name,
            "db_name": m_dbname,
            "measure_type": m_type,
            "inference_report": inference_report,
        })
        report.instrument_name = instrument.name
        report.measure_name = m_name
        report.db_name = m_dbname
        output_table[m_dbname] = [
            values[idx] for idx, _ in enumerate(transformed_measures[m_name])
        ]

        reports[m_name] = report

    parquet_dir = get_output_parquet_files_dir(import_config)

    out_file = parquet_dir / instrument.name

    out_file = write_to_parquet(
        instrument.name, out_file, reports, output_table,
    )

    return (out_file, reports)


def write_to_parquet(
    instrument_name: str,
    filepath: Path,
    reports: dict[str, MeasureReport],
    values_table: dict[str, list[Any]],
) -> Path:
    """Write inferred instrument measure values to parquet file."""
    column_order = []
    string_cols = set()

    fields = []

    fields.append(
        pa.field(
            "person_id",
            pa.string(),
        ),
    )

    for report in reports.values():
        if report.instrument_name != instrument_name:
            raise ValueError(
                f"Failed to create instrument table for {instrument_name}, ",
                f"measure {report.measure_name} is of a different instrument: "
                f"{report.instrument_name}",
            )
        val_type = report.inference_report.value_type
        if val_type is int:
            col_dtype = pa.int32()
        elif val_type is float:
            col_dtype = pa.float32()
        elif val_type is str:
            col_dtype = pa.string()
            string_cols.add(report.measure_name)
        else:
            raise ValueError(f"Unsupported value type {val_type}")

        column_order.append(report.measure_name)
        fields.append(pa.field(report.db_name, col_dtype))

    schema = pa.schema(
        fields,
    )

    writer = pq.ParquetWriter(
        filepath, schema,
    )

    batch = pa.RecordBatch.from_pydict(values_table, schema)  # type: ignore

    table = pa.Table.from_batches([batch], schema)

    writer.write_table(table)

    return filepath


def add_pheno_common_inference(
    config: dict[str, Any],
) -> None:
    """Add pedigree columns as skipped columns to the inference config."""
    default_cols = [
        "familyId",
        "personId",
        "momId",
        "dadId",
        "sex",
        "status",
        "role",
        "sample_id",
        "layout",
        "generated",
        "proband",
        "not_sequenced",
        "missing",
        "member_index",
    ]
    default_cols.extend(ALL_FAMILY_TAG_LABELS)
    default_cols.append("tag_family_type_full")
    for col in default_cols:
        entry = f"pheno_common.{col}"
        config[entry] = {"skip": True}


def load_inference_configs(
    input_dir: str,
    inference_config_filepath: str | None,
) -> dict[str, Any]:
    """Load import inference configuration file."""
    if inference_config_filepath:
        return cast(dict[str, Any], yaml.safe_load(
            Path(input_dir, inference_config_filepath).read_text(),
        ))
    return {}


class ImportManifest(BaseModel):
    """Import manifest for checking cache validity."""

    unix_timestamp: float
    import_config: PhenoImportConfig

    def is_older_than(self, other: "ImportManifest") -> bool:
        if self.unix_timestamp < other.unix_timestamp:
            return True
        return self.import_config != other.import_config

    @staticmethod
    def from_row(row: tuple[str, Any, str]) -> "ImportManifest":
        timestamp = float(row[0])
        import_config = PhenoImportConfig.model_validate_json(row[1])
        return ImportManifest(
            unix_timestamp=timestamp,
            import_config=import_config,
        )

    @staticmethod
    def from_table(
        connection: duckdb.DuckDBPyConnection, table: Table,
    ) -> list["ImportManifest"]:
        """Read manifests from given table."""
        with connection.cursor() as cursor:
            table_row = cursor.execute(sqlglot.parse_one(
                "SELECT * FROM information_schema.tables"
                f" WHERE table_name = '{table.alias_or_name}'",
            ).sql()).fetchone()
            if table_row is None:
                return []
            rows = cursor.execute(select("*").from_(table).sql()).fetchall()
        return [ImportManifest.from_row(row) for row in rows]

    @staticmethod
    def from_phenotype_data(
        pheno_data: PhenotypeData,
    ) -> list["ImportManifest"]:
        """Collect all manifests in a phenotype data instance."""
        is_group = pheno_data.config["type"] == "group"
        if is_group:
            leaves = cast(PhenotypeGroup, pheno_data).get_leaves()
        else:
            leaves = [cast(PhenotypeStudy, pheno_data)]

        return [
            ImportManifest.from_table(
                leaf.db.connection, IMPORT_METADATA_TABLE,
            )[0]
            for leaf in leaves
        ]

    @staticmethod
    def create_table(connection: duckdb.DuckDBPyConnection, table: Table):
        """Create table for recording import manifests."""
        query = sqlglot.parse_one(
            f"CREATE TABLE {table.alias_or_name} "
            "(unix_timestamp DOUBLE, import_config VARCHAR)",
        ).sql()
        with connection.cursor() as cursor:
            cursor.execute(query)

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


def create_tables(connection: duckdb.DuckDBPyConnection) -> None:
    """Create phenotype data tables in DuckDB."""
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
            value_type VARCHAR,
            histogram_type VARCHAR,
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
        *create_instrument,
        *create_measure,
        *create_family,
        *create_person,
    ]

    with connection.cursor() as cursor:
        for query in queries:
            cursor.execute(to_duckdb_transpile(query))


def open_file(filepath: Path) -> TextIO:
    if ".gz" in filepath.suffixes:
        return gzip.open(filepath, "rt", encoding="utf-8-sig")
    return filepath.open()


def read_instrument_measure_names(
    instruments: list[ImportInstrument],
) -> dict[str, list[str]]:
    """Read the headers of all the instrument files."""
    instrument_measure_names = {}
    for instrument in instruments:
        file_to_read = instrument.files[0]
        with open_file(file_to_read) as csvfile:
            reader = filter(
                lambda line: len(line) != 0,
                csv.reader(csvfile, delimiter=instrument.delimiter),
            )
            header = next(reader)
            instrument_measure_names[instrument.name] = [
                col for col in header[1:]
                if col != instrument.person_column
            ]
    return instrument_measure_names


def read_pedigree(
    connection: duckdb.DuckDBPyConnection,
    input_dir: str,
    pedigree_filepath: str,
) -> pd.DataFrame:
    """
    Read a pedigree file into a pandas DataFrame

    Also imports the pedigree data into the database.
    """

    ped_df = FamiliesLoader.flexible_pedigree_read(
        Path(input_dir, pedigree_filepath), enums_as_values=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO family "
            "SELECT DISTINCT family_id FROM ped_df",
        )
        cursor.execute(
            "INSERT INTO person "
            "SELECT family_id, person_id, "
            "role, status, sex, sample_id FROM ped_df ",
        )
    return ped_df


def write_results(
    connection: duckdb.DuckDBPyConnection,
    instrument_pq_files: dict[str, Path],
    ped_df: pd.DataFrame,
) -> None:
    """Write imported data into duckdb as measure value tables."""
    assert ped_df is not None
    with connection.cursor() as cursor:
        for instrument_name, pq_file in instrument_pq_files.items():
            table_name = safe_db_name(f"{instrument_name}_measure_values")
            cursor.execute(
                textwrap.dedent(f"""
                    INSERT INTO instrument VALUES
                    ('{instrument_name}', '{table_name}')
                """),
            )

            query = (
                f"CREATE TABLE {table_name} AS ("
                "SELECT "
                "ped_df.person_id, ped_df.family_id, "
                "ped_df.role, ped_df.status, ped_df.sex, "
                "pq_table.* EXCLUDE (person_id) "
                "FROM ped_df "
                f"RIGHT JOIN read_parquet('{pq_file!s}') as pq_table ON "
                "ped_df.person_id = pq_table.person_id"
                ")"
            )

            connection.execute(query)


def load_description_file(
    input_dir: str,
    config: DataDictionaryConfig,
) -> dict[str, str]:
    """Load measure descriptions for single data dictionary."""
    out = {}
    abspath = Path(input_dir, config.path).absolute()
    assert abspath.exists(), abspath
    with open_file(abspath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=config.delimiter)
        for row in reader:
            instrument_name = config.instrument or row[config.instrument_column]
            measure_name = row[config.measure_column]
            measure_id = f"{instrument_name}.{measure_name}"
            out[measure_id] = row[config.description_column]
    return out


def load_descriptions(
    input_dir: str,
    config: MeasureDescriptionsConfig | None,
) -> dict[str, str]:
    """Load measure descriptions from given configuration."""
    descriptions: dict[str, str] = {}

    if not config:
        return descriptions

    if config.files is not None:
        for datadictfile in config.files:
            descriptions.update(load_description_file(input_dir, datadictfile))

    if config.dictionary is not None:
        for instrument, m_descs in config.dictionary.items():
            for measure, description in m_descs.items():
                measure_id = f"{instrument}.{measure}"
                descriptions[measure_id] = description

    return descriptions


def merge_inference_configs(
    inference_configs: dict[str, Any],
    instrument_name: str,
    measure_name: str,
) -> InferenceConfig:
    """Merge configs by order of specificity"""
    inference_config = InferenceConfig()
    current_config = inference_config.model_dump()

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

    return InferenceConfig.model_validate(current_config)


def create_import_tasks(
    task_graph: TaskGraph,
    instruments: list[ImportInstrument],
    instrument_measure_names: dict[str, list[str]],
    inference_configs: dict[str, Any],
    import_config: PhenoImportConfig,
) -> None:
    """Add measure tasks for importing pheno data."""
    for instrument in instruments:
        seen_col_names: dict[str, int] = defaultdict(int)
        table_column_names = [
            "person_id", "family_id", "role", "status", "sex",
        ]
        measure_names = instrument_measure_names[instrument.name]

        group_measure_names = []
        group_db_names = []
        group_inf_configs = []

        for measure_name in measure_names:
            inference_config = merge_inference_configs(
                inference_configs, instrument.name, measure_name,
            )
            if inference_config.skip:
                continue

            db_name = safe_db_name(measure_name)
            if db_name in table_column_names:
                seen_col_names[measure_name] += 1
                db_name = f"{measure_name}_{seen_col_names[measure_name]}"
            else:
                seen_col_names[measure_name] += 1
            table_column_names.append(db_name)

            group_measure_names.append(measure_name)
            group_db_names.append(db_name)
            group_inf_configs.append(inference_config)

        task_graph.create_task(
            f"{instrument.name}_read_and_classify",
            read_and_classify_measure,
            [
                instrument,
                group_measure_names,
                import_config,
                group_db_names,
                group_inf_configs,
            ],
            [],
        )


if __name__ == "__main__":
    main(sys.argv[1:])
