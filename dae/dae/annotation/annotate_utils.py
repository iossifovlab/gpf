import argparse
import gzip
import logging
import os
import sys
from abc import abstractmethod
from pathlib import Path
from typing import Any

from pysam import TabixFile, tabix_index

from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
)
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
    load_pipeline_from_yaml,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    FullReannotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.format_handlers import AbstractFormat
from dae.annotation.genomic_context import (
    CLIAnnotationContextProvider,
    get_context_pipeline,
)
from dae.annotation.record_to_annotatable import (
    DaeAlleleRecordToAnnotatable,
    RecordToCNVAllele,
    RecordToPosition,
    RecordToRegion,
    RecordToVcfAllele,
    build_record_to_annotatable,
)
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.genomic_context import (
    context_providers_init,
    get_genomic_context,
    register_context_provider,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.regions import (
    Region,
    get_chromosome_length_tabix,
    split_into_regions,
)
from dae.utils.verbosity_configuration import VerbosityConfiguration

PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}"

logger = logging.getLogger("annotate_utils")


def produce_regions(
    pysam_file: TabixFile, region_size: int,
) -> list[Region]:
    """Given a region size, produce contig regions to annotate by."""
    contig_lengths: dict[str, int] = {}
    for contig in map(str, pysam_file.contigs):
        length = get_chromosome_length_tabix(pysam_file, contig)
        if length is None:
            raise ValueError(f"unable to find length of contig '{contig}'")
        contig_lengths[contig] = length

    regions: list[Region] = []
    for contig, length in contig_lengths.items():
        regions.extend(split_into_regions(contig, length, region_size))
    return regions


def produce_partfile_paths(
    input_file_path: str, regions: list[Region], work_dir: str,
) -> list[str]:
    """Produce a list of file paths for output region part files."""
    filenames = []
    for region in regions:
        pos_beg = region.start if region.start is not None else "_"
        pos_end = region.stop if region.stop is not None else "_"
        filenames.append(os.path.join(work_dir, PART_FILENAME.format(
            in_file=os.path.basename(input_file_path),
            chrom=region.chrom, pos_beg=pos_beg, pos_end=pos_end,
        )))
    return filenames


def _read_header(filepath: str, separator: str = "\t") -> list[str]:
    """Extract header from columns file."""
    if filepath.endswith(".gz"):
        file = gzip.open(filepath, "rt")  # noqa: SIM115
    else:
        file = open(filepath, "r")  # noqa: SIM115
    with file:
        header = file.readline()
    return [c.strip() for c in header.split(separator)]


def produce_tabix_index(filepath: str, args: Any = None) -> None:
    """Produce a tabix index file for the given variants file."""
    filepath = filepath.rstrip(".gz")

    header = _read_header(filepath)
    line_skip = 0 if header[0].startswith("#") else 1
    header = [c.strip("#") for c in header]
    record_to_annotatable = build_record_to_annotatable(
        vars(args) if args is not None else {},
        set(header),
    )
    if isinstance(record_to_annotatable, (RecordToRegion,
                                          RecordToCNVAllele)):
        seq_col = header.index(record_to_annotatable.chrom_col)
        start_col = header.index(record_to_annotatable.pos_beg_col)
        end_col = header.index(record_to_annotatable.pos_end_col)
    elif isinstance(record_to_annotatable, RecordToVcfAllele):
        seq_col = header.index(record_to_annotatable.chrom_col)
        start_col = header.index(record_to_annotatable.pos_col)
        end_col = start_col
    elif isinstance(
            record_to_annotatable,
            (RecordToPosition, DaeAlleleRecordToAnnotatable)):
        seq_col = header.index(record_to_annotatable.chrom_column)
        start_col = header.index(record_to_annotatable.pos_column)
        end_col = start_col
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


