import argparse
import os
import sys
from abc import abstractmethod
from typing import Optional
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline, AnnotatorInfo, ReannotationPipeline
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.utils.regions import get_chromosome_length_tabix
from pysam import TabixFile


PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.gz"


def produce_regions(
    pysam_file: TabixFile, region_size: int
) -> list[tuple[str, int, int]]:
    """Given a region size, produce contig regions to annotate by."""
    contig_lengths = {}
    for contig in map(str, pysam_file.contigs):
        contig_lengths[contig] = get_chromosome_length_tabix(pysam_file, contig)
    return [
        (contig, start, start + region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, region_size)
    ]


def produce_partfile_paths(
    input_file_path: str, regions: list[tuple[str, int, int]], work_dir: str
) -> list[str]:
    """Produce a list of file paths for output region part files."""
    filenames = []
    for region in regions:
        pos_beg = region[1] if len(region) > 1 else "_"
        pos_end = region[2] if len(region) > 2 else "_"
        filenames.append(os.path.join(work_dir, PART_FILENAME.format(
            in_file=os.path.basename(input_file_path),
            chrom=region[0], pos_beg=pos_beg, pos_end=pos_end
        )))
    return filenames


def cache_pipeline(
    grr: GenomicResourceRepo, pipeline: AnnotationPipeline
) -> None:
    """Cache the resources used by the pipeline."""
    resource_ids: set[str] = set()
    for annotator in pipeline.annotators:
        resource_ids = resource_ids | \
            set(res.resource_id for res in annotator.resources)
    cache_resources(grr, resource_ids)


def build_pipeline(
    pipeline_config: list[AnnotatorInfo],
    allow_repeated_attributes: bool,
    grr: GenomicResourceRepo,
    reannotate: Optional[str] = None,
) -> tuple[AnnotationPipeline, Optional[AnnotationPipeline]]:
    """Build an annotation pipeline from a pipeline config."""
    pipeline = build_annotation_pipeline(
        pipeline_config=pipeline_config,
        grr_repository=grr,
        allow_repeated_attributes=allow_repeated_attributes)
    pipeline_old = None
    if reannotate:
        pipeline_old = build_annotation_pipeline(
            pipeline_config_file=reannotate,
            grr_repository=grr,
            allow_repeated_attributes=allow_repeated_attributes  # FIXME Is this correct? How do we know whether the old pipeline was made with this as true or false?
        )
        pipeline_new = pipeline
        pipeline = ReannotationPipeline(pipeline_new, pipeline_old)

    return pipeline, pipeline_old


class AnnotationTool:
    def __init__(self, raw_args: Optional[list[str]] = None, gpf_instance: Optional[GPFInstance] = None) -> None:
        if not raw_args:
            raw_args = sys.argv[1:]

        parser = self.get_argument_parser()
        self.args = parser.parse_args(raw_args)
        VerbosityConfiguration.set(self.args)
        CLIAnnotationContext.register(self.args)

        self.gpf_instance = gpf_instance
        self.context = get_genomic_context()
        self.pipeline = CLIAnnotationContext.get_pipeline(self.context)
        self.grr = CLIAnnotationContext.get_genomic_resources_repository(self.context)
        if self.grr is None:
            raise ValueError("No valid GRR configured. Aborting.")

        self.task_graph = TaskGraph()
        if not os.path.exists(self.args.work_dir):
            os.mkdir(self.args.work_dir)
        self.args.task_status_dir = os.path.join(self.args.work_dir, ".task-status")
        self.args.log_dir = os.path.join(self.args.work_dir, ".task-log")

    @abstractmethod
    def get_argument_parser() -> argparse.ArgumentParser:
        pass

    @abstractmethod
    def work(self) -> None:
        pass

    def run(self) -> None:
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