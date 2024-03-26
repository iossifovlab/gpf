import argparse
import os
import sys
from typing import Optional
from glob import glob
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository_factory import build_genomic_resource_repository
from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.context import CLIAnnotationContext
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.parquet.parquet_writer import append_meta_to_parquet, \
    merge_variants_parquets
from dae.parquet.helpers import merge_parquets
from dae.schema2_storage.schema2_import_storage import schema2_dataset_layout
from dae.task_graph.cli_tools import TaskGraphCli
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.variants_loaders.parquet.loader import ParquetLoader
from dae.annotation.annotation_pipeline import ReannotationPipeline
from dae.parquet.schema2.parquet_io import VariantsParquetWriter


class AnnotateSchema2ParquetTool(AnnotationTool):
    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate Schema2 Parquet",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("input", default="-", nargs="?",
                            help="the directory containing Parquet files")
        parser.add_argument("pipeline", default="context", nargs="?",
                            help="The pipeline definition file. By default, or if "
                            "the value is gpf_instance, the annotation pipeline "
                            "from the configured gpf instance will be used.")
        parser.add_argument("-r", "--region-size", default=300_000_000,
                            type=int, help="region size to parallelize by")
        parser.add_argument("-w", "--work-dir",
                            help="Directory to store intermediate output files in",
                            default="annotate_schema2_output")
        parser.add_argument("-o", "--output",
                            help="Path of the directory to hold the output")
        parser.add_argument("-i", "--full-reannotation",
                            help="Ignore any previous annotation and run "
                            " a full reannotation.")

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    @staticmethod
    def get_contig_lengths(ref_genome: ReferenceGenome) -> list[tuple[str, int]]:
        result = []
        prefix = ref_genome.chrom_prefix
        contigs = {f"{prefix}{i}" for i in (*range(1, 23), "X")}
        other_contigs = set(ref_genome.chromosomes) - contigs
        max_len = 0
        for contig in contigs:
            if contig in ref_genome.chromosomes:
                result.append((contig, ref_genome.get_chrom_length(contig)))
        if other_contigs:
            for contig in other_contigs:
                max_len = max(max_len, ref_genome.get_chrom_length(contig))
            result.append(("other", max_len))
        return result

    @staticmethod
    def annotate(
        input_dir: str,
        output_dir: str,
        pipeline_config: str,
        region: str,
        grr_definition: dict,
        bucket_idx: int,
        allow_repeated_attributes: bool,
    ):
        loader = ParquetLoader(input_dir)
        pipeline = AnnotateSchema2ParquetTool._produce_annotation_pipeline(
            pipeline_config,
            loader.meta["annotation_pipeline"] \
                if loader.has_annotation else None,
            grr_definition,
            allow_repeated_attributes
        )
        writer = VariantsParquetWriter(
            output_dir, pipeline.get_attributes(),
            loader.partition_descriptor, bucket_idx
        )

        if isinstance(pipeline, ReannotationPipeline):
            internal_attributes = [
                attribute.name
                for annotator in pipeline.annotators_new | pipeline.annotators_rerun
                for attribute in annotator.attributes
                if attribute.internal
            ]
        else:
            internal_attributes = [
                attribute.name
                for attribute in pipeline.get_attributes()
                if attribute.internal
            ]

        for variant in loader.fetch_summary_variants(region=region):
            for allele in variant.alt_alleles:
                if isinstance(pipeline, ReannotationPipeline):
                    result = pipeline.annotate_summary_allele(allele)
                    for attr in pipeline.attributes_deleted:
                        del allele.attributes[attr]
                else:
                    result = pipeline.annotate(allele.get_annotatable())
                for attr in internal_attributes:
                    del result[attr]
                allele.update_attributes(result)
            writer.write_summary_variant(variant)

        writer.close()

    def work(self) -> None:
        input_dir = os.path.abspath(self.args.input)
        output_dir = os.path.abspath(self.args.output)

        loader = ParquetLoader(input_dir)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        layout = schema2_dataset_layout(output_dir)

        # Write metadata
        with open(self.args.pipeline, "r") as infile:
            raw_annotation = infile.read()
        meta_keys = ["annotation_pipeline"]
        meta_values = [raw_annotation]
        for k, v in loader.meta.items():
            if k == "annotation_pipeline":
                continue  # ignore old annotation
            meta_keys.append(k)
            meta_values.append(str(v))
        append_meta_to_parquet(layout.meta, meta_keys, meta_values)

        # Symlink pedigree and family variants directories
        os.symlink(
            os.path.split(loader.layout.pedigree)[0],
            os.path.split(layout.pedigree)[0],
            target_is_directory=True
        )
        os.symlink(loader.layout.family, layout.family, target_is_directory=True)

        if self.gpf_instance is not None:
            genome = self.gpf_instance.reference_genome
        else:
            genome = self.context.get_reference_genome()

        contig_lens = AnnotateSchema2ParquetTool.get_contig_lengths(genome)
        regions = [
            f"{contig}:{start}-{start + self.args.region_size}"
            for contig, length in contig_lens
            for start in range(1, length, self.args.region_size)
        ]

        annotation_tasks = []
        for idx, region in enumerate(regions):
            annotation_tasks.append(self.task_graph.create_task(
                f"part_{region}",
                AnnotateSchema2ParquetTool.annotate,
                [input_dir, output_dir,
                raw_annotation, region, self.grr.definition,
                idx, self.args.allow_repeated_attributes],
                []
            ))

        if loader.partitioned:
            def merge(summary_dir, partition_dir, partition_descriptor):
                partitions = [
                    tuple(partition.split("="))
                    for partition in partition_dir.split("/")
                ]
                output_dir = os.path.join(summary_dir, partition_dir)
                merge_variants_parquets(partition_descriptor, output_dir, partitions)

            to_join = [
                os.path.relpath(dirpath, loader.layout.summary)
                for dirpath, subdirs, _ in os.walk(loader.layout.summary)
                if not subdirs
            ]

            for path in to_join:
                self.task_graph.create_task(
                    f"merge_{path}",
                    merge,
                    [layout.summary, path, loader.partition_descriptor],
                    annotation_tasks
                )
        else:
            def merge(output_dir, output_filename):
                to_merge = glob(os.path.join(output_dir, "*.parquet"))
                output_path = os.path.join(output_dir, output_filename)
                merge_parquets(to_merge, output_path)

            self.task_graph.create_task(
                "merge", merge,
                [os.path.join(output_dir, "summary"),
                 os.path.basename(loader._get_pq_filepaths()[0][0])],
                annotation_tasks
            )

        del loader


def cli(raw_args: Optional[list[str]] = None, gpf_instance: Optional[GPFInstance] = None) -> None:
    tool = AnnotateSchema2ParquetTool(raw_args, gpf_instance)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])