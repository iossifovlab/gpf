import argparse
import csv
import glob
import gzip
import json
import logging
import os
import shutil
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
import sqlglot.expressions as exp
import yaml
from pydantic import BaseModel

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    HistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.family import ALL_FAMILY_TAG_LABELS
from dae.pedigrees.loader import (
    FamiliesLoader,
)
from dae.pheno.common import (
    IMPORT_METADATA_TABLE,
    DataDictionaryConfig,
    ImportManifest,
    InferenceConfig,
    InstrumentConfig,
    InstrumentDescriptionsConfig,
    InstrumentDictionaryConfig,
    MeasureDescriptionsConfig,
    MeasureHistogramConfigs,
    MeasureType,
    PhenoImportConfig,
    RegressionMeasure,
    StudyConfig,
)
from dae.pheno.db import safe_db_name
from dae.pheno.pheno_data import (
    get_pheno_db_dir,
)
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

    parser.add_argument(
        "--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
    )

    parser.add_argument(
        "--skip-pheno-common",
        dest="skip_pheno_common",
        action="store_true",
        help="Flag for skipping the building of the pheno common instrument.",
    )

    parser.add_argument(
        "--inference-config",
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
        "--instrument-dictionary",
        dest="instrument_dictionary",
        help=(
            "The tab separated file that contains descriptions of instruments."
        ),
        metavar="<instrument dictionary file>",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="The output directory.",
        default="./output",
    )

    parser.add_argument(
        "--pheno-id",
        dest="pheno_name",
        help="output pheno database name.",
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


def generate_phenotype_data_config(
    pheno_name: str,
    storage_id: str | None,
    overrides: StudyConfig | None,
) -> str:
    """Construct phenotype data configuration from command line arguments."""
    config: dict[str, Any] = {
        "type": "study",
        "id": pheno_name,
        "name": pheno_name,
        "browser_images_url": "static/images/",
    }
    if storage_id is not None:
        config["phenotype_storage"] = {
            "id": storage_id,
            "db": f"{pheno_name}/{pheno_name}.db",
        }
    if overrides is None:
        return yaml.dump(config)

    overrides_dict = overrides.model_dump()
    if overrides.common_report is None:
        del overrides_dict["common_report"]
    if overrides.person_set_collections is None:
        del overrides_dict["person_set_collections"]
    config.update(overrides_dict)
    return yaml.dump(config)


def transform_cli_args(args: argparse.Namespace) -> PhenoImportConfig:
    """Create a pheno import config instance from CLI arguments."""
    result = {}

    result["id"] = args.pheno_name
    delattr(args, "pheno_name")

    result["input_dir"] = os.getcwd()

    result["work_dir"] = args.output
    delattr(args, "output")

    result["instrument_files"] = [args.instruments]
    delattr(args, "instruments")

    result["pedigree"] = args.pedigree
    delattr(args, "pedigree")

    result["person_column"] = args.person_column
    delattr(args, "person_column")

    result["delimiter"] = "\t" if args.tab_separated else ","
    delattr(args, "tab_separated")

    result["skip_pedigree_measures"] = args.skip_pheno_common
    delattr(args, "skip_pheno_common")

    result["inference_config"] = args.inference_config
    delattr(args, "inference_config")

    if args.data_dictionary:
        result["data_dictionary"] = {
            "files": [{"path": args.data_dictionary}],
        }
        delattr(args, "data_dictionary")

    if args.instrument_dictionary:
        result["instrument_dictionary"] = {
            "files": [{"path": args.instrument_dictionary}],
        }
        delattr(args, "instrument_dictionary")

    if args.regression:
        result["study_config"] = {"regressions": args.regression}
        delattr(args, "regression")

    return PhenoImportConfig.model_validate(result)


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv
        if not argv[0].endswith("import_phenotypes"):
            logger.warning(
                "%s tool is deprecated! Use import_phenotypes.", argv[0])
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
        gpf_instance = get_gpf_instance(import_config)
        import_pheno_data(import_config, gpf_instance, args)
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
    parquet_dir = Path(import_config.work_dir) / "parquet"
    parquet_dir.mkdir(exist_ok=True)
    return parquet_dir


def get_gpf_instance(config: PhenoImportConfig) -> GPFInstance | None:
    """Return a GPF instance for an import config if it can be found."""
    if config.gpf_instance is not None:
        return GPFInstance.build(config.gpf_instance.path)
    try:
        return GPFInstance.build()
    except ValueError:
        logger.warning("Cannot build GPF instance")
    return None


def determine_destination(
    gpf_instance: GPFInstance | None, config: PhenoImportConfig,
) -> tuple[str | None, Path | None, Path | None]:
    """Determine where output should be placed based on configuration."""
    destination_storage_id = None
    data_copy_destination = None
    config_copy_destination = None
    if config.destination is not None and \
            config.destination.storage_dir is not None:
        data_copy_destination = Path(
            config.destination.storage_dir,
            config.id,
            f"{config.id}.db",
        )
        config_copy_destination = Path(
            config.destination.storage_dir,
            config.id,
            f"{config.id}.yaml",
        )
    elif gpf_instance is not None:
        if config.destination is not None:
            destination_storage_id = config.destination.storage_id
            if destination_storage_id is None:
                raise ValueError(
                    "Cannot use gpf instance and "
                    "destination without a storage id",
                )

            if destination_storage_id not in gpf_instance.phenotype_storages:
                raise ValueError(
                    f"Phenotype storage {destination_storage_id} not found in"
                    "instance!",
                )
            storage = gpf_instance.phenotype_storages.get_phenotype_storage(
                destination_storage_id,
            )
        else:
            storage = \
                gpf_instance.phenotype_storages.get_default_phenotype_storage()
        pheno_dir = get_pheno_db_dir(gpf_instance.dae_config)
        config_copy_destination = Path(
            pheno_dir,
            config.id,
            f"{config.id}.yaml",
        )
        data_copy_destination = \
            storage.base_dir / config.id / f"{config.id}.db"
    return (
        destination_storage_id,
        data_copy_destination,
        config_copy_destination,
    )


def import_pheno_data(  # pylint: disable=R0912
    config: PhenoImportConfig,
    gpf_instance: GPFInstance | None = None,
    task_graph_args: argparse.Namespace | None = None,
) -> None:
    """Import pheno data into DuckDB."""
    os.makedirs(config.work_dir, exist_ok=True)

    if task_graph_args is None:
        task_graph_args = argparse.Namespace(
            jobs=1,
            force=True,
            task_status_dir=None,
            dask_cluster_name=None,
            dask_cluster_config_file=None,
        )

    destination_storage_id, data_copy_destination, config_copy_destination = \
        determine_destination(gpf_instance, config)

    pheno_db_filename = os.path.join(config.work_dir, f"{config.id}.db")

    if os.path.exists(pheno_db_filename):
        if not task_graph_args.force:
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
                config.input_dir, config.inference_config,
            )
        else:
            inference_configs = config.inference_config
    add_pheno_common_inference(inference_configs)

    histogram_configs: MeasureHistogramConfigs | None = None
    if config.histogram_configs is not None:
        if isinstance(config.histogram_configs, str):
            histogram_configs = load_histogram_configs(
                config.input_dir, config.histogram_configs,
            )
        else:
            histogram_configs = config.histogram_configs

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
        task_progress_mode=False,
    )

    measure_descriptions = load_measure_descriptions(
        config.input_dir,
        config.data_dictionary,
    )

    instrument_descriptions = load_instrument_descriptions(
        config.input_dir,
        config.instrument_dictionary,
    )

    create_import_tasks(
        task_graph,
        instruments,
        instrument_measure_names,
        inference_configs,
        histogram_configs,
        config,
    )

    instrument_pq_files = handle_measure_inference_tasks(
        task_graph, task_cache, task_graph_args,
    )

    print(f"DONE {time.time() - start}")

    start = time.time()
    print("WRITING RESULTS")
    write_results(connection, instrument_pq_files, ped_df)
    print(f"DONE {time.time() - start}")

    start = time.time()
    print("WRITING DESCRIPTIONS")
    if measure_descriptions:
        write_descriptions(
            connection,
            "measure_id",
            "measure_descriptions",
            measure_descriptions,
        )
    if instrument_descriptions:
        write_descriptions(
            connection,
            "instrument_name",
            "instrument_descriptions",
            instrument_descriptions,
        )
    print(f"DONE {time.time() - start}")

    ImportManifest.create_table(connection, IMPORT_METADATA_TABLE)

    ImportManifest.write_to_db(connection, IMPORT_METADATA_TABLE, config)

    connection.close()

    regressions = None
    regression_config = None
    overrides = config.study_config
    if overrides is not None:
        regression_config = overrides.regressions
        if regression_config is not None:
            if isinstance(regression_config, str):
                reg_file = Path(config.input_dir, regression_config)
                with reg_file.open("r") as file:
                    regs = yaml.safe_load(file)
                if not isinstance(regs, dict):
                    raise TypeError(
                        "Invalid regressions file, should be a dictionary",
                    )
                regressions = {
                    reg_id: RegressionMeasure.model_validate(reg)
                    for reg_id, reg in regs["regression"].items()
                }
            else:
                regressions = regression_config
        overrides.regressions = regressions

    output_config = generate_phenotype_data_config(
        config.id, destination_storage_id, overrides)

    pheno_conf_path = Path(config.work_dir, f"{config.id}.yaml")
    pheno_conf_path.write_text(output_config)

    if config_copy_destination:
        config_copy_destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(pheno_conf_path, config_copy_destination)
        except shutil.SameFileError:
            logger.warning(
                "Tried to copy pheno config to where it already is %s",
                str(config_copy_destination),
            )

    if data_copy_destination:
        data_copy_destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(pheno_db_filename, data_copy_destination)
        except shutil.SameFileError:
            logger.warning(
                "Tried to copy pheno data to where it already is %s",
                str(data_copy_destination),
            )


