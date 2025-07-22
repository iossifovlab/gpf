import argparse
import gzip
import logging
import os
import sys
from abc import abstractmethod
from typing import Any

from pysam import TabixFile, tabix_index

from dae.annotation.annotation_pipeline import AnnotationPipeline
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
    GenomicContext,
    context_providers_init,
    get_genomic_context,
    register_context_provider,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.regions import (
    Region,
    get_chromosome_length_tabix,
    split_into_regions,
)

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


def produce_tabix_index(filepath: str, args: dict | None = None) -> None:
    """Produce a tabix index file for the given variants file."""
    header = _read_header(filepath)
    line_skip = 0 if header[0].startswith("#") else 1
    header = [c.strip("#") for c in header]
    record_to_annotatable = build_record_to_annotatable(
        args if args is not None else {},
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


def stringify(value: Any, *, vcf: bool = False) -> str:
    """Format the value to a string for human-readable output."""
    if value is None:
        return "." if vcf else ""
    if isinstance(value, float):
        return f"{value:.3g}"
    if isinstance(value, bool):
        return "yes" if value else ""
    return str(value)


def setup_work_dir_and_task_dirs(args: dict) -> None:
    if not os.path.exists(args["work_dir"]):
        os.mkdir(args["work_dir"])
    args["task_status_dir"] = os.path.join(args["work_dir"], ".task-status")
    args["task_log_dir"] = os.path.join(args["work_dir"], ".task-log")


def setup_context(args: dict) -> None:
    register_context_provider(CLIAnnotationContextProvider())
    context_providers_init(**args)


def get_stuff_from_context() -> tuple[AnnotationPipeline,
                                      GenomicContext,
                                      GenomicResourceRepo]:
    registered_context = get_genomic_context()
    # Maybe add a method to build a pipeline from a genomic context
    # the pipeline arguments are registered as a context above, where
    # the pipeline is also written into the context, only to be accessed
    # 3 lines down
    pipeline = get_context_pipeline(registered_context)
    if pipeline is None:
        raise ValueError(
            "no valid annotation pipeline configured")
    context = pipeline.build_pipeline_genomic_context()
    grr = context.get_genomic_resources_repository()
    if grr is None:
        raise ValueError("no valid GRR configured")
    return pipeline, context, grr


def add_input_files_to_task_graph(args: dict, task_graph: TaskGraph) -> None:
    if "input" in args:
        task_graph.input_files.append(args["input"])
    if "pipeline" in args:
        task_graph.input_files.append(args["pipeline"])
    if args.get("reannotate"):
        task_graph.input_files.append(args["reannotate"])


def cache_pipeline_resources(
    grr: GenomicResourceRepo,
    pipeline: AnnotationPipeline,
) -> None:
    resource_ids: set[str] = {
        res.resource_id
        for annotator in pipeline.annotators
        for res in annotator.resources
    }
    cache_resources(grr, resource_ids)


class AnnotationTool:
    """Base class for annotation tools. Format-agnostic."""

    def __init__(
        self,
        raw_args: list[str] | None = None,
    ) -> None:
        if not raw_args:
            raw_args = sys.argv[1:]
        self.args = vars(self.get_argument_parser().parse_args(raw_args))
        setup_context(self.args)
        self.pipeline, self.context, self.grr = get_stuff_from_context()

    @abstractmethod
    def get_argument_parser(self) -> argparse.ArgumentParser:
        pass

    def prepare_for_annotation(self) -> None:
        """Perform operations required for annotation."""
        return

    def add_tasks_to_graph(
        self, task_graph: TaskGraph,  # noqa: ARG002
    ) -> None:
        """Add tasks to annotation tool task graph."""
        return

    def run(self) -> None:
        """Construct annotation tasks and execute task graph."""
        # Is this too eager? What if a reannotation pipeline is created
        # inside work() and the only caching that must be done is far smaller
        # than the entire new annotation config suggests?
        cache_pipeline_resources(self.grr, self.pipeline)

        setup_work_dir_and_task_dirs(self.args)

        self.prepare_for_annotation()

        task_graph = TaskGraph()
        self.add_tasks_to_graph(task_graph)

        if len(task_graph.tasks) > 0:
            add_input_files_to_task_graph(self.args, task_graph)

            TaskGraphCli.process_graph(task_graph, **self.args)
