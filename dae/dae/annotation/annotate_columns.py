from __future__ import annotations
import os
import logging
import sys
import gzip
import argparse
from contextlib import closing
from typing import Optional, cast, Any

from pysam import TabixFile, tabix_index

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.record_to_annotatable import build_record_to_annotatable, \
    add_record_to_annotable_arguments, \
    RecordToRegion, RecordToCNVAllele, \
    RecordToVcfAllele, RecordToPosition
from dae.annotation.annotate_vcf import produce_regions, produce_partfile_paths
from dae.annotation.annotation_pipeline import ReannotationPipeline
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.fs_utils import tabix_index_filename

logger = logging.getLogger("annotate_columns")


def configure_argument_parser() -> argparse.ArgumentParser:
    """Configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input", default="-", nargs="?",
                        help="the input column file")
    parser.add_argument("pipeline", default="context", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument("-r", "--region-size", default=300_000_000,
                        type=int, help="region size to parallelize by")
    parser.add_argument("-w", "--work-dir",
                        help="Directory to store intermediate output files in",
                        default="annotate_columns_output")
    parser.add_argument("-o", "--output",
                        help="Filename of the output result",
                        default=None)
    parser.add_argument("-in_sep", "--input-separator", default="\t",
                        help="The column separator in the input")
    parser.add_argument("-out_sep", "--output-separator", default="\t",
                        help="The column separator in the output")
    parser.add_argument("--reannotate", default=None,
                        help="Old pipeline config to reannotate over")
    CLIAnnotationContext.add_context_arguments(parser)
    add_record_to_annotable_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def read_input(
    args: Any, region: tuple = tuple()
) -> tuple[Any, Any, list[str]]:
    """Return a file object, line iterator and list of header columns.

    Handles differences between tabixed and non-tabixed input files.
    """
    if args.input.endswith(".gz"):
        tabix_file = TabixFile(args.input)
        with gzip.open(args.input, "rt") as in_file_raw:
            header = in_file_raw.readline() \
                .strip("\r\n") \
                .split(args.input_separator)
        return closing(tabix_file), tabix_file.fetch(*region), header
    # pylint: disable=consider-using-with
    text_file = open(args.input, "rt")
    header = text_file.readline().strip("\r\n").split(args.input_separator)
    return text_file, text_file, header


def produce_tabix_index(
    filepath: str, args: Any, header: list[str],
    ref_genome: Optional[ReferenceGenome]
) -> None:
    """Produce a tabix index file for the given variants file."""
    record_to_annotatable = build_record_to_annotatable(
        vars(args), set(header), ref_genome)
    line_skip = 0 if header[0].startswith("#") else 1
    seq_col = 0
    start_col = 1
    if isinstance(record_to_annotatable, (RecordToRegion,
                                          RecordToCNVAllele)):
        end_col = 2
    elif isinstance(record_to_annotatable, (RecordToVcfAllele,
                                            RecordToPosition)):
        end_col = 1
    else:
        raise ValueError(
            "Could not generate tabix index: record"
            f" {type(record_to_annotatable)} is of unsupported type.")
    tabix_index(filepath,
                seq_col=seq_col,
                start_col=start_col,
                end_col=end_col,
                line_skip=line_skip,
                force=True)


def cache_pipeline(
    grr: GenomicResourceRepo, pipeline: AnnotationPipeline
) -> None:
    """Cache the resources used by the pipeline."""
    resource_ids: set[str] = set()
    for annotator in pipeline.annotators:
        resource_ids = resource_ids | \
            set(res.resource_id for res in annotator.resources)
    cache_resources(grr, resource_ids)


def annotate(
    args: Any,
    grr_definition: Optional[dict],
    ref_genome_id: str,
    out_file_path: str,
    region: tuple = tuple(),
    compress_output: bool = False
) -> None:
    """Annotate a variants file with a given pipeline configuration."""
    # pylint: disable=too-many-locals,too-many-branches
    grr = build_genomic_resource_repository(definition=grr_definition)

    # TODO Insisting on having the pipeline config passed in args
    # prevents the finding of a default annotation config. Consider fixing
    pipeline = build_annotation_pipeline(
        pipeline_config_file=args.pipeline,
        grr_repository=grr)

    if args.reannotate:
        pipeline_old = build_annotation_pipeline(
            pipeline_config_file=args.reannotate,
            grr_repository=grr)
        pipeline_new = pipeline
        pipeline = ReannotationPipeline(pipeline_new, pipeline_old)

    ref_genome = cast(ReferenceGenome, grr.find_resource(ref_genome_id)) \
        if ref_genome_id else None
    errors = []

    cache_pipeline(grr, pipeline)

    in_file, line_iterator, header_columns = read_input(args, region)
    record_to_annotatable = build_record_to_annotatable(
        vars(args), set(header_columns), ref_genome=ref_genome)

    annotation_columns = [
        attr.name for attr in pipeline.get_attributes()
        if not attr.internal]

    if compress_output:
        out_file = gzip.open(out_file_path, "wt")
    else:
        out_file = open(out_file_path, "wt")

    pipeline.open()
    with pipeline, in_file, out_file:
        if isinstance(pipeline, ReannotationPipeline):
            old_annotation_columns = {
                attr.name for attr in pipeline_old.get_attributes()
                if not attr.internal
            }
            new_header = [
                col for col in header_columns
                if col not in old_annotation_columns
            ]
        else:
            new_header = list(header_columns)

        new_header = new_header + annotation_columns
        out_file.write(args.output_separator.join(new_header) + "\n")
        for lnum, line in enumerate(line_iterator):
            try:
                columns = line.strip("\n\r").split(args.input_separator)
                record = dict(zip(header_columns, columns))
                if isinstance(pipeline, ReannotationPipeline):
                    for col in pipeline.attributes_deleted:
                        del record[col]
                    annotation = pipeline.annotate(
                        record_to_annotatable.build(record), record
                    )
                else:
                    annotation = pipeline.annotate(
                        record_to_annotatable.build(record)
                    )

                record.update(annotation)
                result = list(map(str, record.values()))
                out_file.write(args.output_separator.join(result) + "\n")
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning(
                    "unexpected input data format at line %s: %s",
                    lnum, line, exc_info=True)
                errors.append((lnum, line, str(ex)))

    if len(errors) > 0:
        logger.error("there were errors during the import")
        for lnum, line, error in errors:
            logger.error("line %s: %s", lnum, line)
            logger.error("\t%s", error)

    if len(errors) > 0:
        logger.error("there were errors during the import")
        for lnum, line, error in errors:
            logger.error("line %s: %s", lnum, line)
            logger.error("\t%s", error)


def combine(args: Any, partfile_paths: list[str], out_file_path: str) -> None:
    """Combine annotated region parts into a single VCF file."""
    CLIAnnotationContext.register(args)
    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)
    annotation_attributes = [
        attr.name for attr in pipeline.get_attributes()
        if not attr.internal
    ]

    with gzip.open(args.input, "rt") as in_file_raw:
        hcs = in_file_raw.readline().strip("\r\n").split(args.input_separator)
        header = args.output_separator.join(hcs + annotation_attributes)

    with open(out_file_path, "wt") as out_file:
        out_file.write(header + "\n")
        for partfile_path in partfile_paths:
            with gzip.open(partfile_path, "rt") as partfile:
                partfile.readline()  # skip header
                out_file.write(partfile.read())
    for partfile_path in partfile_paths:
        os.remove(partfile_path)
    produce_tabix_index(
        out_file_path, args, hcs, context.get_reference_genome())


def cli(raw_args: Optional[list[str]] = None) -> None:
    """Run command line interface for annotate columns."""
    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    grr = CLIAnnotationContext.get_genomic_resources_repository(context)
    ref_genome = context.get_reference_genome()
    ref_genome_id = ref_genome.resource_id if ref_genome is not None else None

    if grr is None:
        raise ValueError("No valid GRR configured. Aborting.")

    if args.output:
        output = args.output
    else:
        input_name = args.input.rstrip(".gz")
        if "." in input_name:
            idx = input_name.find(".")
            output = f"{input_name[:idx]}_annotated{input_name[idx:]}"
        else:
            output = f"{input_name}_annotated"

    if tabix_index_filename(args.input):
        with closing(TabixFile(args.input)) as pysam_file:
            regions = produce_regions(pysam_file, args.region_size)
        file_paths = produce_partfile_paths(args.input, regions, args.work_dir)
        task_graph = TaskGraph()
        region_tasks = []
        for index, (region, file_path) in enumerate(zip(regions, file_paths)):
            region_tasks.append(task_graph.create_task(
                f"part-{index}",
                annotate,
                [args, grr.definition,
                 ref_genome_id, file_path, region, True],
                []))

        task_graph.create_task(
            "combine",
            combine,
            [args, file_paths, output],
            region_tasks)

        if not os.path.exists(args.work_dir):
            os.mkdir(args.work_dir)
        args.task_status_dir = os.path.join(args.work_dir, "tasks-status")
        args.log_dir = os.path.join(args.work_dir, ".tasks-log")

        TaskGraphCli.process_graph(task_graph, **vars(args))
    else:
        annotate(args, grr.definition,
                 ref_genome_id, output, output.endswith(".gz"))


if __name__ == "__main__":
    cli(sys.argv[1:])