def handle_measure_inference_tasks(
    task_graph: TaskGraph,
    task_cache: TaskCache,
    task_graph_args: argparse.Namespace,
) -> dict[str, tuple[Path, Path]]:
    """Read the output of the measure inference tasks into dictionaries."""

    instrument_pq_files: dict[str, tuple[Path, Path]] = {}
    with TaskGraphCli.create_executor(
        task_cache, **vars(task_graph_args),
    ) as xtor:
        try:
            task_results = task_graph_run_with_results(task_graph, xtor)
            for (
                instrument_name, values_filepath, reports_filepath,
            ) in task_results:
                instrument_pq_files[instrument_name] = (
                    values_filepath, reports_filepath,
                )

        except Exception:
            logger.exception("Failed to classify measure")

    return instrument_pq_files


def collect_instruments(
    import_config: PhenoImportConfig,
) -> list[ImportInstrument]:
    """Collect all instrument files for a given import config."""

    all_instruments: dict[str, ImportInstrument] = {}

    def handle_path(raw_path: str) -> None:
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

        matched_paths = list(
            filter(lambda m: m.suffixes[0] in (".csv", ".txt"), matched_paths))

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

    def handle_conf(conf: InstrumentConfig) -> None:
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
    measure_names: list[str],
    import_config: PhenoImportConfig,
    db_names: list[str],
    inf_configs: list[InferenceConfig],
    hist_configs: MeasureHistogramConfigs | None,
) -> tuple[str, Path, Path]:
    """Read a measure's values and classify from an instrument file."""

    person_id_column = import_config.person_column
    transformed_measures: dict[str, dict[str, Any]] = defaultdict(dict)
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
                for measure_name in measure_names:
                    transformed_measures[measure_name][person_id] = \
                        _transform_value(row[measure_name])

    output_table, reports = infer_measures(
        instrument,
        person_ids,
        measure_names,
        db_names,
        inf_configs,
        transformed_measures,
    )

    output_base_dir = get_output_parquet_files_dir(import_config)
    values_parquet_dir = output_base_dir / "values"
    values_parquet_dir.mkdir(exist_ok=True)
    reports_parquet_dir = output_base_dir / "reports"
    reports_parquet_dir.mkdir(exist_ok=True)

    out_file = values_parquet_dir / f"{instrument.name}.parquet"

    out_file = write_to_parquet(
        instrument.name, out_file, reports, output_table,
    )

    reports_out_file = reports_parquet_dir / f"{instrument.name}.parquet"

    reports_out_file = write_reports_to_parquet(
        reports_out_file,
        reports,
        hist_configs,
    )

    return (instrument.name, out_file, reports_out_file)


