from __future__ import annotations
import os
import logging
import sys
import gzip
import argparse
from contextlib import closing
from typing import Optional

from pysam import TabixFile

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.annotation.record_to_annotatable import \
    add_record_to_annotable_arguments
from dae.annotation.annotate_vcf import produce_regions, produce_partfile_paths
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.cached_repository import cache_resources
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
    CLIAnnotationContext.add_context_arguments(parser)
    add_record_to_annotable_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def _handle_output(outfile: str):
    # if outfile == "-":
    #     return sys.stdout
    if outfile.endswith(".gz"):
        # pylint: disable=consider-using-with
        return gzip.open(outfile, "wt")
    # pylint: disable=consider-using-with
    return open(outfile, "wt")


def annotate(args, region, out_file_path):
    CLIAnnotationContext.register(args)
    context = get_genomic_context()
    grr = CLIAnnotationContext.get_genomic_resources_repository(context)
    pipeline = CLIAnnotationContext.get_pipeline(context)
    errors = []
    # TODO Is getting the context and pipeline in this way acceptable?

    # cache pipeline
    resources: set[str] = set()
    for annotator in pipeline.annotators:
        resources = resources | annotator.resources
    cache_resources(grr, resources)

    with gzip.open(args.input, "rt") as in_file_raw:
        hcs = in_file_raw.readline().strip("\r\n").split(args.input_separator)
    record_to_annotatable = build_record_to_annotatable(
        vars(args), set(hcs), context=context)
    annotation_attributes = pipeline.annotation_schema.public_fields

    pipeline.open()
    print(out_file_path)
    in_file = TabixFile(args.input)
    with _handle_output(out_file_path) as out_file:
        print(*(hcs + annotation_attributes),
              sep=args.output_separator, file=out_file)
        for lnum, line in enumerate(in_file.fetch(*region)):
            try:
                columns = line.strip("\n\r").split(args.input_separator)
                record = dict(zip(hcs, columns))
                annotation = pipeline.annotate(
                    record_to_annotatable.build(record)
                )
                print(*(columns + [
                    str(annotation[attrib])
                    for attrib in annotation_attributes]),
                    sep=args.output_separator, file=out_file)
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


def combine(args, partfile_paths, out_file_path):
    """Combine annotated region parts into a single VCF file."""
    CLIAnnotationContext.register(args)
    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)
    annotation_attributes = pipeline.annotation_schema.public_fields
    with _handle_output(out_file_path) as out_file:
        with gzip.open(args.input, "rt") as in_file_raw:
            hcs = in_file_raw.readline().strip("\r\n").split(
                args.input_separator)
            print(*(hcs + annotation_attributes),
                  sep=args.output_separator, file=out_file)
            for partfile_path in partfile_paths:
                with gzip.open(partfile_path, "rt") as partfile:
                    out_file.write(partfile.read())
    # TODO How to write tabix index for output file? Is it possible?
    # What if it has N lines skipped, other custom fields?
    for partfile_path in partfile_paths:
        os.remove(partfile_path)


def cli(raw_args: Optional[list[str]] = None) -> None:
    """Run command line interface for annotate columns."""
    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    # TODO Get context here and from it the resource id for the
    # reference genome and then pass it to annotate, then get it from grr

    if args.output:
        output = args.output
    else:
        filename, extension = os.path.basename(args.input).split(".")
        output = f"{filename}_annotated.{extension}"

    if not os.path.exists(args.work_dir):
        os.mkdir(args.work_dir)

    def run_parallelized():
        with closing(TabixFile(args.input)) as pysam_file:
            regions = produce_regions(pysam_file, args.region_size)
        file_paths = produce_partfile_paths(args.input, regions, args.work_dir)
        task_graph = TaskGraph()
        region_tasks = []
        for index, (region, file_path) in enumerate(zip(regions, file_paths)):
            region_tasks.append(task_graph.create_task(
                f"part-{index}",
                annotate,
                [args, region, file_path],  # FIXME part filepaths have .vcf
                []
            ))

        task_graph.create_task(
            "combine",
            combine,
            [args, file_paths, output],
            region_tasks
        )

        args.task_status_dir = os.path.join(args.work_dir, "tasks-status")
        args.log_dir = os.path.join(args.work_dir, "tasks-log")

        TaskGraphCli.process_graph(task_graph, **vars(args))

    def run_sequentially():
        print("Tabixless annotation currently not supported. WIP")
        return 0

    if tabix_index_filename(args.input):
        run_parallelized()
    else:
        # TODO Make it work for non-tabixed input
        run_sequentially()


if __name__ == "__main__":
    cli(sys.argv[1:])
