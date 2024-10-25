import argparse
import csv
import logging
import os
import re
import sys
import textwrap
import time
import traceback
from collections import defaultdict
from collections.abc import Callable
from copy import copy
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd
import sqlglot
import yaml
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.pedigrees.loader import (
    FamiliesLoader,
)
from dae.pheno.common import ImportConfig, InferenceConfig
from dae.pheno.db import safe_db_name
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.prepare.measure_classifier import (
    ClassifierReport,
    classification_reference_impl,
)
from dae.pheno.prepare_data import PreparePhenoBrowserBase
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


def main(argv: list[str] | None = None) -> int:
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

        if not args.browser_only:
            import_pheno_data(args)

        if not args.import_only:
            build_browser(args)

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


def import_pheno_data(args: Any) -> None:
    """Import pheno data into DuckDB."""
    os.makedirs(args.output, exist_ok=True)

    args.pheno_db_filename = os.path.join(
        args.output, f"{args.pheno_name}.db",
    )
    if os.path.exists(args.pheno_db_filename):
        if args.force:
            os.remove(args.pheno_db_filename)
        else:
            print(
                f"Pheno DB already exists at {args.pheno_db_filename}!\n"
                "Use --force or specify another directory.",
            )
            sys.exit(1)

    config = parse_phenotype_data_config(args)
    os.makedirs(os.path.join(config.output, "parquet"), exist_ok=True)

    inference_configs: dict[str, Any] = {}
    if args.inference_config:
        inference_configs = yaml.safe_load(
            Path(args.inference_config).read_text(),
        )
    inference_configs = load_inference_configs(args.inference_config)

    connection = duckdb.connect(args.pheno_db_filename)

    create_tables(connection)

    print("READING PEDIGREE")
    start = time.time()

    ped_df = read_pedigree(connection, args.pedigree)

    print(f"DONE {time.time() - start}")

    print("READING COLUMNS FROM INSTRUMENT FILE")
    start = time.time()

    instruments = collect_instruments(args.instruments)
    instrument_measure_names = read_instrument_measure_names(
        instruments, tab_separated=args.tab_separated,
    )

    print(f"DONE {time.time() - start}")

    print("READING AND CLASSIFYING INSTRUMENTS")
    start = time.time()

    task_graph = TaskGraph()

    task_cache = TaskCache.create(
        force=cast(bool | None, args.force),
        cache_dir=cast(str | None, args.task_status_dir),
    )

    create_import_tasks(
        task_graph, instruments,
        instrument_measure_names,
        inference_configs,
        args.person_column,
    )

    def default_row() -> dict[str, Any]:
        def none_val() -> None:
            return None
        return defaultdict(none_val)
    instrument_tables: dict[str, Any] = {
        instr: defaultdict(default_row)
        for instr in instruments
    }
    description_builder = load_descriptions(args.data_dictionary)
    with TaskGraphCli.create_executor(task_cache, **vars(args)) as xtor:
        try:
            for result in task_graph_run_with_results(task_graph, xtor):
                values, report = result
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
                            description,
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

    write_results(connection, instrument_tables, ped_df)

    print(f"DONE {time.time() - start}")

    connection.close()


def build_pheno_browser(
    dbfile: str, pheno_name: str, output_dir: str,
    pheno_regressions: Box | None = None, **kwargs: Any,
) -> None:
    """Calculate and save pheno browser values to db."""

    phenodb = PhenotypeStudy(
        pheno_name, dbfile=dbfile, read_only=False,
    )

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    prep = PreparePhenoBrowserBase(
        pheno_name, phenodb, output_dir, pheno_regressions, images_dir)
    prep.run(**kwargs)


def build_browser(
    args: argparse.Namespace,
) -> None:
    """Perform browser data build step."""
    if args.regression:
        regressions = GPFConfigParser.load_config(
            args.regression, regression_conf_schema,
        )
    else:
        regressions = None
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    kwargs = copy(vars(args))
    pheno_db_filename = args.pheno_db_filename
    del kwargs["pheno_db_filename"]
    pheno_name = args.pheno_name
    del kwargs["pheno_name"]

    build_pheno_browser(
        pheno_db_filename,
        pheno_name,
        output_dir,
        regressions,
        **kwargs,
    )

    pheno_conf_path = os.path.join(
        output_dir, f"{pheno_name}.yaml",
    )

    config = yaml.dump(generate_phenotype_data_config(args, regressions))
    Path(pheno_conf_path).write_text(config)


def collect_instruments(dirname: str) -> dict[str, Any]:
    """Collect all instrument files in a directory."""
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
    """Read a measure's values and classify from an instrument file."""
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


def load_inference_configs(
    inference_config_filepath: str | None,
) -> dict[str, Any]:
    """Load import inference configuration file."""
    if inference_config_filepath:
        return cast(dict[str, Any], yaml.safe_load(
            Path(inference_config_filepath).read_text(),
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


def read_instrument_measure_names(
    instruments: dict[str, list[Path]],
    *,
    tab_separated: bool = False,
) -> dict[str, list[str]]:
    """Read the headers of all the instrument files."""
    delimiter = "\t" if tab_separated else ","
    instrument_measure_names = {}
    for instrument_name, instrument_files in instruments.items():
        file_to_read = instrument_files[0]
        with file_to_read.open() as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            header = next(reader)
            instrument_measure_names[instrument_name] = header[1:]
    return instrument_measure_names


def read_pedigree(
    connection: duckdb.DuckDBPyConnection, pedigree_filepath: str,
) -> pd.DataFrame:
    """
    Read a pedigree file into a pandas DataFrame

    Also imports the pedigree data into the database.
    """
    ped_df = FamiliesLoader.flexible_pedigree_read(
        pedigree_filepath, enums_as_values=True,
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

            output_table_df = output_table_df.merge(
                ped_df[["person_id", "family_id", "role", "status", "sex"]],
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


def merge_inference_configs(
    inference_configs: dict[str, Any],
    instrument_name: str,
    measure_name: str,
) -> InferenceConfig:
    """Merge configs by order of specificity"""
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


def create_import_tasks(
    task_graph: TaskGraph,
    instruments: dict[str, Any],
    instrument_measure_names: dict[str, list[str]],
    inference_configs: dict[str, Any],
    person_column: str,
) -> None:
    """Add measure tasks for importing pheno data."""
    for instrument_name, instrument_filenames in instruments.items():
        seen_col_names: dict[str, int] = defaultdict(int)
        table_column_names = [
            "person_id", "family_id", "role", "status", "sex",
        ]
        measure_names = instrument_measure_names[instrument_name]

        for measure_name in measure_names:
            inference_config = merge_inference_configs(
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
                    person_column,
                    db_name,
                    inference_config,
                ],
                [],
            )


if __name__ == "__main__":
    main(sys.argv[1:])