def infer_measures(
    instrument: ImportInstrument,
    person_ids: list[str],
    measure_names: list[str],
    db_names: list[str],
    inf_configs: list[InferenceConfig],
    measure_person_values: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[Any]], dict[str, MeasureReport]]:
    """Perform inference for measure values of an instrument."""
    output_table: dict[str, list[Any]] = {"person_id": person_ids}
    reports = {}

    m_zip = zip(measure_names,
                db_names,
                inf_configs,
                strict=True)

    for (m_name, m_dbname, m_infconf) in m_zip:
        m_values = list(measure_person_values[m_name].values())
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
            "measure_name": instrument.name.strip(),
            "instrument_name": m_name.strip(),
            "db_name": m_dbname,
            "measure_type": m_type,
            "inference_report": inference_report,
        })
        report.instrument_name = instrument.name
        report.measure_name = m_name
        report.db_name = m_dbname
        output_table[m_dbname] = [
            values[idx] for idx, _ in enumerate(measure_person_values[m_name])
        ]

        reports[m_name] = report

    return output_table, reports


def write_to_parquet(
    instrument_name: str,
    filepath: Path,
    reports: dict[str, MeasureReport],
    values_table: dict[str, list[Any]],
) -> Path:
    """Write inferred instrument measure values to parquet file."""
    column_order = []
    string_cols = set()

    fields: list[pa.Field] = []

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
            col_dtype: pa.DataType = pa.int32()
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

    batch = pa.RecordBatch.from_pydict(values_table, schema)

    table = pa.Table.from_batches([batch], schema)

    writer.write_table(table)

    return filepath


