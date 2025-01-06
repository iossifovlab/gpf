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
from collections.abc import Callable
from itertools import chain
from pathlib import Path
from typing import Any, TextIO, cast

import duckdb
import pandas as pd
import sqlglot
import yaml
from pydantic import BaseModel

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
    DataDictionary,
    InferenceConfig,
    MeasureType,
    PhenoImportConfig,
)
from dae.pheno.db import safe_db_name
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

    result["tab_separated"] = args.tab_separated
    delattr(args, "tab_separated")

    result["skip_pedigree_measures"] = args.skip_pheno_common
    delattr(args, "skip_pheno_common")

    result["inference_config"] = args.inference_config
    delattr(args, "inference_config")

    result["data_dictionary"] = {
        "file": args.data_dictionary,
    }
    delattr(args, "data_dictionary")

    result["regression_config"] = args.regression
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

    os.makedirs(os.path.join(config.output_dir, "parquet"), exist_ok=True)

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

    instruments = collect_instruments(
        config.input_dir, config.instrument_files,
    )

    if not config.skip_pedigree_measures:
        instruments["pheno_common"] = [Path(config.pedigree).absolute()]

    instrument_measure_names = read_instrument_measure_names(
        instruments,
        config.person_column,
        tab_separated=config.tab_separated,
    )

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
        config.person_column,
        tab_separated=config.tab_separated,
    )

    print(f"DONE {time.time() - start}")

    print("WRITING RESULTS")
    start = time.time()

    imported_instruments, instrument_tables = handle_measure_inference_tasks(
        connection, config, task_graph, task_cache, task_graph_args,
        list(instruments.keys()),
    )

    for k in list(instrument_tables.keys()):
        if k not in imported_instruments:
            del instrument_tables[k]

    write_results(connection, instrument_tables, ped_df)

    print(f"DONE {time.time() - start}")

    connection.close()

    regressions = None
    if config.regression_config is not None:
        if isinstance(config.regression_config, str):
            regressions = GPFConfigParser.load_config(
                str(Path(config.input_dir, config.regression_config)),
                regression_conf_schema,
            )
        else:
            regressions = config.regression_config

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
    instruments: list[str],
) -> tuple[set[str], dict[str, Any]]:
    """Read the output of the measure inference tasks into dictionaries."""
    def default_row() -> dict[str, Any]:
        def none_val() -> None:
            return None
        return defaultdict(none_val)
    instrument_tables: dict[str, Any] = {
        instr: defaultdict(default_row)
        for instr in instruments
    }
    imported_instruments = set()
    description_builder = load_descriptions(
        config.input_dir, config.data_dictionary)
    with TaskGraphCli.create_executor(
        task_cache, **vars(task_graph_args),
    ) as xtor:
        try:
            task_result_chain = chain.from_iterable(
                task_graph_run_with_results(task_graph, xtor))
            for (values, report) in task_result_chain:
                table = instrument_tables[report.instrument_name]
                for p_id, value in values.items():
                    table[p_id][report.db_name] = value
                m_id = f"{report.instrument_name}.{report.measure_name}"
                description = ""
                if description_builder:
                    description = description_builder(
                        report.instrument_name,
                        report.measure_name,
                    )

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
                imported_instruments.add(report.instrument_name)

        except Exception:
            logger.exception("Failed to classify measure")
    return imported_instruments, instrument_tables


