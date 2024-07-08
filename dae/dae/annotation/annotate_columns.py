from __future__ import annotations

import argparse
import gzip
import logging
import os
import sys
from collections.abc import Generator, Iterable
from contextlib import closing
from pathlib import Path
from typing import Any

from pysam import TabixFile, tabix_index

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotate_utils import (
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
)
from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.annotation.record_to_annotatable import (
    RecordToAnnotable,
    RecordToCNVAllele,
    RecordToPosition,
    RecordToRegion,
    RecordToVcfAllele,
    add_record_to_annotable_arguments,
    build_record_to_annotatable,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename

logger = logging.getLogger("annotate_columns")


def read_input(
    args: Any, region: tuple = (),
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
    text_file = open(args.input, "rt")  # noqa: SIM115
    header = text_file.readline().strip("\r\n").split(args.input_separator)
    return text_file, text_file, header


def produce_tabix_index(
    filepath: str, args: Any, header: list[str],
    ref_genome: ReferenceGenome | None,
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
        raise TypeError(
            "Could not generate tabix index: record"
            f" {type(record_to_annotatable)} is of unsupported type.")
    tabix_index(filepath,
                seq_col=seq_col,
                start_col=start_col,
                end_col=end_col,
                line_skip=line_skip,
                force=True)


def combine(
    args: Any,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict | None,
    ref_genome_id: str | None,
    partfile_paths: list[str], out_file_path: str,
) -> None:
    """Combine annotated region parts into a single VCF file."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=args.allow_repeated_attributes,
        work_dir=Path(args.work_dir),
    )
    if ref_genome_id is not None:
        genome = build_reference_genome_from_resource(
            grr.get_resource(ref_genome_id))
    else:
        genome = None
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
    produce_tabix_index(out_file_path, args, hcs, genome)


class AnnotateColumnsTool(AnnotationTool):
    """Annotation tool for TSV-style text files."""

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate columns",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "input", default="-", nargs="?",
            help="the input column file")
        parser.add_argument(
            "-r", "--region-size", default=300_000_000,
            type=int, help="region size to parallelize by")
        parser.add_argument(
            "-w", "--work-dir",
            help="Directory to store intermediate output files in",
            default="annotate_columns_output")
        parser.add_argument(
            "-o", "--output",
            help="Filename of the output result",
            default=None)
        parser.add_argument(
            "-in_sep", "--input-separator", default="\t",
            help="The column separator in the input")
        parser.add_argument(
            "-out_sep", "--output-separator", default="\t",
            help="The column separator in the output")
        parser.add_argument(
            "--reannotate", default=None,
            help="Old pipeline config to reannotate over")
        parser.add_argument(
            "--batch-mode", default=False,
            action="store_true",
        )

        CLIAnnotationContext.add_context_arguments(parser)
        add_record_to_annotable_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    @staticmethod
    def annotate(
        args: argparse.Namespace,
        pipeline_config: RawAnnotatorsConfig,
        grr_definition: dict | None,
        ref_genome_id: str | None,
        out_file_path: str,
        region: tuple = (),
        compress_output: bool = False,  # noqa: FBT001 FBT002
    ) -> None:
        """Annotate a variants file with a given pipeline configuration."""
        # pylint: disable=too-many-locals,too-many-branches
        # TODO Insisting on having the pipeline config passed in args
        # prevents the finding of a default annotation config. Consider fixing

        pipeline_config_old = None
        if args.reannotate:
            pipeline_config_old = Path(args.reannotate).read_text()

        pipeline = AnnotateColumnsTool._produce_annotation_pipeline(
            pipeline_config, pipeline_config_old, grr_definition,
            allow_repeated_attributes=args.allow_repeated_attributes,
            work_dir=Path(args.work_dir),
        )
        grr = pipeline.repository
        ref_genome = None
        if ref_genome_id:
            res = grr.find_resource(ref_genome_id)
            if res is not None:
                ref_genome = build_reference_genome_from_resource(res).open()

        in_file, line_iterator, header_columns = read_input(args, region)
        record_to_annotatable = build_record_to_annotatable(
            vars(args), set(header_columns), ref_genome=ref_genome)

        annotation_columns = [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal]

        if compress_output:
            out_file = gzip.open(out_file_path, "wt")
        else:
            out_file = open(out_file_path, "wt")  # noqa: SIM115

        if region is None or len(region) == 0:
            batch_work_dir = None
        else:
            chrom = region[0]
            pos_beg = region[1] if len(region) > 1 else "_"
            pos_end = region[2] if len(region) > 2 else "_"
            batch_work_dir = f"{chrom}_{pos_beg}_{pos_end}"

        pipeline.open()
        with pipeline, in_file, out_file:
            if isinstance(pipeline, ReannotationPipeline):
                old_annotation_columns = {
                    attr.name
                    for attr in pipeline.pipeline_old.get_attributes()
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
            if args.batch_mode:
                values = AnnotateColumnsTool.batch_annotate(
                    args, pipeline, line_iterator,
                    header_columns,
                    record_to_annotatable,
                    batch_work_dir=batch_work_dir,
                )
            else:
                values = AnnotateColumnsTool.single_annotate(
                    args, pipeline, line_iterator,
                    header_columns,
                    record_to_annotatable,
                )
            for val in values:
                out_file.write(args.output_separator.join(val) + "\n")

    @staticmethod
    def batch_annotate(
        args: argparse.Namespace,
        pipeline: AnnotationPipeline,
        line_iterator: Iterable,
        header_columns: list[str],
        record_to_annotatable: RecordToAnnotable,
        batch_work_dir: str | None = None,
    ) -> Generator[list[str], None, None]:
        """Annotate given lines as a batch."""
        errors = []
        annotation_columns = [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal]

        records = []
        annotatables: list[Annotatable | None] = []
        for lnum, line in enumerate(line_iterator):
            try:
                columns = line.strip("\n\r").split(args.input_separator)
                record = dict(zip(header_columns, columns, strict=True))
                records.append(record)

                annotatables.append(record_to_annotatable.build(record))
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(
                    "unexpected input data format at line %s: %s",
                    lnum, line)
                errors.append((lnum, line, str(ex)))
        try:
            if isinstance(pipeline, ReannotationPipeline):
                annotations = pipeline.batch_annotate(
                    annotatables, records,
                    batch_work_dir=batch_work_dir,
                )
            else:
                annotations = pipeline.batch_annotate(
                    annotatables,
                    batch_work_dir=batch_work_dir,
                )
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception("Error during batch annotation")
            errors.append((-1, -1, str(ex)))

        for record, annotation in zip(records, annotations, strict=True):
            for col in annotation_columns:
                record[col] = annotation[col]
            yield list(map(str, record.values()))

        if len(errors) > 0:
            logger.error("there were errors during the import")
            for lnum, line, error in errors:
                logger.error("line %s: %s", lnum, line)
                logger.error("\t%s", error)

    @staticmethod
    def single_annotate(
        args: argparse.Namespace,
        pipeline: AnnotationPipeline,
        line_iterator: Iterable,
        header_columns: list[str],
        record_to_annotatable: RecordToAnnotable,
    ) -> Generator[list[str], None, None]:
        """Annotate given lines one by one."""
        errors = []
        annotation_columns = [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal]

        for lnum, line in enumerate(line_iterator):
            try:
                columns = line.strip("\n\r").split(args.input_separator)
                record = dict(zip(header_columns, columns, strict=True))
                if isinstance(pipeline, ReannotationPipeline):
                    for col in pipeline.attributes_deleted:
                        del record[col]
                    annotation = pipeline.annotate(
                        record_to_annotatable.build(record), record,
                    )
                else:
                    annotation = pipeline.annotate(
                        record_to_annotatable.build(record),
                    )

                for col in annotation_columns:
                    record[col] = annotation[col]
                result = list(map(str, record.values()))
                yield result
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(
                    "unexpected input data format at line %s: %s",
                    lnum, line)
                errors.append((lnum, line, str(ex)))

        if len(errors) > 0:
            logger.error("there were errors during the import")
            for lnum, line, error in errors:
                logger.error("line %s: %s", lnum, line)
                logger.error("\t%s", error)

    def work(self) -> None:
        if self.args.output:
            output = self.args.output
        else:
            input_name = self.args.input.rstrip(".gz")
            if "." in input_name:
                idx = input_name.find(".")
                output = f"{input_name[:idx]}_annotated{input_name[idx:]}"
            else:
                output = f"{input_name}_annotated"

        ref_genome = self.context.get_reference_genome()
        ref_genome_id = ref_genome.resource_id \
            if ref_genome is not None else None

        if tabix_index_filename(self.args.input):
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(
                self.args.input, regions, self.args.work_dir)

            region_tasks = []
            for index, (region, path) in enumerate(
                zip(regions, file_paths, strict=True),
            ):
                region_tasks.append(self.task_graph.create_task(
                    f"part-{index}",
                    AnnotateColumnsTool.annotate,
                    [self.args, self.pipeline.raw,
                     self.grr.definition,
                     ref_genome_id, path, region, True],
                    []))

            self.task_graph.create_task(
                "combine",
                combine,
                [self.args, self.pipeline.raw, self.grr.definition,
                 ref_genome_id, file_paths, output],
                region_tasks)
        else:
            self.task_graph.create_task(
                "annotate_all",
                AnnotateColumnsTool.annotate,
                [self.args, self.pipeline.raw, self.grr.definition,
                 ref_genome_id, output,
                 (), output.endswith(".gz")],
                [])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateColumnsTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