def add_pheno_common_inference(
    config: dict[str, Any],
) -> None:
    """Add pedigree columns as skipped columns to the inference config."""
    default_cols = [
        "familyId", "personId", "momId",
        "dadId", "sex", "status", "role",
        "sample_id", "layout", "generated",
        "proband", "not_sequenced", "missing",
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


def load_histogram_configs(
    input_dir: str,
    histogram_config_filepath: str | None,
) -> MeasureHistogramConfigs | None:
    """Load import histogram configuration file."""
    if histogram_config_filepath:
        return MeasureHistogramConfigs.model_validate(yaml.safe_load(
            Path(input_dir, histogram_config_filepath).read_text(),
        ))
    return None


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
            measure_type INT,
            value_type VARCHAR,
            histogram_type VARCHAR,
            histogram_config VARCHAR,
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
            dad_id VARCHAR,
            mom_id VARCHAR,
            layout VARCHAR,
            generated BOOLEAN DEFAULT false,
            not_sequenced BOOLEAN DEFAULT false,
            tag_nuclear_family BOOLEAN DEFAULT false,
            tag_quad_family BOOLEAN DEFAULT false,
            tag_trio_family BOOLEAN DEFAULT false,
            tag_simplex_family BOOLEAN DEFAULT false,
            tag_multiplex_family BOOLEAN DEFAULT false,
            tag_control_family BOOLEAN DEFAULT false,
            tag_affected_dad_family BOOLEAN DEFAULT false,
            tag_affected_mom_family BOOLEAN DEFAULT false,
            tag_affected_prb_family BOOLEAN DEFAULT false,
            tag_affected_sib_family BOOLEAN DEFAULT false,
            tag_unaffected_dad_family BOOLEAN DEFAULT false,
            tag_unaffected_mom_family BOOLEAN DEFAULT false,
            tag_unaffected_prb_family BOOLEAN DEFAULT false,
            tag_unaffected_sib_family BOOLEAN DEFAULT false,
            tag_male_prb_family BOOLEAN DEFAULT false,
            tag_female_prb_family BOOLEAN DEFAULT false,
            tag_missing_mom_family BOOLEAN DEFAULT false,
            tag_missing_dad_family BOOLEAN DEFAULT false,
            member_index INT NOT NULL,
            PRIMARY KEY (family_id, person_id)
        );
        CREATE UNIQUE INDEX person_person_id_idx
            ON person (person_id);
        """,
    ))

    create_instrument_descriptions = sqlglot.parse(textwrap.dedent(
        """
        CREATE TABLE IF NOT EXISTS instrument_descriptions(
            instrument_name VARCHAR NOT NULL UNIQUE PRIMARY KEY,
            description VARCHAR,
        );
        CREATE UNIQUE INDEX IF NOT EXISTS
            instrument_descriptions_instrument_name_idx
            ON instrument_descriptions (instrument_name);
        """,
    ))

    create_measure_descriptions = sqlglot.parse(textwrap.dedent(
        """
        CREATE TABLE IF NOT EXISTS measure_descriptions(
            measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
            description VARCHAR,
        );
        CREATE UNIQUE INDEX IF NOT EXISTS
            measure_descriptions_measure_id_idx
            ON measure_descriptions (measure_id);
        """,
    ))

    queries = [
        *create_instrument,
        *create_measure,
        *create_family,
        *create_person,
        *create_instrument_descriptions,
        *create_measure_descriptions,
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

    initial_ped_df = FamiliesLoader.flexible_pedigree_read(
        Path(input_dir, pedigree_filepath), enums_as_values=True,
    )
    families = FamiliesLoader.build_families_data_from_pedigree(
        initial_ped_df, {"ped_layout_mode": "generate"},
    )

    columns: list[str] = [
        "family_id",
        "person_id",
        "role",
        "status",
        "sex",
        "sample_id",
        "dad_id",
        "mom_id",
        "layout",
        "generated",
        "not_sequenced",
        "tag_nuclear_family",
        "tag_quad_family",
        "tag_trio_family",
        "tag_simplex_family",
        "tag_multiplex_family",
        "tag_control_family",
        "tag_affected_dad_family",
        "tag_affected_mom_family",
        "tag_affected_prb_family",
        "tag_affected_sib_family",
        "tag_unaffected_dad_family",
        "tag_unaffected_mom_family",
        "tag_unaffected_prb_family",
        "tag_unaffected_sib_family",
        "tag_male_prb_family",
        "tag_female_prb_family",
        "tag_missing_mom_family",
        "tag_missing_dad_family",
        "member_index",
    ]

    ped_df = families.ped_df
    ped_df["role"] = ped_df["role"].apply(lambda x: x.value)
    ped_df["status"] = ped_df["status"].apply(lambda x: x.value)
    ped_df["sex"] = ped_df["sex"].apply(lambda x: x.value)

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO family "
            "SELECT DISTINCT family_id FROM ped_df",
        )
        cursor.execute(
            f"INSERT INTO person "
            f"SELECT {', '.join(columns)} FROM ped_df ",
        )
    return ped_df


def write_results(
    connection: duckdb.DuckDBPyConnection,
    instrument_pq_files: dict[str, tuple[Path, Path]],
    ped_df: pd.DataFrame,
) -> None:
    """Write imported data into duckdb as measure value tables."""
    assert ped_df is not None
    with connection.cursor() as cursor:
        for instrument_name, pq_files in instrument_pq_files.items():
            values_file, reports_file = pq_files
            table_name = safe_db_name(f"{instrument_name}_measure_values")
            cursor.execute(
                textwrap.dedent(f"""
                    INSERT INTO instrument VALUES
                    ('{instrument_name}', '{table_name}')
                """),
            )

            query = (
                "INSERT INTO measure "
                f"SELECT * from read_parquet('{reports_file!s}')"
            )
            cursor.execute(query)

            query = (
                f"CREATE TABLE {table_name} AS ("
                "SELECT "
                "ped_df.person_id, ped_df.family_id, "
                "ped_df.role, ped_df.status, ped_df.sex, "
                "pq_table.* EXCLUDE (person_id) "
                "FROM ped_df "
                f"RIGHT JOIN read_parquet('{values_file!s}') as pq_table ON "
                "ped_df.person_id = pq_table.person_id "
                "WHERE ped_df.person_id IS NOT NULL"
                ")"
            )

            connection.execute(query)


def write_descriptions(
    connection: duckdb.DuckDBPyConnection,
    primary_column: str,
    table_name: str,
    descriptions: dict[str, str],
) -> None:
    """Write descriptions into duckdb as description table."""
    with connection.cursor() as cursor:
        table_name = safe_db_name(table_name)
        query = exp.insert(
            exp.values(descriptions.items()),
            table_name,
            columns=[primary_column, "description"],
        )
        cursor.execute(to_duckdb_transpile(query))


def load_measure_description_file(
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
            instrument_name = config.instrument or \
                row[config.instrument_column]
            measure_name = row[config.measure_column]
            measure_id = f"{instrument_name}.{measure_name}"
            out[measure_id] = row[config.description_column]
    return out


def load_measure_descriptions(
    input_dir: str,
    measure_config: MeasureDescriptionsConfig | None,
) -> dict[str, str]:
    """Load measure descriptions from given configuration."""
    descriptions: dict[str, str] = {}

    if measure_config is not None:
        if measure_config.files is not None:
            for measuredictfile in measure_config.files:
                descriptions.update(
                    load_measure_description_file(
                        input_dir,
                        measuredictfile,
                    ),
                )

        if measure_config.dictionary is not None:
            for instrument, m_descs in measure_config.dictionary.items():
                for measure, description in m_descs.items():
                    measure_id = f"{instrument}.{measure}"
                    descriptions[measure_id] = description

    return descriptions


def load_instrument_description_file(
    input_dir: str,
    config: InstrumentDictionaryConfig,
) -> dict[str, str]:
    """Load measure descriptions for single data dictionary."""
    out = {}
    abspath = Path(input_dir, config.path).absolute()
    assert abspath.exists(), abspath
    with open_file(abspath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=config.delimiter)
        for row in reader:
            instrument_name = config.instrument or \
                row[config.instrument_column]
            out[instrument_name] = row[config.description_column]
    return out


def load_instrument_descriptions(
    input_dir: str,
    instrument_config: InstrumentDescriptionsConfig | None,
) -> dict[str, str]:
    """Load measure descriptions from given configuration."""
    descriptions: dict[str, str] = {}

    if instrument_config is not None:
        if instrument_config.files is not None:
            for instrumentdictfile in instrument_config.files:
                descriptions.update(
                    load_instrument_description_file(
                        input_dir,
                        instrumentdictfile,
                    ),
                )

        if instrument_config.dictionary is not None:
            descriptions.update(instrument_config.dictionary)

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


def merge_histogram_configs(
    histogram_configs: MeasureHistogramConfigs | None,
    measure_report: MeasureReport,
) -> HistogramConfig | None:
    """Merge configs by order of specificity"""
    histogram_config: HistogramConfig | None
    if measure_report.inference_report.histogram_type is \
            NumberHistogram:
        histogram_config = NumberHistogramConfig.default_config(None)

        if histogram_configs is None:
            return None

        configs_dict = histogram_configs.number_config
    elif measure_report.inference_report.histogram_type is \
            CategoricalHistogram:
        histogram_config = CategoricalHistogramConfig.default_config()

        if histogram_configs is None:
            return None

        configs_dict = histogram_configs.categorical_config
    else:
        return None

    instrument_name = measure_report.instrument_name
    measure_name = measure_report.measure_name
    current_config = None

    if "*.*" in configs_dict:
        update_config = configs_dict["*.*"]
        if current_config is None:
            current_config = histogram_config.to_dict()
        current_config.update(update_config)

    if f"{instrument_name}.*" in configs_dict:
        update_config = configs_dict[f"{instrument_name}.*"]
        if current_config is None:
            current_config = histogram_config.to_dict()
        current_config.update(update_config)

    if f"*.{measure_name}" in configs_dict:
        update_config = configs_dict[f"*.{measure_name}"]
        if current_config is None:
            current_config = histogram_config.to_dict()
        current_config.update(update_config)

    if f"{instrument_name}.{measure_name}" in configs_dict:
        update_config = configs_dict[
            f"{instrument_name}.{measure_name}"
        ]
        if current_config is None:
            current_config = histogram_config.to_dict()
        current_config.update(update_config)

    if current_config is None:
        return current_config

    if measure_report.inference_report.histogram_type is \
            NumberHistogram:
        return NumberHistogramConfig.from_dict(current_config)
    return CategoricalHistogramConfig.from_dict(current_config)


def create_import_tasks(
    task_graph: TaskGraph,
    instruments: list[ImportInstrument],
    instrument_measure_names: dict[str, list[str]],
    inference_configs: dict[str, Any],
    histogram_configs: MeasureHistogramConfigs | None,
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
            args=[
                instrument,
                group_measure_names,
                import_config,
                group_db_names,
                group_inf_configs,
                histogram_configs,
            ],
            deps=[],
        )


def write_reports_to_parquet(
    output_file: Path,
    reports: dict[str, MeasureReport],
    hist_configs: MeasureHistogramConfigs | None,
) -> Path:
    """Write inferred instrument measure values to parquet file."""
    fields: list[pa.Field] = [
        pa.field("measure_id", pa.string()),
        pa.field("db_column_name", pa.string()),
        pa.field("measure_name", pa.string()),
        pa.field("instrument_name", pa.string()),
        pa.field("measure_type", pa.int32()),
        pa.field("value_type", pa.string()),
        pa.field("histogram_type", pa.string()),
        pa.field("histogram_config", pa.string()),
        pa.field("individuals", pa.int32()),
        pa.field("default_filter", pa.string()),
        pa.field("min_value", pa.float64()),
        pa.field("max_value", pa.float64()),
        pa.field("values_domain", pa.string()),
        pa.field("rank", pa.int32()),
    ]
    batch_values: dict[str, list[Any]] = {
        "measure_id": [],
        "db_column_name": [],
        "measure_name": [],
        "instrument_name": [],
        "measure_type": [],
        "value_type": [],
        "histogram_type": [],
        "histogram_config": [],
        "individuals": [],
        "default_filter": [],
        "min_value": [],
        "max_value": [],
        "values_domain": [],
        "rank": [],
    }

    for report in reports.values():

        histogram_config = merge_histogram_configs(
            hist_configs,
            report,
        )
        if histogram_config is None:
            histogram_config_json = None
        else:
            histogram_config_json = json.dumps(histogram_config.to_dict())

        m_id = f"{report.instrument_name}.{report.measure_name}"
        value_type = report.inference_report.value_type.__name__
        histogram_type = report.inference_report.histogram_type.__name__
        values_domain = report.inference_report.values_domain.replace(
            "'", "''",
        )
        batch_values["measure_id"].append(m_id)
        batch_values["db_column_name"].append(report.db_name)
        batch_values["measure_name"].append(report.measure_name)
        batch_values["instrument_name"].append(report.instrument_name)
        batch_values["measure_type"].append(report.measure_type.value)
        batch_values["value_type"].append(value_type)
        batch_values["histogram_type"].append(histogram_type)
        batch_values["histogram_config"].append(histogram_config_json)
        batch_values["individuals"].append(
            report.inference_report.count_with_values)
        batch_values["default_filter"].append("")
        batch_values["min_value"].append(report.inference_report.min_value)
        batch_values["max_value"].append(report.inference_report.max_value)
        batch_values["values_domain"].append(values_domain)
        batch_values["rank"].append(
            report.inference_report.count_unique_values)

    schema = pa.schema(
        fields,
    )

    writer = pq.ParquetWriter(
        output_file, schema,
    )

    batch = pa.RecordBatch.from_pydict(batch_values, schema)

    table = pa.Table.from_batches([batch], schema)

    writer.write_table(table)

    return output_file


if __name__ == "__main__":
    logger.warning(
        "%s tool is deprecated! Use import_phenotypes.", sys.argv[0])

    main(sys.argv[1:])
