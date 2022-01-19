import argparse
import logging
from typing import Optional, cast
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.gene_models_resource import \
    load_gene_models_from_resource
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome_resource import \
    open_reference_genome_from_resource
from dae.genomic_resources.genomic_context import get_genomic_context

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo

logger = logging.getLogger(__name__)


class Context:

    @staticmethod
    def add_context_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            '-grr', '--grr-file-name', default=None,
            help="The GRR configuration file. If the argument is absent, "
            "the a GRR repository from the current genomic context "
            "(i.e. gpf_instance) will be used or, if that fails, the "
            "default GRR configuration will be used.")
        parser.add_argument(
            '-ref', '--reference-genome-resource-id', default=None,
            help="The resource id for the reference genome. If the argument "
                 "is absent the reference genome from the current genomic "
                 "context will be used.")
        parser.add_argument(
            '-genes', '--gene-models-resource-id', default=None,
            help="The resource is of the gene models resoruce. If the argument"
                 " is absent the gene models from the current genomic "
                 "context will be used.")

    def __init__(self, args):
        self.args = args
        self._grr: Optional[GenomicResourceRepo] = None
        self._ref_genome: Optional[ReferenceGenome] = None
        self._gene_models: Optional[GeneModels] = None
        self._pipeline: Optional[AnnotationPipeline] = None

    def get_grr(self) -> GenomicResourceRepo:
        if self._grr is None:
            if self.args.grr_file_name:
                logger.info("Using the GRR consigured in the file "
                            f"{self.args.grr_file_name} as requested on the "
                            "command line.")
                self._grr = build_genomic_resource_repository(
                    file_name=self.args.grr_file_name)
            else:
                gc = get_genomic_context()
                self._grr = gc.get_genomic_resource_repository()
                if self._grr is None:
                    logger.info("Using the defualt configured GRR.")
                    self._grr = build_genomic_resource_repository()
                else:
                    logger.info("Using the GRR from the genomic context.")

        return self._grr

    def get_pipeline(self) -> AnnotationPipeline:
        if self._pipeline is None:
            if self.args.pipeline == "context":
                logger.info("Using the annotation pipeline from "
                            "the GPF instance.")
                gc = get_genomic_context()
                o = gc.get_context_object("annotation_pipeline")
                if o is None:
                    raise Exception("No annotation pipeline could be found "
                                    "in the genomic context.")
                if not isinstance(o, AnnotationPipeline):
                    raise Exception("The annotation pipeline from the genomic "
                                    " context is not an AnnotationPipeline")
                self._pipeline = cast(AnnotationPipeline, o)
            else:
                logger.info("Using the annotation pipeline from "
                            f"the file {self.args.pipeline}.")
                self._pipeline = build_annotation_pipeline(
                    pipeline_config_file=self.args.pipeline,
                    grr_repository=self.get_grr())
        return self._pipeline

    def get_reference_genome(self) -> ReferenceGenome:
        if self._ref_genome is None:
            if self.args.reference_genome_resource_id is not None:
                logger.info("Using the reference genome from resoruce"
                            f" {self.args.reference_genome_resource_id} "
                            "provided on the command line.")
                resource = self.get_grr().get_resource(
                    self.args.reference_genome_resource_id)

                self._ref_genome = open_reference_genome_from_resource(
                    resource)
            else:
                logger.info("Using the reference genome from the context.")
                self._ref_genome = get_genomic_context().get_reference_genome()

        if self._ref_genome is None:
            raise Exception("No reference genome could be found!")
        return self._ref_genome

    def get_gene_models(self) -> GeneModels:
        if self._gene_models is None:
            if self.args.gene_models_resource_id is not None:
                logger.info("Using the gene models from resoruce "
                            f"{self.args.gene_models_resource_id} "
                            "provided on the command line.")
                resource = self.get_grr().get_resource(
                    self.args.gene_models_resource_id)

                self._gene_models = load_gene_models_from_resource(resource)
            else:
                logger.info("Using the gene models from the GPF instance.")
                self._gene_models = get_genomic_context().get_gene_models()
        if self._gene_models is None:
            raise Exception("No gene models could be found!")
        return self._gene_models
