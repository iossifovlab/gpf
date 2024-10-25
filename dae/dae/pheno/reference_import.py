import argparse
import csv
import logging
import os
import re
import sys
import textwrap
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd
import sqlglot
import yaml

from dae.pedigrees.loader import (
    FamiliesLoader,
)
from dae.pheno.common import ImportConfig, InferenceConfig
from dae.pheno.db import safe_db_name
from dae.pheno.prepare.measure_classifier import (
    ClassifierReport,
    classification_reference_impl,
)
from dae.pheno.prepare.pheno_prepare import PrepareVariables
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

    parser.add_argument(
        "--continue",
        dest="browser_only",
        help="Perform the second browser generation step on an existing DB.",
        action="store_true",
    )

    parser.add_argument(
        "--import-only",
        dest="import_only",
        help="Perform the data import step only.",
        action="store_true",
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
    args: argparse.Namespace, regressions: Any,
) -> dict[str, Any]:
    """Construct phenotype data configuration from command line arguments."""
    dbfile = os.path.join("%(wd)s", os.path.basename(args.pheno_db_filename))
    # pheno_db_path = os.path.dirname("%(wd)s")  # noqa
    config = {
        "vars": {"wd": "."},
        "phenotype_data": {
            "name": args.pheno_name,
            "dbfile": dbfile,
            "browser_images_url": "static/images/",
        },
    }
    if regressions:
        regressions_dict = regressions.to_dict()
        for reg in regressions_dict["regression"].values():
            if reg["measure_name"] is None:
                del reg["measure_name"]
            if reg["measure_names"] is None:
                del reg["measure_names"]
        config["regression"] = regressions_dict["regression"]
    return config