def collect_instruments(
    input_dir: str,
    paths: list[str],
) -> dict[str, list[Path]]:
    """Collect all instrument files from a list of paths."""
    all_filenames: list[Path] = []
    for raw_path in paths:
        path = Path(input_dir, raw_path)
        if "*" in raw_path:
            all_filenames.extend(
                Path(res).absolute()
                for res in glob.glob(str(path), recursive=True))
        elif path.is_file():
            all_filenames.append(path.absolute())
        elif path.is_dir():
            for root, _, filenames in os.walk(path):
                all_filenames.extend(Path(root, filename).absolute()
                                     for filename in filenames)

    instruments = defaultdict(list)
    for filename in all_filenames:
        basename = filename.name.split(".")[0]
        if filename.suffixes[0] not in (".csv", ".txt"):
            logger.debug(
                "filename %s is not an instrument; skipping...", filename)
            continue
        logger.debug("instrument matched: %s", filename.name)
        instruments[basename].append(filename)

    return instruments


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
    instrument_filepaths: list[Path],
    instrument_name: str,
    group_measure_names: list[str],
    person_id_column: str,
    group_db_name: list[str],
    group_inf_configs: list[InferenceConfig],
    tab_separated: bool = False,  # noqa: FBT001,FBT002
) -> list[tuple[dict[str, Any], MeasureReport]]:
    """Read a measure's values and classify from an instrument file."""
    transformed_measures = defaultdict(dict)
    output = []

    if instrument_name == "pheno_common":
        person_id_column = "personId"

    for instrument_filepath in instrument_filepaths:
        with open_file(instrument_filepath) as csvfile:
            reader = csv.DictReader(
                filter(lambda x: x.strip() != "", csvfile),
                delimiter="\t"
                if tab_separated or instrument_name == "pheno_common"
                else ",",
            )

            for row in reader:
                person_id = row[person_id_column]
                for measure_name in group_measure_names:
                    transformed_measures[measure_name][person_id] = \
                        _transform_value(row[measure_name])

    m_zip = zip(group_measure_names,
                group_db_name,
                group_inf_configs,
                strict=True)

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
            "measure_name": instrument_name,
            "instrument_name": m_name,
            "db_name": m_dbname,
            "measure_type": m_type,
            "inference_report": inference_report,
        })
        report.instrument_name = instrument_name
        report.measure_name = m_name
        report.db_name = m_dbname
        pid_to_val = {
            person_id: values[idx]
            for idx, person_id in enumerate(transformed_measures[m_name])
        }
        output.append((pid_to_val, report))

    return output


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
    instruments: dict[str, list[Path]],
    person_column: str,
    *,
    tab_separated: bool = False,
) -> dict[str, list[str]]:
    """Read the headers of all the instrument files."""
    instrument_measure_names = {}
    for instrument_name, instrument_files in instruments.items():
        delimiter = "\t" \
            if tab_separated or instrument_name == "pheno_common" \
            else ","
        file_to_read = instrument_files[0]
        with open_file(file_to_read) as csvfile:
            reader = filter(
                lambda line: len(line) != 0,
                csv.reader(csvfile, delimiter=delimiter),
            )
            header = next(reader)
            instrument_measure_names[instrument_name] = list(
                filter(lambda col: col != person_column, header[1:]),
            )
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
    instrument_tables: dict[str, Any],
    ped_df: pd.DataFrame,
) -> None:
    """Write imported data into duckdb as measure value tables."""
    with connection.cursor() as cursor:
        for instrument_name, table in instrument_tables.items():
            output_table_df = pd.DataFrame(
                table).transpose().rename_axis("person_id").reset_index()

            output_table_df = ped_df[
                ["person_id", "family_id", "role", "status", "sex"]
            ].merge(
                output_table_df,
                on="person_id", how="left",
            )

            cols = output_table_df.columns.tolist()

            # Reorder columns so that pedigree columns are first
            output_table_df = \
                output_table_df[cols[0:1] + cols[-4:] + cols[1:-4]]

            output_table_df.drop(
                output_table_df[
                    ~output_table_df["person_id"].isin(ped_df["person_id"])
                ].index,
            )

            table_name = safe_db_name(f"{instrument_name}_measure_values")
            cursor.execute(
                textwrap.dedent(f"""
                    INSERT INTO instrument VALUES
                    ('{instrument_name}', '{table_name}')
                """),
            )
            cursor.execute(
                textwrap.dedent(f"""
                    CREATE TABLE {table_name} AS
                    SELECT * FROM output_table_df
                """),
            )


def load_descriptions(
    input_dir: str,
    config: DataDictionary | None,
) -> Callable | None:
    """Load measure descriptions."""
    if not config:
        return None

    # TODO Implement support for other modes of setting
    # the data dictionary - `instrument_files` and `dictionary`
    description_path = config.file

    if not description_path:
        return None
    absolute_path = Path(input_dir, description_path).absolute()
    assert absolute_path.exists(), absolute_path

    data = pd.read_csv(absolute_path, sep="\t")

    class DescriptionDf:
        """Phenotype database support for measure descriptions."""

        def __init__(self, desc_df: pd.DataFrame):
            self.desc_df = desc_df
            header = list(desc_df)
            assert all(
                col in header
                for col in [
                    "instrumentName",
                    "measureName",
                    "measureId",
                    "description",
                ]
            ), header

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
    instruments: dict[str, Any],
    instrument_measure_names: dict[str, list[str]],
    inference_configs: dict[str, Any],
    person_column: str,
    *,
    tab_separated: bool = False,
) -> None:
    """Add measure tasks for importing pheno data."""
    for instrument_name, instrument_filenames in instruments.items():
        seen_col_names: dict[str, int] = defaultdict(int)
        table_column_names = [
            "person_id", "family_id", "role", "status", "sex",
        ]
        measure_names = instrument_measure_names[instrument_name]

        group_measure_names = []
        group_db_names = []
        group_inf_configs = []

        for measure_name in measure_names:
            inference_config = merge_inference_configs(
                inference_configs, instrument_name, measure_name,
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
            f"{instrument_name}_read_and_classify",
            read_and_classify_measure,
            [
                instrument_filenames,
                instrument_name,
                group_measure_names,
                person_column,
                group_db_names,
                group_inf_configs,
                tab_separated,
            ],
            [],
        )


if __name__ == "__main__":
    main(sys.argv[1:])
