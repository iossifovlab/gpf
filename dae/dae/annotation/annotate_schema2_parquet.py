import argparse
import os
from glob import glob
from typing import Optional

import yaml

from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.annotation_config import RawAnnotatorsConfig
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.parquet.helpers import merge_parquets
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    merge_variants_parquets,
    serialize_summary_schema,
    serialize_variants_data_schema,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.parquet_io import VariantsParquetWriter
from dae.schema2_storage.schema2_import_storage import (
    Schema2DatasetLayout,
    create_schema2_dataset_layout,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.variants_loaders.parquet.loader import ParquetLoader


class AnnotateSchema2ParquetTool(AnnotationTool):
    """Annotation tool for the Parquet file format."""

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate Schema2 Parquet",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "input", default="-", nargs="?",
            help="the directory containing Parquet files")
        parser.add_argument(
            "pipeline", default="context", nargs="?",
            help="The pipeline definition file. By default,"
            " or if the value is gpf_instance, the annotation"
            " pipeline from the configured gpf instance will"
            " be used.")
        parser.add_argument(
            "-r", "--region-size", default=300_000_000,
            type=int, help="region size to parallelize by")
        parser.add_argument(
            "-w", "--work-dir",
            help="Directory to store intermediate output files in",
            default="annotate_schema2_output")
        parser.add_argument(
            "-o", "--output",
            help="Path of the directory to hold the output")
        parser.add_argument(
            "-i", "--full-reannotation",
            help="Ignore any previous annotation and run "
            " a full reannotation.")

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    @staticmethod
    def annotate(
        input_dir: str,
        output_dir: str,
        pipeline_config: RawAnnotatorsConfig,
        region: str,
        grr_definition: dict,
        bucket_idx: int,
        allow_repeated_attributes: bool,
    ) -> None:
        """Run annotation over a given directory of Parquet files."""
        loader = ParquetLoader(input_dir)
        pipeline = AnnotateSchema2ParquetTool._produce_annotation_pipeline(
            pipeline_config,
            (loader.meta["annotation_pipeline"]
             if loader.has_annotation else None),
            grr_definition,
            allow_repeated_attributes=allow_repeated_attributes,
        )

        writer = VariantsParquetWriter(
            output_dir, pipeline.get_attributes(),
            loader.partition_descriptor,
            bucket_index=bucket_idx,
        )

        if isinstance(pipeline, ReannotationPipeline):
            internal_attributes = [
                attribute.name
                for annotator in (pipeline.annotators_new
                                  | pipeline.annotators_rerun)
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

    @staticmethod
    def _write_meta(
        layout: Schema2DatasetLayout,
        loader: ParquetLoader,
        pipeline_raw_config: RawAnnotatorsConfig,
        pipeline: AnnotationPipeline,
    ) -> None:
        """Write metadata to the output Parquet dataset."""

        # Write metadata
        meta_keys = [
            "annotation_pipeline",
            "summary_schema",
            "variants_data_schema",
        ]
        meta_values = [
            yaml.dump(pipeline_raw_config, sort_keys=False),
            serialize_summary_schema(
                pipeline.get_attributes(),
                loader.partition_descriptor),
            serialize_variants_data_schema(
                pipeline.get_attributes()),
        ]
        for k, v in loader.meta.items():
            if k in {
                    "annotation_pipeline",
                    "summary_schema",
                    "variants_data_schema"}:
                continue  # ignore old annotation
            meta_keys.append(k)
            meta_values.append(str(v))
        append_meta_to_parquet(layout.meta, meta_keys, meta_values)

    def work(self) -> None:
        input_dir = os.path.abspath(self.args.input)
        output_dir = os.path.abspath(self.args.output)

        loader = ParquetLoader(input_dir)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        layout = create_schema2_dataset_layout(output_dir)

        if loader.layout.summary is None:
            raise ValueError("Invalid summary dir in input layout!")
        if loader.layout.family is None:
            raise ValueError("Invalid family dir in input layout!")
        if layout.summary is None:
            raise ValueError("Invalid summary dir in output layout!")
        if layout.family is None:
            raise ValueError("Invalid family dir in output layout!")

        pipeline = AnnotateSchema2ParquetTool._produce_annotation_pipeline(
            self.pipeline.raw,
            (loader.meta["annotation_pipeline"]
             if loader.has_annotation else None),
            self.grr.definition,
            allow_repeated_attributes=self.args.allow_repeated_attributes,
        )

        self._write_meta(
            layout, loader,
            self.pipeline.raw,
            pipeline,
        )

        # Symlink pedigree and family variants directories
        os.symlink(
            os.path.split(loader.layout.pedigree)[0],
            os.path.split(layout.pedigree)[0],
            target_is_directory=True,
        )
        os.symlink(
            loader.layout.family,
            layout.family,
            target_is_directory=True,
        )

        if "reference_genome" not in loader.meta:
            raise ValueError("No reference genome found in study metadata!")
        genome = ReferenceGenome(
            self.grr.get_resource(loader.meta["reference_genome"]))

        contig_lens = {}
        contigs = loader.contigs or genome.chromosomes
        for contig in contigs:
            contig_lens[contig] = genome.get_chrom_length(contig)

        regions = [
            f"{contig}:{start}-{start + self.args.region_size}"
            for contig, length in contig_lens.items()
            for start in range(1, length, self.args.region_size)
        ]

        annotation_tasks = []
        for idx, region in enumerate(regions):
            annotation_tasks.append(self.task_graph.create_task(
                f"part_{region}",
                AnnotateSchema2ParquetTool.annotate,
                [input_dir, output_dir,
                 self.pipeline.raw, region, self.grr.definition,
                 idx, self.args.allow_repeated_attributes],
                [],
            ))

        if loader.partitioned:
            def merge_partitioned(
                summary_dir: str, partition_dir: str,
                partition_descriptor: PartitionDescriptor,
            ) -> None:
                partitions = []
                for partition in partition_dir.split("/"):
                    key, value = partition.split("=", maxsplit=1)
                    partitions.append((key, value))
                output_dir = os.path.join(summary_dir, partition_dir)
                merge_variants_parquets(
                    partition_descriptor, output_dir, partitions)

            to_join = [
                os.path.relpath(dirpath, loader.layout.summary)
                for dirpath, subdirs, _ in os.walk(loader.layout.summary)
                if not subdirs
            ]

            for path in to_join:
                self.task_graph.create_task(
                    f"merge_{path}",
                    merge_partitioned,
                    [layout.summary, path, loader.partition_descriptor],
                    annotation_tasks,
                )
        else:
            def merge(output_dir: str, output_filename: str) -> None:
                to_merge = glob(os.path.join(output_dir, "*.parquet"))
                output_path = os.path.join(output_dir, output_filename)
                merge_parquets(to_merge, output_path)

            out_path = next(loader.get_summary_pq_filepaths()).pop()

            self.task_graph.create_task(
                "merge", merge,
                [os.path.join(output_dir, "summary"),
                 os.path.basename(out_path)],
                annotation_tasks,
            )


def cli(
    raw_args: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None,
) -> None:
    tool = AnnotateSchema2ParquetTool(raw_args, gpf_instance)
    tool.run()
