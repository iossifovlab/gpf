import argparse
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
from pysam import TabixFile

from dae.annotation.annotation_genomic_context_cli import (
    get_context_pipeline,
)
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.genomic_resources.genomic_context_base import (
    GenomicContext,
)
from dae.genomic_resources.repository import GenomicResourceRepo
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


def stringify(value: Any, *, vcf: bool = False) -> str:
    """Format the value to a string for human-readable output."""
    if value is None:
        return "." if vcf else ""
    if isinstance(value, (float, np.floating)):
        return f"{value:.3g}"
    if isinstance(value, bool):
        return "yes" if value else ("." if vcf else "")
    if vcf is True and value == "":
        return "."
    return str(value)


def build_cli_genomic_context(
    cli_args: dict[str, Any],
) -> GenomicContext:
    """Helper method to collect necessary objects from the genomic context."""
    context_providers_init(**cli_args)
    return get_genomic_context()


def get_pipeline_from_context(context: GenomicContext) -> AnnotationPipeline:
    """Get the annotation pipeline from the genomic context."""
    pipeline = get_context_pipeline(context)
    if pipeline is None:
        raise ValueError("no valid annotation pipeline configured")
    return pipeline


def get_grr_from_context(context: GenomicContext) -> GenomicResourceRepo:
    """Get the genomic resource repository from the genomic context."""
    grr = context.get_genomic_resources_repository()
    if grr is None:
        raise ValueError("no valid GRR configured")
    return grr


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
    """Cache resources that the given pipeline will use."""
    resource_ids: set[str] = {
        res.resource_id
        for annotator in pipeline.annotators
        for res in annotator.resources
    }
    cache_resources(grr, resource_ids)


def handle_default_args(args: dict[str, Any]) -> dict[str, Any]:
    """Handle default arguments for annotation command line tools."""
    if not os.path.exists(args["input"]):
        raise ValueError(f"{args['input']} does not exist!")
    output = build_output_path(args["input"], args.get("output"))
    args["output"] = output

    if args.get("work_dir") is None:
        path = Path(args["output"])
        if path.suffix == ".gz":
            path = path.with_suffix("")
        path = path.with_suffix("")
        args["work_dir"] = str(f"{path}_work")

    if not os.path.exists(args["work_dir"]):
        os.mkdir(args["work_dir"])

    if args.get("task_status_dir") is None:
        args["task_status_dir"] = os.path.join(
            args["work_dir"], ".task-status")
    if args.get("task_log_dir") is None:
        args["task_log_dir"] = os.path.join(
            args["work_dir"], ".task-log")

    return args


def add_common_annotation_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to an annotation command line parser."""
    parser.add_argument(
        "input", default="-", nargs="?",
        help="the input column file")
    parser.add_argument(
        "--version", default=False,
        action="store_true", help="Show the GPF version and exit")
    parser.add_argument(
        "-r", "--region-size", default=300_000_000,
        type=int, help="region size to parallelize by; zero or negative "
        "values disable parallelization")
    parser.add_argument(
        "-w", "--work-dir",
        help="Directory to store intermediate output files in",
        default=None)
    parser.add_argument(
        "-o", "--output",
        help="Filename of the output result",
        default=None)
    parser.add_argument(
        "--reannotate", default=None,
        help="Old pipeline config to reannotate over")
    parser.add_argument(
        "--full-reannotation", "--fr",
        help="Ignore any previous annotation and run "
        " a full reannotation.",
        action="store_true",
    )
    parser.add_argument(
        "--keep-parts", "--keep-intermediate-files",
        help="Keep intermediate files after annotatio.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no-keep-parts", "--no-keep-intermediate-files",
        help="Remove intermediate files after annotatio.",
        dest="keep_parts",
        action="store_false",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,  # 0 = annotate iteratively, no batches
        help="Annotate in batches of",
    )

    context_providers_add_argparser_arguments(parser)
    TaskGraphCli.add_arguments(parser, default_task_status_dir=None)
    VerbosityConfiguration.set_arguments(parser)


def build_output_path(raw_input_path: str, output_path: str | None) -> str:
    """Build an output filepath for an annotation tool's output."""
    if output_path:
        return output_path.rstrip(".gz")
    # no output filename given, produce from input filename
    path = Path(raw_input_path.rstrip(".gz"))
    # backup suffixes
    suffixes = path.suffixes

    path = Path(path.name)
    # append '_annotated' to filename stem
    path = path.with_stem(f"{path.stem}_annotated")
    # restore suffixes and return
    if not suffixes:
        return str(path)
    return str(path.with_suffix(suffixes[-1]))
