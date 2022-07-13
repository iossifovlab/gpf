"""
import script similar to vcf2parquet.py

# when complete add to setup.py
# do not inherit, create a new tool.
# retrace steps of Variants2ParquetTool class
"""

import os
import sys
import time
import logging
import argparse
from math import ceil
from typing import Optional, Any
from collections import defaultdict

from box import Box

from dae.backends.vcf.loader import VcfLoader
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.effect_annotator import EffectAnnotatorAdapter

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader

from dae.backends.raw.loader import (
    AnnotationPipelineDecorator,
    EffectAnnotationDecorator,
)

from dae.backends.schema2.parquet_io import (
    ParquetManager,
    ParquetPartitionDescriptor,
    NoPartitionDescriptor,
)

logger = logging.getLogger(__name__)


def save_study_config(dae_config, study_id, study_config, force=False):
    dirname = os.path.join(dae_config.studies.dir, study_id)
    filename = os.path.join(dirname, "{}.conf".format(study_id))

    if os.path.exists(filename):
        logger.info(f"configuration file already exists: {filename}")
        if not force:
            logger.info("skipping overwring the old config file...")
            return

        new_name = os.path.basename(filename) + "." + str(time.time_ns())
        new_path = os.path.join(os.path.dirname(filename), new_name)
        logger.info(f"Backing up configuration for {study_id} in {new_path}")
        os.rename(filename, new_path)

    os.makedirs(dirname, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(study_config)


def construct_import_annotation_pipeline(
    gpf_instance, annotation_configfile=None
):

    if annotation_configfile is not None:
        config_filename = annotation_configfile
    else:
        if gpf_instance.dae_config.annotation is None:
            return None
        config_filename = gpf_instance.dae_config.annotation.conf_file

    if not os.path.exists(config_filename):
        logger.warning(f"missing annotation configuration: {config_filename}")
        return None

    grr = gpf_instance.grr
    assert os.path.exists(config_filename), config_filename
    return build_annotation_pipeline(
        pipeline_config_file=config_filename, grr_repository=grr
    )


def construct_import_effect_annotator(gpf_instance):
    genome = gpf_instance.reference_genome
    gene_models = gpf_instance.gene_models

    config = Box(
        {
            "annotator_type": "effect_annotator",
            "genome": gpf_instance.dae_config.reference_genome.resource_id,
            "gene_models": gpf_instance.dae_config.gene_models.resource_id,
            "attributes": [
                {
                    "source": "allele_effects",
                    "destination": "allele_effects",
                    "internal": True,
                }
            ],
        }
    )

    effect_annotator = EffectAnnotatorAdapter(
        config, genome=genome, gene_models=gene_models
    )
    return effect_annotator


class MakefilePartitionHelper:
    def __init__(
        self,
        partition_descriptor,
        genome,
        add_chrom_prefix=None,
        del_chrom_prefix=None,
    ):

        self.genome = genome
        self.partition_descriptor = partition_descriptor
        self.chromosome_lengths = dict(self.genome.get_all_chrom_lengths())

        self._build_adjust_chrom(add_chrom_prefix, del_chrom_prefix)

    def _build_adjust_chrom(self, add_chrom_prefix, del_chrom_prefix):
        self._chrom_prefix = None

        def same_chrom(chrom):
            return chrom

        self._adjust_chrom = same_chrom
        self._unadjust_chrom = same_chrom

        if add_chrom_prefix is not None:
            self._chrom_prefix = add_chrom_prefix
            self._adjust_chrom = self._prepend_chrom_prefix
            self._unadjust_chrom = self._remove_chrom_prefix
        elif del_chrom_prefix is not None:
            self._chrom_prefix = del_chrom_prefix
            self._adjust_chrom = self._remove_chrom_prefix
            self._unadjust_chrom = self._prepend_chrom_prefix

    def region_bins_count(self, chrom):
        result = ceil(
            self.chromosome_lengths[chrom]
            / self.partition_descriptor.region_length
        )
        return result

    def _remove_chrom_prefix(self, chrom):
        assert self._chrom_prefix
        if chrom.startswith(self._chrom_prefix):
            # fmt: off
            return chrom[len(self._chrom_prefix):]
            # fmt: on
        return chrom

    def _prepend_chrom_prefix(self, chrom):
        assert self._chrom_prefix
        if not chrom.startswith(self._chrom_prefix):
            return f"{self._chrom_prefix}{chrom}"
        return chrom

    def build_target_chromosomes(self, target_chromosomes):
        return [self._adjust_chrom(tg) for tg in target_chromosomes]

    def generate_chrom_targets(self, target_chrom):
        target = target_chrom
        if target_chrom not in self.partition_descriptor.chromosomes:
            target = "other"
        region_bins_count = self.region_bins_count(target_chrom)

        chrom = self._unadjust_chrom(target_chrom)

        if region_bins_count == 1:
            return [(f"{target}_0", chrom)]
        result = []
        for region_index in range(region_bins_count):
            start = region_index * self.partition_descriptor.region_length + 1
            end = (region_index + 1) * self.partition_descriptor.region_length
            if end > self.chromosome_lengths[target_chrom]:
                end = self.chromosome_lengths[target_chrom]
            result.append(
                (f"{target}_{region_index}", f"{chrom}:{start}-{end}")
            )
        return result

    def bucket_index(self, region_bin):
        # fmt: off
        genome_chromosomes = [
            chrom
            for chrom, _ in
            self.genome.get_all_chrom_lengths()
        ]
        # fmt: on
        variants_targets = self.generate_variants_targets(genome_chromosomes)
        assert region_bin in variants_targets

        variants_targets = list(variants_targets.keys())
        return variants_targets.index(region_bin)

    def generate_variants_targets(self, target_chromosomes):

        if len(self.partition_descriptor.chromosomes) == 0:
            return {"none": [self.partition_descriptor.output]}

        generated_target_chromosomes = [
            self._adjust_chrom(tg) for tg in target_chromosomes[:]
        ]

        targets = defaultdict(list)
        for target_chrom in generated_target_chromosomes:
            if target_chrom not in self.chromosome_lengths:
                continue

            assert target_chrom in self.chromosome_lengths, (
                target_chrom,
                self.chromosome_lengths,
            )
            region_targets = self.generate_chrom_targets(target_chrom)

            for target, region in region_targets:
                # target = self.reset_target(target)
                targets[target].append(region)
        return targets


class Variants2Schema2:

    VARIANTS_LOADER_CLASS: Any = VcfLoader
    VARIANTS_TOOL: Optional[str] = "vcf2schema2.py"
    VARIANTS_FREQUENCIES: bool = True

    BUCKET_INDEX_DEFAULT = 1000

    @classmethod
    def cli_arguments_parser(cls, gpf_instance):
        parser = argparse.ArgumentParser(
            description="Convert variants file to parquet",
            conflict_handler="resolve",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("--verbose", "-V", action="count", default=0)

        FamiliesLoader.cli_arguments(parser)
        cls.VARIANTS_LOADER_CLASS.cli_arguments(parser)

        parser.add_argument(
            "--study-id",
            "--id",
            type=str,
            default=None,
            dest="study_id",
            metavar="<study id>",
            help="Study ID. "
            "If none specified, the basename of families filename is used to "
            "construct study id [default: basename(families filename)]",
        )

        parser.add_argument(
            "-o",
            "--out",
            type=str,
            default=".",
            dest="output",
            metavar="<output directory>",
            help="output directory. "
            "If none specified, current directory is used "
            "[default: %(default)s]",
        )

        parser.add_argument(
            "--pd",
            "--partition-description",
            type=str,
            default=None,
            dest="partition_description",
            help="Path to a config file containing the partition description "
            "[default: %(default)s]",
        )

        parser.add_argument(
            "--rows",
            type=int,
            default=20_000,
            dest="rows",
            help="Amount of allele rows to write at once "
            "[default: %(default)s]",
        )

        parser.add_argument(
            "--annotation-config",
            type=str,
            default=None,
            help="Path to an annotation config file to use when annotating "
            "[default: %(default)s]",
        )

        parser.add_argument(
            "-b",
            "--bucket-index",
            type=int,
            default=cls.BUCKET_INDEX_DEFAULT,
            dest="bucket_index",
            metavar="bucket index",
            help="bucket index [default: %(default)s]",
        )

        parser.add_argument(
            "--region-bin",
            "--rb",
            type=str,
            default=None,
            dest="region_bin",
            metavar="region bin",
            help="region bin [default: %(default)s] "
            "ex. X_0 "
            "If both `--regions` and `--region-bin` options are specified, "
            "the `--region-bin` option takes precedence",
        )

        parser.add_argument(
            "--regions",
            type=str,
            dest="regions",
            metavar="region",
            default=None,
            nargs="+",
            help="region to convert [default: %(default)s] "
            "ex. chr1:1-10000. "
            "If both `--regions` and `--region-bin` options are specified, "
            "the `--region-bin` option takes precedence",
        )

        return parser

    @classmethod
    def main(cls, argv=sys.argv[1:], gpf_instance=None):
        if gpf_instance is None:
            gpf_instance = GPFInstance()

        parser = cls.cli_arguments_parser(gpf_instance)

        argv = parser.parse_args(argv)
        if argv.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif argv.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif argv.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

        (
            families_filename,
            families_params,
        ) = FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(families_filename, **families_params)
        families = families_loader.load()

        variants_loader = cls._load_variants(argv, families, gpf_instance)

        partition_description = cls._build_partition_description(argv)
        generator = cls._build_partition_helper(
            argv, gpf_instance, partition_description
        )

        target_chromosomes = cls._collect_target_chromosomes(
            argv, variants_loader
        )
        variants_targets = generator.generate_variants_targets(
            target_chromosomes
        )

        # if argv.study_id is not None:
        #     study_id = argv.study_id
        # else:
        #     study_id, _ = os.path.splitext(
        #         os.path.basename(families_filename))

        bucket_index = argv.bucket_index
        if argv.region_bin is not None:
            if argv.region_bin == "none":
                pass
            else:
                assert argv.region_bin in variants_targets, (
                    argv.region_bin,
                    list(variants_targets.keys()),
                )

                regions = variants_targets[argv.region_bin]
                bucket_index = (
                    cls.BUCKET_INDEX_DEFAULT
                    + generator.bucket_index(argv.region_bin)
                )
                logger.info(
                    f"resetting regions (rb: {argv.region_bin}): {regions}"
                )
                variants_loader.reset_regions(regions)

        elif argv.regions is not None:
            regions = argv.regions
            logger.info(f"resetting regions (region): {regions}")
            variants_loader.reset_regions(regions)

        variants_loader = cls._build_variants_loader_pipeline(
            gpf_instance, argv, variants_loader
        )

        logger.debug(f"argv.rows: {argv.rows}")

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket_index,
            rows=argv.rows,
        )

    @classmethod
    def _build_variants_loader_pipeline(
        cls, gpf_instance: GPFInstance, argv, variants_loader
    ):

        effect_annotator = construct_import_effect_annotator(gpf_instance)

        variants_loader = EffectAnnotationDecorator(
            variants_loader, effect_annotator
        )

        annotation_pipeline = construct_import_annotation_pipeline(
            gpf_instance,
            annotation_configfile=argv.annotation_config,
        )
        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )

        return variants_loader

    @classmethod
    def _load_variants(cls, argv, families, gpf_instance):
        (
            variants_filenames,
            variants_params,
        ) = cls.VARIANTS_LOADER_CLASS.parse_cli_arguments(argv)

        variants_loader = cls.VARIANTS_LOADER_CLASS(
            families,
            variants_filenames,
            params=variants_params,
            genome=gpf_instance.reference_genome,
        )
        return variants_loader

    @staticmethod
    def _build_partition_description(argv):
        if argv.partition_description is not None:
            partition_description = ParquetPartitionDescriptor.from_config(
                argv.partition_description, root_dirname=argv.output
            )
        else:
            partition_description = NoPartitionDescriptor(argv.output)
        return partition_description

    @staticmethod
    def _build_partition_helper(argv, gpf_instance, partition_description):

        add_chrom_prefix = argv.add_chrom_prefix
        del_chrom_prefix = argv.del_chrom_prefix

        generator = MakefilePartitionHelper(
            partition_description,
            gpf_instance.reference_genome,
            add_chrom_prefix=add_chrom_prefix,
            del_chrom_prefix=del_chrom_prefix,
        )
        return generator

    @staticmethod
    def _collect_target_chromosomes(argv, variants_loader):
        if (
            "target_chromosomes" in argv
            and argv.target_chromosomes is not None
        ):
            target_chromosomes = argv.target_chromosomes
        else:
            target_chromosomes = variants_loader.chromosomes
        return target_chromosomes


def main(argv=sys.argv[1:], gpf_instance=None):

    Variants2Schema2.main(argv, gpf_instance=gpf_instance)


if __name__ == "__main__":
    main()