class AnnotationTool:
    """Base class for annotation tools. Format-agnostic."""

    def __init__(
        self,
        raw_args: list[str] | None = None,
    ) -> None:
        if not raw_args:
            raw_args = sys.argv[1:]

        parser = self.get_argument_parser()

        self.args = parser.parse_args(raw_args)
        VerbosityConfiguration.set(self.args)

        register_context_provider(CLIAnnotationContextProvider())
        context_providers_init(**vars(self.args))

        registered_context = get_genomic_context()

        # Maybe add a method to build a pipeline from a genomic context
        # the pipeline arguments are registered as a context above, where
        # the pipeline is also written into the context, only to be accessed
        # 3 lines down
        pipeline = get_context_pipeline(registered_context)
        if pipeline is None:
            raise ValueError(
                "no valid annotation pipeline configured")
        self.pipeline = pipeline
        self.context = self.pipeline.build_pipeline_genomic_context()
        grr = self.context.get_genomic_resources_repository()
        if grr is None:
            raise ValueError("no valid GRR configured")
        self.grr = grr

        self.task_graph = TaskGraph()

    def setup_work_dir(self) -> None:
        if not os.path.exists(self.args.work_dir):
            os.mkdir(self.args.work_dir)
        self.args.task_status_dir = os.path.join(
            self.args.work_dir, ".task-status")
        self.args.task_log_dir = os.path.join(self.args.work_dir, ".task-log")

    @staticmethod
    def produce_annotation_pipeline(
        pipeline_config: RawAnnotatorsConfig,
        pipeline_config_old: str | None,
        grr_definition: dict | None,
        *,
        allow_repeated_attributes: bool,
        work_dir: Path | None = None,
        full_reannotation: bool = False,
    ) -> AnnotationPipeline:
        """Produce an annotation or reannotation pipeline."""
        grr = build_genomic_resource_repository(definition=grr_definition)
        pipeline = build_annotation_pipeline(
            pipeline_config, grr,
            allow_repeated_attributes=allow_repeated_attributes,
            work_dir=work_dir,
        )
        if pipeline_config_old is not None:
            pipeline_old = load_pipeline_from_yaml(pipeline_config_old, grr)
            pipeline = ReannotationPipeline(pipeline, pipeline_old) \
                if not full_reannotation \
                else FullReannotationPipeline(pipeline, pipeline_old)

        return pipeline

    @staticmethod
    def get_task_dir(region: Region | None) -> str:
        """Get dir for batch annotation."""
        if region is None:
            return "batch_work_dir"
        chrom = region.chrom
        pos_beg = region.start if region.start is not None else "_"
        pos_end = region.stop if region.stop is not None else "_"
        return f"{chrom}_{pos_beg}_{pos_end}"

    @staticmethod
    def annotate(
        handler: AbstractFormat,
        batch_mode: bool,  # noqa: FBT001
    ) -> None:
        """Run annotation."""
        handler.open()
        if batch_mode:
            handler.process_batched()
        else:
            handler.process()
        handler.close()

    @abstractmethod
    def get_argument_parser(self) -> argparse.ArgumentParser:
        pass

    def prepare_for_annotation(self) -> None:
        """Perform operations required for annotation."""
        return

    def add_tasks_to_graph(self) -> None:
        """Add tasks to annotation tool task graph."""
        return

    def run(self) -> None:
        """Construct annotation tasks and execute task graph."""
        # Is this too eager? What if a reannotation pipeline is created
        # inside work() and the only caching that must be done is far smaller
        # than the entire new annotation config suggests?
        resource_ids: set[str] = {
            res.resource_id
            for annotator in self.pipeline.annotators
            for res in annotator.resources
        }
        cache_resources(self.grr, resource_ids)

        self.setup_work_dir()

        self.prepare_for_annotation()

        self.add_tasks_to_graph()

        if len(self.task_graph.tasks) > 0:
            if hasattr(self.args, "input"):
                self.task_graph.input_files.append(self.args.input)
            if hasattr(self.args, "pipeline"):
                self.task_graph.input_files.append(self.args.pipeline)
            if hasattr(self.args, "reannotate") and self.args.reannotate:
                self.task_graph.input_files.append(self.args.reannotate)

            TaskGraphCli.process_graph(self.task_graph, **vars(self.args))
