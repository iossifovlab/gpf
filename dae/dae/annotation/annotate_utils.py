import argparse
import os
import pathlib
import sys
from abc import abstractmethod
from typing import Optional

from pysam import TabixFile

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.implementations.annotation_pipeline_impl import (
    AnnotationPipelineImplementation,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.regions import get_chromosome_length_tabix
from dae.utils.verbosity_configuration import VerbosityConfiguration

PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.gz"


def produce_regions(
    pysam_file: TabixFile, region_size: int,
) -> list[tuple[str, int, int]]:
    """Given a region size, produce contig regions to annotate by."""
    contig_lengths: dict[str, int] = {}
    for contig in map(str, pysam_file.contigs):
        length = get_chromosome_length_tabix(pysam_file, contig)
        if length is None:
            raise ValueError(f"unable to find length of contig '{contig}'")
        contig_lengths[contig] = length
    return [
        (contig, start, start + region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, region_size)
    ]


def produce_partfile_paths(
    input_file_path: str, regions: list[tuple[str, int, int]], work_dir: str,
) -> list[str]:
    """Produce a list of file paths for output region part files."""
    filenames = []
    for region in regions:
        pos_beg = region[1] if len(region) > 1 else "_"
        pos_end = region[2] if len(region) > 2 else "_"
        filenames.append(os.path.join(work_dir, PART_FILENAME.format(
            in_file=os.path.basename(input_file_path),
            chrom=region[0], pos_beg=pos_beg, pos_end=pos_end,
        )))
    return filenames


def cache_pipeline(
    grr: GenomicResourceRepo, pipeline: AnnotationPipeline,
) -> None:
    """Cache the resources used by the pipeline."""
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
        raw_args: Optional[list[str]] = None,
        gpf_instance: Optional[GPFInstance] = None,
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
        if not os.path.exists(self.args.work_dir):
            os.mkdir(self.args.work_dir)
        self.args.task_status_dir = os.path.join(
            self.args.work_dir, ".task-status")
        self.args.log_dir = os.path.join(self.args.work_dir, ".task-log")

    @staticmethod
    def _produce_annotation_pipeline(
        pipeline_config: str,
        pipeline_config_old: Optional[str],
        grr_definition: Optional[dict],
        *,
        allow_repeated_attributes: bool,
    ) -> AnnotationPipeline:
        grr = build_genomic_resource_repository(definition=grr_definition)
        pipeline = build_annotation_pipeline(
            pipeline_config_str=pipeline_config,
            grr_repository=grr,
            allow_repeated_attributes=allow_repeated_attributes,
        )
        if pipeline_config_old is not None:
            pipeline_old = build_annotation_pipeline(
                pipeline_config_str=pipeline_config_old,
                grr_repository=grr,
            )
            pipeline = ReannotationPipeline(pipeline, pipeline_old)
        return pipeline

    def _get_pipeline_config(self) -> str:
        if (pipeline_path := pathlib.Path(self.args.pipeline)).exists():
            return pipeline_path.read_text()
        if (pipeline_res := self.grr.find_resource(self.args.pipeline)):
            return AnnotationPipelineImplementation(pipeline_res).raw
        raise ValueError

    @abstractmethod
    def get_argument_parser(self) -> argparse.ArgumentParser:
        pass

    @abstractmethod
    def work(self) -> None:
        pass

    def run(self) -> None:
        """Construct annotation tasks and process them."""
        # FIXME Is this too eager? What if a reannotation pipeline is created
        # inside work() and the only caching that must be done is far smaller
        # than the entire new annotation config suggests?
        cache_pipeline(self.grr, self.pipeline)

        self.task_graph.input_files.append(self.args.input)
        self.task_graph.input_files.append(self.args.pipeline)
        if hasattr(self.args, "reannotate") and self.args.reannotate:
            self.task_graph.input_files.append(self.args.reannotate)

        self.work()

        TaskGraphCli.process_graph(self.task_graph, **vars(self.args))
