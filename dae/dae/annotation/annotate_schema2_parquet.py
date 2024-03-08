import argparse
import os
import sys
from typing import Optional
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository_factory import build_genomic_resource_repository
from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.context import CLIAnnotationContext
from dae.parquet.parquet_writer import append_meta_to_parquet
from dae.schema2_storage.schema2_import_storage import schema2_dataset_layout
from dae.task_graph.cli_tools import TaskGraphCli
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.variants_loaders.parquet.loader import ParquetLoader
from dae.annotation.annotation_pipeline import AnnotatorInfo, ReannotationPipeline
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
        for contig in other_contigs:
            max_len = max(max_len, ref_genome.get_chrom_length(contig))
        result.append(("other", max_len))
        return result

    @staticmethod
    def annotate(
        input_dir: str,
        output_dir: str,
        pipeline_config: list[AnnotatorInfo],
        region: str,
        grr_definition: dict,
        bucket_idx: int,
        allow_repeated_attributes: bool,
    ):
        loader = ParquetLoader(input_dir)
        grr = build_genomic_resource_repository(definition=grr_definition)

        pipeline = build_annotation_pipeline(
            pipeline_config=pipeline_config,
            grr_repository=grr,
            allow_repeated_attributes=allow_repeated_attributes
        )
        pipeline_old = None
        if "annotation_pipeline" in loader.meta:
            pipeline_old = build_annotation_pipeline(
                pipeline_config_str=loader.meta.get("annotation_pipeline"),
                grr_repository=grr,
            )
            pipeline = ReannotationPipeline(pipeline, pipeline_old)

        writer = VariantsParquetWriter(
            output_dir, pipeline.get_attributes(),
            loader.partition_descriptor, bucket_idx
        )

        for variant in loader.fetch_summary_variants(region=region):
            for allele in variant.alt_alleles:
                if isinstance(pipeline, ReannotationPipeline):
                    result = pipeline.annotate_summary_allele(allele)
                    for attr in pipeline.attributes_deleted:
                        del allele.attributes[attr]
                else:
                    result = pipeline.annotate(allele.get_annotatable())
                allele.update_attributes(result)
            writer.write_summary_variant(variant)

        writer.close()

    def work(self) -> None:
        loader = ParquetLoader(self.args.input)

        os.mkdir(self.args.output)
        layout = schema2_dataset_layout(self.args.output)

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

        contig_lens = AnnotateSchema2ParquetTool.get_contig_lengths(
            self.context.get_reference_genome())

        regions = [
            f"{contig}:{start}-{start + self.args.region_size}"
            for contig, length in contig_lens
            for start in range(1, length, self.args.region_size)
        ]
        for idx, region in enumerate(regions):
            self.task_graph.create_task(
                f"part-{idx}",
                AnnotateSchema2ParquetTool.annotate,
                [self.args.input, self.args.output,
                self.pipeline.get_info(), region, self.grr.definition,
                idx, self.args.allow_repeated_attributes],
                []
            )

        del loader



def cli(raw_args: Optional[list[str]] = None) -> None:
    tool = AnnotateSchema2ParquetTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])