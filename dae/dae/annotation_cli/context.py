import argparse
import sys
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AnnotationPipelineContext

from dae.annotation.effect_annotator import EffectAnnotatorAdapter
from dae.genomic_resources import build_genomic_resource_repository


def add_context_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        '-grr', '--grr-file-name', default=None,
        help="The GRR configuration file. If absent, "
        "the default GRR repository will be used. "
        "If equall equal to gpf_instance, will try get "
        "the GRR for the configured gpf instance.")
    parser.add_argument(
        '-gpf', '--gpf-instance-dir', default=None,
        help="The gpf instance to be used for as context.")
    parser.add_argument(
        '-ref', '--ref-genome-resource-id', default=None,
        help='The resource id for the referende genome.')
    parser.add_argument(
        '-genes', '--gene-models-resource-id', default=None,
        help="The resource is of the gene models resoruce.")


class Context(AnnotationPipelineContext):
    def __init__(self, args):
        self.args = args
        self._gpf_instance = None
        self._ref_genome = None
        self._gene_models = None
        self._pipeline = None

    def user_message(self, verbosity: int, msg: str):
        if self.args.verbosity >= verbosity:
            print(msg, file=sys.stderr)

    def get_gpf_instance(self):
        if self._gpf_instance is None:
            from dae.gpf_instance import GPFInstance
            if self.args.gpf_instance_dir:
                self.user_message(
                    2, f"Using the gpf_instance in the "
                    f"directory {self.args.gpf_instance_dir} specified on the "
                    "command line.")
            else:
                self.user_message(
                    2, "Using the default convigured gpf_instance.")
            self._gpf_instance = GPFInstance(self.args.gpf_instance_dir)
            self.user_message(
                1, "Using the GPF instance in "
                f"{self._gpf_instance.dae_db_dir}")
        return self._gpf_instance

    def get_grr(self):
        if self.args.pipeline == "gpf_instance":
            self.user_message(1, "Using the grr from the gpf instance "
                              "because we are using hte gpf instance's "
                              "annotation pipeline.")
            grr = self.get_gpf_instance().grr
        if self.args.grr_file_name == "gpf_instance":
            self.user_message(1, "Using the GRR from the gpf instance "
                              "as requested on the command line.")
            grr = self.get_gpf_instance().grr
        else:
            if self.args.grr_file_name:
                self.user_message(
                    1, "Using the GRR consigured in the file "
                    f"{self.args.grr_file_name} as requested on the "
                    "command line.")
            else:
                self.user_message(
                    1, "Using the defualt configured GRR.")
            grr = build_genomic_resource_repository(
                file_name=self.args.grr_file_name)
        return grr

    def get_pipeline(self):
        if self._pipeline is None:
            if self.args.pipeline == "gpf_instance":
                from dae.gpf_instance import GPFInstance
                gpf: GPFInstance = self.get_gpf_instance()
                self._pipeline = gpf.get_annotation_pipeline()
                self._pipeline.add_annotator(EffectAnnotatorAdapter(
                    gene_models=gpf.gene_models,
                    genome=gpf.reference_genome))
                # TODO: Improved on that
                # 1. copy the pipeline?
                # 2. prepend the EffectAnnotator
            else:
                self._pipeline = AnnotationPipeline.build(
                    pipeline_config_file=self.args.pipeline,
                    grr_repository=self.get_grr())
        return self._pipeline

    def get_reference_genome(self):
        if self._ref_genome is None:
            if self.args.ref_genome_resource_id is not None:
                self._ref_genome = self.get_grr().get_resource(
                    self.args.ref_genome_resource_id)
                self._ref_genome.open()
            else:
                self._ref_genome = self.get_gpf_instance().reference_genome
        return self._ref_genome

    def get_gene_models(self):
        if self.gene_models is None:
            if self.args.gene_models_resource_id is not None:
                self._gene_models = self.get_grr().get_resource(
                    self.args.gene_models_resource_id)
                self.gene_models.open()
            else:
                self.gene_models = self.get_gpf_instance().gene_models
        return self.gene_models
