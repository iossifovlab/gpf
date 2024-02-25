from __future__ import annotations

import os
import sys
import argparse
import logging
from contextlib import closing
from typing import List, Optional, Union
from dae.annotation.annotate_utils import AnnotationTool, build_pipeline, produce_partfile_paths, produce_regions

from pysam import VariantFile, TabixFile, \
    tabix_index  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline, \
    ReannotationPipeline, AnnotatorInfo

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.utils.fs_utils import tabix_index_filename
from dae.genomic_resources import build_genomic_resource_repository

from dae.task_graph import TaskGraphCli

logger = logging.getLogger("annotate_vcf")


def update_header(
    variant_file: VariantFile,
    pipeline: Union[AnnotationPipeline, ReannotationPipeline]
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


def annotate(  # pylint: disable=too-many-locals,too-many-branches
    input_file: str,
    region: Optional[tuple[str, int, int]],
    pipeline_config: list[AnnotatorInfo],
    grr_definition: Optional[dict],
    out_file_path: str,
    allow_repeated_attributes: bool,
    reannotate: Optional[str] = None,
) -> None:
    # flake8: noqa: C901
    """Annotate a region from a given input VCF file using a pipeline."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline, _ = build_pipeline(
        pipeline_config=pipeline_config,
        grr=grr,
        allow_repeated_attributes=allow_repeated_attributes,
        reannotate=reannotate
    )

    with closing(VariantFile(input_file)) as in_file:
        update_header(in_file, pipeline)
        with pipeline.open(), closing(VariantFile(
            out_file_path, "w", header=in_file.header
        )) as out_file:
            annotation_attributes = pipeline.get_attributes()

            if region is None:
                in_file_iter = in_file.fetch()
            else:
                in_file_iter = in_file.fetch(*region)

            for vcf_var in in_file_iter:
                # pylint: disable=use-list-literal
                buffers: List[List] = [list() for _ in annotation_attributes]

                if vcf_var.ref is None:
                    logger.warning(
                        "vcf variant without reference: %s %s",
                        vcf_var.chrom, vcf_var.pos
                    )
                    continue

                if vcf_var.alts is None:
                    logger.info(
                        "vcf variant without alternatives: %s %s",
                        vcf_var.chrom, vcf_var.pos
                    )
                    continue

                has_value = {}

                if isinstance(pipeline, ReannotationPipeline):
                    for col in pipeline.attributes_deleted:
                        del vcf_var.info[col]

                for alt in vcf_var.alts:
                    if isinstance(pipeline, ReannotationPipeline):
                        annotation = pipeline.annotate(
                            VCFAllele(
                                vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt
                            ), dict(vcf_var.info)
                        )
                    else:
                        annotation = pipeline.annotate(
                            VCFAllele(
                                vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt
                            )
                        )

                    for buff, attribute in zip(buffers, annotation_attributes):
                        attr = annotation.get(attribute.name)
                        attr = attr if attr is not None else "."
                        if attr != ".":
                            has_value[attribute.name] = True
                        if isinstance(attr, list):
                            attr = ";".join(map(str, attr))
                        elif isinstance(attr, dict):
                            attr = ";".join(
                                f"{k}:{v}"
                                for k, v in attr.items()
                            )
                        attr = str(attr).replace(";", "|")\
                                        .replace(",", "|")\
                                        .replace(" ", "_")
                        buff.append(attr)

                for attribute, buff in zip(annotation_attributes, buffers):
                    if has_value.get(attribute.name, False):
                        vcf_var.info[attribute.name] = buff
                out_file.write(vcf_var)


def combine(
    input_file_path: str,
    pipeline_config: Optional[list[AnnotatorInfo]],
    grr_definition: Optional[dict],
    partfile_paths: List[str],
    output_file_path: str
) -> None:
    """Combine annotated region parts into a single VCF file."""
    pipeline = build_annotation_pipeline(
        pipeline_config=pipeline_config,
        grr_repository_definition=grr_definition)

    with closing(VariantFile(input_file_path)) as input_file:
        update_header(input_file, pipeline)
        with closing(
            VariantFile(output_file_path, "w", header=input_file.header)
        ) as output_file:
            for partfile_path in partfile_paths:
                partfile = VariantFile(partfile_path)
                for rec in partfile.fetch():
                    output_file.write(rec)
        tabix_index(output_file_path, preset="vcf")

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


class AnnotateVCFTool(AnnotationTool):
    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate VCF",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("input", default="-", nargs="?",
                            help="the input vcf file")
        parser.add_argument("pipeline", default="context", nargs="?",
                            help="The pipeline definition file. By default, or if "
                            "the value is gpf_instance, the annotation pipeline "
                            "from the configured gpf instance will be used.")
        parser.add_argument("-r", "--region-size", default=300_000_000,
                            type=int, help="region size to parallelize by")
        parser.add_argument("-w", "--work-dir",
                            help="Directory to store intermediate output files in",
                            default="annotate_vcf_output")
        parser.add_argument("-o", "--output",
                            help="Filename of the output VCF result",
                            default=None)
        parser.add_argument("--reannotate", default=None,
                            help="Old pipeline config to reannotate over")

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_argumnets(parser)
        return parser
    
    def work(self) -> None:
        if self.args.output:
            output = self.args.output
        else:
            output = os.path.basename(self.args.input).split(".")[0] + "_annotated.vcf"

        if not tabix_index_filename(self.args.input):
            assert self.grr is not None
            self.task_graph.create_task(
                "all_variants_annotate",
                annotate,
                [self.args.input, None, self.pipeline.get_info(),
                self.grr.definition, output, self.args.allow_repeated_attributes,
                self.args.reannotate],
                []
            )
        else:
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(self.args.input, regions, self.args.work_dir)
            region_tasks = []
            for index, (region, file_path) in enumerate(zip(regions, file_paths)):
                assert self.grr is not None
                region_tasks.append(self.task_graph.create_task(
                    f"part-{index}",
                    annotate,
                    [self.args.input, region,
                    self.pipeline.get_info(), self.grr.definition,
                    file_path, self.args.allow_repeated_attributes, self.args.reannotate],
                    []
                ))

            assert self.grr is not None
            self.task_graph.create_task(
                "combine",
                combine,
                [self.args.input, self.pipeline.get_info(),
                self.grr.definition, file_paths, output],
                region_tasks
            )


def cli(raw_args: Optional[list[str]] = None) -> None:
    tool = AnnotateVCFTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])