#!/usr/bin/env python
# encoding: utf-8

import sys
import pathlib
from typing import Optional, cast
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from sqlalchemy.sql import select, insert

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.registry import PhenoRegistry
from dae.pheno.db import safe_db_name, generate_instrument_table_name


logger = logging.getLogger("generate_common_reports")


def measures_cli_parser() -> ArgumentParser:
    """Create CLI arguments for tool."""
    parser = ArgumentParser(
        description="pheno measures table builder",
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "pheno_data_dir",
        help="Specify pheno data directory.",
        default=None,
    )

    parser.add_argument(
        "--show-pheno-dbs",
        help="This option will print available "
        "phenotype databases",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--dbs",
        help="Specify databases for creating measures table, Defaults to all.",
        default=None,
        action="append",
    )

    return parser


def main(
    argv: Optional[list[str]] = None
) -> None:
    """Run the pheno measure tables creation procedure."""
    if argv is None:
        argv = sys.argv[1:]

    parser = measures_cli_parser()
    VerbosityConfiguration.set_argumnets(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    pheno_registry = PhenoRegistry()

    pheno_configs = GPFConfigParser.collect_directory_configs(
        args.pheno_data_dir
    )

    with PhenoRegistry.CACHE_LOCK:
        for config in pheno_configs:
            path = pathlib.Path(config)
            pheno_registry.register_phenotype_data(
                PhenoRegistry.load_pheno_data(path),
                lock=False
            )

    available_dbs = pheno_registry.get_phenotype_data_ids()

    if args.show_pheno_dbs:
        for db_name in available_dbs:
            logger.warning("db: %s", db_name)
    else:
        if args.dbs is not None:
            assert all((db_name in available_dbs) for db_name in args.dbs), \
                available_dbs
            available_dbs = args.dbs

        for db_name in available_dbs:
            pheno_data = cast(
                PhenotypeStudy, pheno_registry.get_phenotype_data(db_name)
            )
            db = pheno_data.db

            db.clear_instruments_table(drop=True)
            db.clear_measures_table(drop=True)
            db.build_instruments_and_measures_table()

            instruments = pheno_data.instruments.values()
            query = insert(db.instruments)
            query_values = []
            for instrument in instruments:
                table_name = generate_instrument_table_name(
                    instrument.instrument_name
                )
                query_values.append({
                    "instrument_name": instrument.instrument_name,
                    "table_name": safe_db_name(table_name)
                })

            with pheno_data.db.pheno_engine.begin() as connection:
                connection.execute(query.values(query_values))
                connection.commit()

            selector = select(
                db.measure.c.measure_id,
                db.measure.c.instrument_name,
                db.measure.c.measure_name,
                db.measure.c.measure_type,
                db.measure.c.description,
                db.measure.c.individuals,
                db.measure.c.default_filter,
                db.measure.c.min_value,
                db.measure.c.max_value,
                db.measure.c.values_domain,
                db.measure.c.rank,
            )
            selector = selector.select_from(db.measure)
            with db.pheno_engine.begin() as connection:
                measure_rows = connection.execute(selector).fetchall()
            # pylint: disable=protected-access
            measures = {
                m.measure_id: {**m._mapping}
                for m in measure_rows
            }

            selector = select(
                db.instruments.c.id,
                db.instruments.c.instrument_name
            )
            selector = selector.select_from(db.instruments)
            with db.pheno_engine.begin() as connection:
                instruments_db = connection.execute(selector).fetchall()
            instruments_id_map = {
                instr.instrument_name: instr.id for instr in instruments_db
            }

            query = insert(db.measures)
            query_values = []
            for instrument_row in instruments_db:
                instrument_measures = pheno_data.instruments[
                    instrument_row.instrument_name
                ].measures
                seen_measure_names: dict[str, int] = {}
                for measure in instrument_measures.values():
                    measure_mapping = measures[measure.measure_id]
                    measure_mapping["instrument_id"] = instruments_id_map[
                        instrument_row.instrument_name
                    ]
                    del measure_mapping["instrument_name"]
                    db_name = safe_db_name(
                        measure.measure_id
                    )
                    if db_name.lower() in seen_measure_names:
                        seen_measure_names[db_name.lower()] += 1
                        db_name = \
                            f"{db_name}_{seen_measure_names[db_name.lower()]}"
                    else:
                        seen_measure_names[db_name.lower()] = 1

                    measure_mapping["db_column_name"] = db_name
                    query_values.append(measure_mapping)

            with pheno_data.db.pheno_engine.begin() as connection:
                connection.execute(query.values(query_values))
                connection.commit()

            db.clear_instrument_values_tables(drop=True)
            db.build_instrument_values_tables()
            db.populate_instrument_values_tables(use_old=True)


if __name__ == "__main__":
    main(sys.argv[1:])
