from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Generator
from contextlib import closing
from pathlib import Path
from typing import Any

from pysam import (
    TabixFile,
    VariantFile,
    VariantRecord,
)

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotate_utils import (
    AbstractFormat,
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
    stringify,
)
from dae.annotation.annotation_config import AttributeInfo, RawAnnotatorsConfig
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_vcf")


class VCFFormat(AbstractFormat):
    def __init__(
        self,
        pipeline_config,
        pipeline_config_old,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
        input_path: str,
        output_path: str,
    ):
        super().__init__(pipeline_config, pipeline_config_old,
                         cli_args, grr_definition, region)
        self.input_path = input_path
        self.output_path = output_path
        self.grr_definition = grr_definition

        self.grr = None
        self.input_file = None
        self.output_file = None
        self.annotation_attributes = None
        self._annot_buffer = []
        self._prev_var = None

    def open(self) -> None:
        super().open()
        assert self.pipeline is not None
        self.annotation_attributes = self.pipeline.get_attributes()

        self.input_file = VariantFile(self.input_path, "r")
        update_header(self.input_file, self.pipeline)
        self.output_file = VariantFile(self.output_path, "w",
                                       header=self.input_file.header)

    def close(self):
        super().close()
        self.input_file.close()  # type: ignore
        VCFFormat._update_vcf_variant(
            self._prev_var, self._annot_buffer,  # type: ignore
            self.annotation_attributes,  # type: ignore
            self.pipeline,  # type: ignore
        )
        self.output_file.write(self._prev_var)  # type: ignore
        self.output_file.close()  # type: ignore

    def _read(self) -> Generator[Any, None, None]:
        assert self.input_file is not None

        if self.region is None:
            in_file_iter = self.input_file.fetch()
        else:
            in_file_iter = self.input_file.fetch(
                self.region.chrom, self.region.start, self.region.stop)

        for vcf_var in in_file_iter:
            if vcf_var.ref is None:
                logger.warning(
                    "vcf variant without reference: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            if vcf_var.alts is None:
                logger.info(
                    "vcf variant without alternatives: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            for alt in vcf_var.alts:
                yield vcf_var, alt

    def _convert(self, variant: tuple[VariantRecord, Any]) -> tuple[dict, Annotatable]:
        vcf_var, alt = variant
        return dict(vcf_var.info), VCFAllele(vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt)  # type: ignore

    def _write(
        self, variant: tuple[VariantRecord, Any], annotation: dict,
    ) -> None:
        vcf_var, _ = variant
        if self._prev_var is None or vcf_var == self._prev_var:
            self._annot_buffer.append(annotation)
            self._prev_var = vcf_var
        else:
            VCFFormat._update_vcf_variant(
                self._prev_var, self._annot_buffer,
                self.annotation_attributes,  # type: ignore
                self.pipeline,  # type: ignore
            )
            self.output_file.write(self._prev_var)  # type: ignore
            self._annot_buffer = [annotation]
            self._prev_var = vcf_var

    @staticmethod
    def _update_vcf_variant(
        vcf_var: VariantRecord,
        allele_annotations: list,
        attributes: list[AttributeInfo],
        pipeline: AnnotationPipeline,
    ) -> None:
        buffers: list[list] = [[] for _ in attributes]
        for annotation in allele_annotations:
            if isinstance(pipeline, ReannotationPipeline):
                for col in pipeline.attributes_deleted:
                    del vcf_var.info[col]

            for buff, attribute in zip(buffers, attributes, strict=True):
                attr = annotation.get(attribute.name)
                if isinstance(attr, list):
                    attr = ";".join(stringify(a, vcf=True) for a in attr)
                elif isinstance(attr, dict):
                    attr = ";".join(
                        f"{k}:{v}"
                        for k, v in attr.items()
                    )
                else:
                    attr = stringify(attr, vcf=True)
                attr = stringify(attr, vcf=True) \
                    .replace(";", "|")\
                    .replace(",", "|")\
                    .replace(" ", "_")
                buff.append(attr)
        # If the all values for a given attribute are
        # empty (i.e. - "."), then that attribute has no
        # values to be written and will be skipped in the output
        has_value = {
            attr.name: any(filter(lambda x: x != ".", buffers[idx]))
            for idx, attr in enumerate(attributes)
        }
        for buff, attribute in zip(buffers, attributes, strict=True):
            if attribute.internal or not has_value[attribute.name]:

                continue
            vcf_var.info[attribute.name] = buff


def update_header(
    variant_file: VariantFile,
    pipeline: AnnotationPipeline | ReannotationPipeline,
) -> None:
    """Update a variant file's header with annotation pipeline scores."""
    header = variant_file.header
    header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")
    header.add_meta("pipeline_annotation_tool", f"{' '.join(sys.argv)}")
    if isinstance(pipeline, ReannotationPipeline):
        header_info_keys = variant_file.header.info.keys()
        old_annotation_columns = {
            attr.name for attr in pipeline.pipeline_old.get_attributes()
            if not attr.internal
        }
        new_annotation_columns = {
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        }

        for info_key in header_info_keys:
            if info_key in old_annotation_columns \
                    and info_key not in new_annotation_columns:
                variant_file.header.info.remove_header(info_key)

        attributes = []
        for attr in pipeline.get_attributes():
            if attr.internal:
                continue

            if attr.name not in variant_file.header.info:
                attributes.append(attr)
    else:
        attributes = pipeline.get_attributes()

    for attribute in attributes:
        description = attribute.description
        description = description.replace("\n", " ")
        description = description.replace('"', '\\"')
        header.info.add(attribute.name, "A", "String", description)


def combine(
    input_file_path: str,
    pipeline_config: RawAnnotatorsConfig,
    grr_definition: dict | None,
    partfile_paths: list[str],
    output_file_path: str,
) -> None:
    """Combine annotated region parts into a single VCF file."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline = build_annotation_pipeline(pipeline_config, grr)

    output_file_path = output_file_path.rstrip(".gz")

    with closing(VariantFile(input_file_path)) as input_file:
        update_header(input_file, pipeline)
        with closing(
            VariantFile(output_file_path, "w", header=input_file.header),
        ) as output_file:
            for partfile_path in partfile_paths:
                partfile = VariantFile(partfile_path)
                for rec in partfile.fetch():
                    output_file.write(rec)

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


class AnnotateVCFTool(AnnotationTool):
    """Annotation tool for the VCF file format."""

    def __init__(
        self, raw_args: list[str] | None = None,
        gpf_instance: GPFInstance | None = None,
    ):
        super().__init__(raw_args, gpf_instance)
        self.output = None

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate VCF",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("input", default="-", nargs="?",
                            help="the input vcf file")
        parser.add_argument("-r", "--region-size", default=300_000_000,
                            type=int, help="region size to parallelize by")
        parser.add_argument("-w", "--work-dir",
                            help="Directory to store intermediate output files",
                            default="annotate_vcf_output")
        parser.add_argument("-o", "--output",
                            help="Filename of the output VCF result",
                            default=None)
        parser.add_argument("--reannotate", default=None,
                            help="Old pipeline config to reannotate over")
        parser.add_argument(
            "-i", "--full-reannotation",
            help="Ignore any previous annotation and run "
            " a full reannotation.",
            action="store_true",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=0,  # 0 = annotate iteratively, no batches
            help="Annotate in batches of",
        )

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    def prepare_for_annotation(self) -> None:
        if self.args.output:
            self.output = self.args.output
        else:
            self.output = os.path.basename(
                self.args.input).split(".")[0] + "_annotated.vcf"

    def add_tasks_to_graph(self) -> None:
        assert self.grr is not None
        assert self.output is not None
        pipeline_config_old = None
        if self.args.reannotate:
            pipeline_config_old = Path(self.args.reannotate).read_text()
        raw_pipeline_config = self.pipeline.raw

        if not tabix_index_filename(self.args.input):
            handler = VCFFormat(
                raw_pipeline_config,
                pipeline_config_old,
                vars(self.args),
                self.grr.definition,
                None,
                self.args.input,
                self.output,
            )
            self.task_graph.create_task(
                "all_variants_annotate",
                AnnotateVCFTool.annotate,
                [handler, self.args.batch_size > 0],
                [],
            )
        else:
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(
                self.args.input, regions, self.args.work_dir)
            region_tasks = []
            for index, (region, file_path) in enumerate(
                zip(regions, file_paths, strict=True),
            ):
                handler = VCFFormat(
                    raw_pipeline_config,
                    pipeline_config_old,
                    vars(self.args),
                    self.grr.definition,
                    region,
                    self.args.input,
                    file_path,
                )
                assert self.grr is not None
                region_tasks.append(self.task_graph.create_task(
                    f"part-{index}",
                    AnnotateVCFTool.annotate,
                    [handler, self.args.batch_size > 0],
                    [],
                ))

            assert self.grr is not None
            combine_task = self.task_graph.create_task(
                "combine",
                combine,
                [self.args.input, self.pipeline.raw,
                self.grr.definition, file_paths, self.output],
                region_tasks,
            )
            self.task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                [self.output],
                [combine_task])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateVCFTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