def parse_phenotype_data_config(args: argparse.Namespace) -> ImportConfig:
    """Construct phenotype data configuration from command line arguments."""
    config = ImportConfig()
    config.verbose = args.verbose
    config.instruments_dir = args.instruments
    config.instruments_tab_separated = args.tab_separated

    config.pedigree = args.pedigree
    config.output = args.output

    config.db_filename = args.pheno_db_filename

    return config


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Setup argument parser

        parser = pheno_cli_parser()
        args = parser.parse_args(argv)
        if args.instruments is None:
            print("missing instruments directory parameter", sys.stderr)
            raise ValueError  # noqa: TRY301
        if args.pedigree is None:
            print("missing pedigree filename", sys.stderr)
            raise ValueError  # noqa: TRY301
        if args.pheno_name is None:
            print("missing pheno db name", sys.stderr)
            raise ValueError  # noqa: TRY301

        output_dir = args.output

        os.makedirs(output_dir, exist_ok=True)

        args.pheno_db_filename = os.path.join(
            output_dir, f"{args.pheno_name}.db",
        )
        if os.path.exists(args.pheno_db_filename):
            os.remove(args.pheno_db_filename)

        config = parse_phenotype_data_config(args)
        os.makedirs(os.path.join(config.output, "parquet"), exist_ok=True)

        inference_configs: dict[str, Any] = {}
        if args.inference_config:
            inference_configs = yaml.safe_load(
                Path(args.inference_config).read_text(),
            )

        instrument_name = "test_instrument"

        connection = duckdb.connect(args.pheno_db_filename)

        create_tables(connection)

        import time
        print("READING PEDIGREE")
        start = time.time()
        ped_df = FamiliesLoader.flexible_pedigree_read(
            args.pedigree, enums_as_values=True,
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
        print(f"DONE {time.time() - start}")

        print("READING COLUMNS FROM INSTRUMENT FILE")

        instruments = collect_instruments(args.instruments)
        start = time.time()
        delimiter = "\t" if args.tab_separated else ","
        instrument_measure_names = {}
        for instrument_name, instrument_files in instruments.items():
            file_to_read = instrument_files[0]
            with file_to_read.open() as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                header = next(reader)
                instrument_measure_names[instrument_name] = \
                    list(map(safe_db_name, header[1:]))

        print(f"DONE {time.time() - start}")

        print("READING AND CLASSIFYING INSTRUMENTS")
        start = time.time()

        table_column_names = [
            "person_id", "family_id", "role", "status", "sex",
        ]
        seen_col_names = defaultdict(int)

        task_graph = TaskGraph()

        task_cache = TaskCache.create(
            force=cast(bool | None, args.force),
            cache_dir=cast(str | None, args.task_status_dir),
        )

        person_id_column = args.person_column

        for instrument_name, instrument_filenames in instruments.items():
            measure_names = instrument_measure_names[instrument_name]

            for measure_name in measure_names:
                inference_config = PrepareVariables.merge_inference_configs(
                    inference_configs, instrument_name, measure_name,
                )

                if inference_config.skip:
                    continue

                if measure_name in table_column_names:
                    seen_col_names[measure_name] += 1
                    db_name = f"{measure_name}_{seen_col_names[measure_name]}"
                else:
                    seen_col_names[measure_name] += 1
                    db_name = measure_name

                table_column_names.append(db_name)
                m_id = safe_db_name(f"{instrument_name}.{measure_name}")

                task_graph.create_task(
                    f"{m_id}_read_and_classify",
                    read_and_classify_measure,
                    [
                        instrument_filenames,
                        instrument_name,
                        measure_name,
                        person_id_column,
                        db_name,
                        inference_config,
                    ],
                    [],
                )

        def default_row():
            def none_val():
                return None
            return defaultdict(none_val)
        instrument_tables: dict[str, Any] = {
            instr: defaultdict(default_row)
            for instr in instruments
        }
        kwargs = vars(args)
        with TaskGraphCli.create_executor(task_cache, **kwargs) as xtor:
            try:
                for result in task_graph_run_with_results(task_graph, xtor):
                    values, report = result
                    table = instrument_tables[report.instrument_name]
                    for p_id, value in values.items():
                        table[p_id][report.db_name] = value
                    m_id = f"{report.instrument_name}.{report.measure_name}"

                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO measure VALUES ("
                            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                            ")",
                            parameters=[
                                m_id,
                                report.db_name,
                                report.measure_name,
                                report.instrument_name,
                                "",
                                report.measure_type.value,
                                report.count_with_values,
                                "",
                                report.min_value,
                                report.max_value,
                                report.values_domain.replace("'", "''"),
                                report.rank,
                            ],
                        )

            except Exception:
                logger.exception("Failed to classify measure")

        print(f"DONE {time.time() - start}")

        print("WRITING RESULTS")
        start = time.time()

        with connection.cursor() as cursor:
            for instrument_name, table in instrument_tables.items():
                output_table_df = pd.DataFrame(
                    table).transpose().rename_axis("person_id").reset_index()

                output_table_df = output_table_df.merge(
                    ped_df[["person_id", "family_id", "sex", "status", "role"]],
                    on="person_id", how="left",
                )

                output_table_df.drop(
                    output_table_df[
                        ~output_table_df["person_id"].isin(ped_df["person_id"])
                    ].index,
                )

                table_name = safe_db_name(f"{instrument_name}_measure_values")
                cursor.execute(
                    textwrap.dedent(f"""
                        CREATE TABLE {table_name} AS
                        SELECT * FROM output_table_df
                    """),
                )
        print(f"DONE {time.time() - start}")

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


def collect_instruments(dirname: str) -> dict[str, Any]:
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
                Path(os.path.abspath(os.path.join(root, filename))),
            )
    return instruments


def read_and_classify_measure(
    instrument_filepaths: list[Path], instrument_name: str,
    measure_name: str, person_id_column: str, db_name: str,
    inference_config: InferenceConfig,
    *,
    tab_separated: bool = False,
) -> tuple[dict[str, Any], ClassifierReport]:
    output = {}
    for instrument_filepath in instrument_filepaths:
        with instrument_filepath.open() as csvfile:
            reader = csv.DictReader(
                csvfile,
                delimiter="\t" if tab_separated else ",",
            )

            def transform_value(val: str) -> str | None:
                if val == "":
                    return None
                if val == "True":
                    return "1.0"
                if val == "False":
                    return "0.0"
                if isinstance(val, bool):
                    return str(int(val))
                return val
            for row in reader:
                person_id = row[person_id_column]
                output[person_id] = transform_value(row[measure_name])

    values, report = classification_reference_impl(
        list(output.values()), inference_config,
    )
    report.instrument_name = instrument_name
    report.measure_name = measure_name
    report.db_name = db_name

    for idx, person_id in enumerate(output):
        output[person_id] = values[idx]
    return output, report

def create_tables(connection: duckdb.DuckDBPyConnection) -> None:
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
        *create_instrument,
        *create_measure,
        *create_family,
        *create_person,
        *create_variable_browser,
        *create_regression,
        *create_regression_values,
    ]

    with connection.cursor() as cursor:
        for query in queries:
            cursor.execute(to_duckdb_transpile(query))



if __name__ == "__main__":
    main(sys.argv[1:])
