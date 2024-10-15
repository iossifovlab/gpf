import argparse
import csv
import os
import sys
import textwrap
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import sqlglot
import yaml

from dae.pedigrees.loader import (
    FamiliesLoader,
)
from dae.pheno.common import ImportConfig
from dae.pheno.db import safe_db_name
from dae.pheno.prepare.measure_classifier import (
    classification_reference_impl,
)
from dae.pheno.prepare.pheno_prepare import PrepareVariables
from dae.utils.sql_utils import to_duckdb_transpile
from dae.variants.attributes import Status

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
        "--instrument",
        dest="instrument",
        help="The instrument file",
        metavar="<instrument file>",
    )

    parser.add_argument("--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
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
        "-o", "--output", dest="output",
        help="The output directory.", default="./output",
    )

    parser.add_argument(
        "--pheno-id", dest="pheno_name", help="output pheno database name.",
    )

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
    config.instruments_dir = args.instrument
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
        if args.instrument is None:
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

        queries = [
            *create_instrument,
            *create_measure,
            *create_family,
            *create_person,
        ]

        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))

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

        print("READING INSTRUMENT FILE")
        start = time.time()
        file_to_read = Path(args.instrument)
        delimiter = "\t" if args.tab_separated else ","
        with file_to_read.open() as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            header = next(reader)
            measure_names = list(map(safe_db_name, header[1:]))
            person_measures_values = {}
            pedigree_people = {
                v: k for k, v in ped_df["person_id"].to_dict().items()
            }

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
                person_id = row[0]
                if person_id not in pedigree_people:
                    continue
                zipped = zip(measure_names, row[1:], strict=True)
                person_measures_values[person_id] = {
                    m_name: transform_value(value) for m_name, value in zipped
                }

        ped_df = ped_df[
            ped_df["person_id"].isin(person_measures_values.keys())
        ]

        print(f"DONE {time.time() - start}")

        print("CLASSIFYING INSTRUMENTS")
        start = time.time()

        ped_df_cols = ped_df[[
            "person_id",
            "family_id",
            "role",
            "status",
            "sex",
        ]]
        person_ids = ped_df_cols["person_id"].to_list()
        transformed_measure_values = {
            "person_id": person_ids,
            "family_id": ped_df_cols["family_id"].to_list(),
            "role": ped_df_cols["role"].to_list(),
            "status": ped_df_cols["status"].to_list(),
            "sex": ped_df_cols["sex"].to_list(),
        }
        seen_col_names = defaultdict(int)
        for measure_name in measure_names:
            values = [
                person_measures_values[p_id][measure_name]
                for p_id in person_ids
            ]
            inference_config = PrepareVariables.merge_inference_configs(
                inference_configs, instrument_name, measure_name,
            )
            if inference_config.skip:
                continue
            values, report = classification_reference_impl(
                values, inference_config,
            )

            if measure_name in transformed_measure_values:
                seen_col_names[measure_name] += 1
                db_name = f"{measure_name}_{seen_col_names[measure_name]}"
            else:
                seen_col_names[measure_name] += 1
                db_name = measure_name
            transformed_measure_values[db_name] = values
            m_id = safe_db_name(f"{instrument_name}.{measure_name}")
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO measure VALUES ("
                    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                    ")",
                    parameters=[
                        m_id,
                        db_name,
                        measure_name,
                        instrument_name,
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
        print(f"DONE {time.time() - start}")

        print("WRITING RESULTS")
        start = time.time()
        output_table_df = pd.DataFrame(  # noqa: F841
            transformed_measure_values)

        with connection.cursor() as cursor:
            table_name = "test_instrument_measure_values"
            cursor.execute(
                textwrap.dedent(f"""
                    CREATE TABLE {table_name} AS SELECT * FROM output_table_df
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


if __name__ == "__main__":
    main(sys.argv[1:])
