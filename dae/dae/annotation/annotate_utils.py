import argparse
import os
import sys
from abc import abstractmethod
from pathlib import Path
from typing import Any

from pysam import TabixFile

from dae.annotation.annotation_config import RawAnnotatorsConfig
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
    load_pipeline_from_yaml,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    FullReannotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.regions import (
    Region,
    get_chromosome_length_tabix,
    split_into_regions,
)
from dae.utils.verbosity_configuration import VerbosityConfiguration

PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.gz"


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
    if isinstance(value, float):
        return f"{value:.3g}"
    if isinstance(value, bool):
        return "yes" if value else ""
    return str(value)


class AnnotationTool:
    """Base class for annotation tools. Format-agnostic."""

    def __init__(
        self,
        raw_args: list[str] | None = None,
        gpf_instance: GPFInstance | None = None,
    ) -> None:
        if not raw_args:
            raw_args = sys.argv[1:]

        parser = self.get_argument_parser()
        self.args = parser.parse_args(raw_args)
        VerbosityConfiguration.set(self.args)
        CLIAnnotationContext.register(self.args)

        self.gpf_instance = gpf_instance
        self.context = get_genomic_context()
        self.pipeline = CLIAnnotationContext.get_pipeline(self.context)
        grr = \
            CLIAnnotationContext.get_genomic_resources_repository(self.context)
        if grr is None:
            raise ValueError("No valid GRR configured. Aborting.")
        self.grr = grr

        self.task_graph = TaskGraph()

    def setup_work_dir(self) -> None:
        if not os.path.exists(self.args.work_dir):
            os.mkdir(self.args.work_dir)
        self.args.task_status_dir = os.path.join(
            self.args.work_dir, ".task-status")
        self.args.log_dir = os.path.join(self.args.work_dir, ".task-log")

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

    @abstractmethod
    def get_argument_parser(self) -> argparse.ArgumentParser:
        pass

    @abstractmethod
    def work(self) -> None:
        pass

    def run(self) -> None:
        """Construct annotation tasks and process them."""
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

        if hasattr(self.args, "input"):
            self.task_graph.input_files.append(self.args.input)
        if hasattr(self.args, "pipeline"):
            self.task_graph.input_files.append(self.args.pipeline)
        if hasattr(self.args, "reannotate") and self.args.reannotate:
            self.task_graph.input_files.append(self.args.reannotate)

        self.work()

        if len(self.task_graph.tasks) > 0:
            TaskGraphCli.process_graph(self.task_graph, **vars(self.args))
