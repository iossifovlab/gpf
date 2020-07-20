import os
import sys
import argparse
import time

from typing import Optional, Any

from math import ceil
from collections import defaultdict

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.cnv.loader import CNVLoader

from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescriptor, \
    NoPartitionDescriptor

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update


def save_study_config(dae_config, study_id, study_config, force=False):
    dirname = os.path.join(dae_config.studies_db.dir, study_id)
    filename = os.path.join(dirname, "{}.conf".format(study_id))

    if os.path.exists(filename):
        print("configuration file already exists:", filename)
        if not force:
            print("skipping overwring the old config file...")
            return

        new_name = os.path.basename(filename) + "." + str(time.time_ns())
        new_path = os.path.join(os.path.dirname(filename), new_name)
        print(f"Backing up configuration for {study_id} in {new_path}")
        os.rename(filename, new_path)

    os.makedirs(dirname, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(study_config)


def construct_import_annotation_pipeline(
        gpf_instance, annotation_configfile=None):

    if annotation_configfile is not None:
        config_filename = annotation_configfile
    else:
        config_filename = gpf_instance.dae_config.annotation.conf_file

    assert os.path.exists(config_filename), config_filename
    options = {
        "vcf": True,
        "c": "chrom",
        "p": "position",
        "r": "reference",
        "a": "alternative",
    }

    pipeline = PipelineAnnotator.build(
        options, config_filename, gpf_instance.genomes_db,
    )
    return pipeline


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
        self.chromosome_lengths = dict(
            self.genome.get_genomic_sequence().get_all_chrom_lengths()
        )

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
            self.genome.get_genomic_sequence().get_all_chrom_lengths()
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
                # print(
                #     f"WARNING: contig {target_chrom} not found in specified "
                #     f"genome",
                #     file=sys.stderr)
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


class MakefileGenerator:
    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance

        self.study_id = None
        self.partition_helper = None

        self.families_loader = None
        self._families = None

        self.vcf_loader = None
        self.denovo_loader = None
        self.cnv_loader = None
        self.dae_loader = None
        self.genotype_storage_id = None

    @property
    def families(self):
        if self._families is None:
            assert self.families_loader is not None
            self._families = self.families_loader.load()
        return self._families

    def build_familes_loader(self, argv):
        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(
            families_filename, params=families_params
        )
        self.families_loader = families_loader
        return self

    def build_vcf_loader(self, argv):
        variants_filenames, variants_params = \
            VcfLoader.parse_cli_arguments(argv)

        if variants_filenames is None:
            return self

        variants_loader = VcfLoader(
            self.families,
            variants_filenames,
            params=variants_params,
            genome=self.gpf_instance.genomes_db.get_genome(),
        )
        self.vcf_loader = variants_loader
        return self

    def build_denovo_loader(self, argv):
        variants_filename, variants_params = \
            DenovoLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DenovoLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.genomes_db.get_genome(),
        )
        self.denovo_loader = variants_loader
        return self

    def build_cnv_loader(self, argv):
        variants_filename, variants_params = \
            CNVLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = CNVLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.genomes_db.get_genome(),
        )
        self.cnv_loader = variants_loader
        return self

    def build_dae_loader(self, argv):
        variants_filename, variants_params = \
            DaeTransmittedLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DaeTransmittedLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.genomes_db.get_genome(),
        )
        self.dae_loader = variants_loader
        return self

    def build_study_id(self, argv):
        assert self.families_loader is not None
        if argv.study_id is not None:
            study_id = argv.study_id
        else:
            families_filename = self.families_loader.filename
            study_id, _ = os.path.splitext(os.path.basename(families_filename))
        self.study_id = study_id
        return self

    def build_partition_helper(self, argv):
        if argv.partition_description is not None:
            partition_description = ParquetPartitionDescriptor.from_config(
                argv.partition_description, root_dirname=argv.output
            )
        else:
            partition_description = NoPartitionDescriptor(argv.output)

        add_chrom_prefix = argv.add_chrom_prefix
        del_chrom_prefix = argv.del_chrom_prefix

        self.partition_helper = MakefilePartitionHelper(
            partition_description,
            self.gpf_instance.genomes_db.get_genome(),
            add_chrom_prefix=add_chrom_prefix,
            del_chrom_prefix=del_chrom_prefix,
        )

        return self

    def build_genotype_storage(self, argv):
        if argv.genotype_storage is None:
            genotype_storage_id = self.gpf_instance.dae_config.get(
                "genotype_storage", {}
            ).get("default", None)
        else:
            genotype_storage_id = argv.genotype_storage

        genotype_storage = self.gpf_instance.genotype_storage_db \
            .get_genotype_storage(
                genotype_storage_id
            )
        if genotype_storage is None:
            raise ValueError(
                f"genotype storage {genotype_storage_id} not found"
            )
        if not genotype_storage.is_impala():
            raise ValueError(
                f"genotype storage {genotype_storage_id} is not "
                f"Impala Genotype Storage"
            )
        self.genotype_storage_id = genotype_storage_id
        return self

    def build(self, argv):
        self.build_familes_loader(argv) \
            .build_denovo_loader(argv) \
            .build_cnv_loader(argv) \
            .build_vcf_loader(argv) \
            .build_dae_loader(argv) \
            .build_study_id(argv) \
            .build_partition_helper(argv) \
            .build_genotype_storage(argv)
        return self

    def _create_output_directory(self, argv):
        dirname = argv.output
        if dirname is None:
            dirname = "."
        os.makedirs(dirname, exist_ok=True)
        os.makedirs(os.path.join(dirname, "logs"), exist_ok=True)
        return dirname

    def generate_makefile(self, argv):
        dirname = self._create_output_directory(argv)
        with open(os.path.join(dirname, "Makefile"), "w") as outfile:
            self.generate_preamble(argv, outfile)
            self.generate_variants_bins(argv, outfile)
            self.generate_all_targets(argv, outfile)
            self.generate_variants_targets(argv, outfile)
            self.generate_pedigree_rule(argv, outfile)
            self.generate_variants_rules(argv, outfile)
            self.generate_hdfs_load_targets(argv, outfile)
            self.generate_report_targets(argv, outfile)

    def generate_study_config(self, argv):
        dirname = argv.output
        assert os.path.exists(dirname)

        config_dict = {
            "id": self.study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "has_cnv": False,
            "genotype_storage": {
                "id": self.genotype_storage_id,
                "tables": {
                    "variants": f'{self.study_id}_variants',
                    "pedigree": f'{self.study_id}_pedigree',
                },
            },
            "genotype_browser": {"enabled": True},
        }

        if self.denovo_loader:
            config_dict["has_denovo"] = True
        if self.cnv_loader:
            config_dict["has_denovo"] = True
            config_dict["has_cnv"] = True

        if argv.study_config is not None:
            study_config_dict = GPFConfigParser.load_config_raw(
                argv.study_config
            )
            config_dict = recursive_dict_update(config_dict, study_config_dict)

        config_builder = StudyConfigBuilder(config_dict)
        config = config_builder.build_config()
        with open(os.path.join(
                dirname, f"{self.study_id}.conf"), "w") as outfile:
            outfile.write(config)

    def _collect_variants_targets(self):
        variants_targets = []
        if self.denovo_loader is not None:
            variants_targets.append("$(denovo_bins_flags)")
        if self.cnv_loader is not None:
            variants_targets.append("$(cnv_bins_flags)")
        if self.vcf_loader is not None:
            variants_targets.append("$(vcf_bins_flags)")
        if self.dae_loader is not None:
            variants_targets.append("$(dae_bins_flags)")
        return variants_targets

    def generate_all_targets(self, argv, outfile=sys.stdout):
        targets = [
            f"${{OUTDIR}}/ped.flag",
            f"hdfs_load.flag",
            f"reports.flag"
        ]
        targets.extend(self._collect_variants_targets())

        print("\n", file=outfile)
        print("all:", " ".join(targets), file=outfile)

    def generate_variants_targets(self, argv, outfile=sys.stdout):
        variants_targets = self._collect_variants_targets()
        if len(variants_targets) > 0:
            print("\n", file=outfile)
            print("variants:", " ".join(variants_targets), file=outfile)

    def _construct_families_command(self, argv):
        families_params = FamiliesLoader.build_cli_arguments(
            self.families_loader.params
        )
        families_filename = self.families_loader.filename
        families_filename = os.path.abspath(families_filename)

        command = [
            f"ped2parquet.py {families_params} {families_filename}",
            f"--study-id {self.study_id}",
            f"-o ${{OUTDIR}}/{self.study_id}_pedigree/pedigree.parquet",
        ]
        if argv.partition_description is not None:
            pd = os.path.abspath(argv.partition_description)
            command.append(f"--pd {pd}")

        return " ".join(command)

    def generate_pedigree_rule(self, argv, outfile=sys.stdout):
        print("\n", file=outfile)
        print(f"pedigree: ${{OUTDIR}}/ped.flag\n", file=outfile)

        command = self._construct_families_command(argv)
        print(
            f"${{OUTDIR}}/ped.flag:\n"
            f"\t{command} && touch $@", file=outfile)

    def _construct_variants_command(self, argv, variants_loader, tool_command):
        families_params = FamiliesLoader.build_cli_arguments(
            self.families_loader.params)

        families_filename = self.families_loader.filename
        families_filename = os.path.abspath(families_filename)

        variants_params = variants_loader.build_cli_arguments(
            variants_loader.params)

        variants_filenames = [
            os.path.abspath(fn) for fn in variants_loader.variants_filenames
        ]
        variants_filenames = " ".join(variants_filenames)

        command = [
            f"{tool_command}",
            f"{families_params} {families_filename}",
            f"{variants_params} {variants_filenames}",
            f"--study-id {self.study_id}",
            f"-o ${{OUTDIR}}/{self.study_id}_variants",
        ]
        if argv.partition_description is not None:
            pd = os.path.abspath(argv.partition_description)
            command.append(f"--pd {pd}")
        if argv.add_chrom_prefix is not None:
            command.append(f"--add-chrom-prefix {argv.add_chrom_prefix}")
        if argv.del_chrom_prefix is not None:
            command.append(f"--del-chrom-prefix {argv.del_chrom_prefix}")

        return " ".join(command)

    def _generate_variants_bins(
        self, argv, target_prefix, variants_loader, outfile=sys.stdout
    ):
        if "target_chromosomes" in argv and \
                argv.target_chromosomes is not None:

            target_chromosomes = argv.target_chromosomes
        else:
            target_chromosomes = variants_loader.chromosomes

        variants_targets = self.partition_helper.generate_variants_targets(
            target_chromosomes
        )

        bins = " ".join(list(variants_targets.keys()))

        print("\n", file=outfile)
        print(f"{target_prefix}_bins={bins}", file=outfile)
        print(
            f"{target_prefix}_bins_flags="
            f"$(foreach bin, $({target_prefix}_bins), "
            f"${{OUTDIR}}/{target_prefix}_$(bin).flag)\n",
            file=outfile,
        )

    def generate_vcf_bins(self, argv, outfile=sys.stdout):
        if self.vcf_loader is None:
            return

        self._generate_variants_bins(
            argv, "vcf", self.vcf_loader, outfile=outfile
        )

    def generate_denovo_bins(self, argv, outfile=sys.stdout):
        if self.denovo_loader is None:
            return

        self._generate_variants_bins(
            argv, "denovo", self.denovo_loader, outfile=outfile
        )

    def generate_cnv_bins(self, argv, outfile=sys.stdout):
        if self.cnv_loader is None:
            return

        self._generate_variants_bins(
            argv, "cnv", self.cnv_loader, outfile=outfile
        )

    def generate_dae_bins(self, argv, outfile=sys.stdout):
        if self.dae_loader is None:
            return

        self._generate_variants_bins(
            argv, "dae", self.dae_loader, outfile=outfile
        )

    def generate_preamble(self, argv, outfile=sys.stdout):
        print("SHELL=/bin/bash -o pipefail", file=outfile)
        print(".DELETE_ON_ERROR:", file=outfile)
        outdir = self._get_output_dir(argv)
        print(f"OUTDIR={outdir}", file=outfile)
        print(file=outfile)

    def generate_variants_bins(self, argv, outfile=sys.stdout):
        self.generate_vcf_bins(argv, outfile)
        self.generate_dae_bins(argv, outfile)
        self.generate_denovo_bins(argv, outfile)
        self.generate_cnv_bins(argv, outfile)

    def _generate_variants_rule(
        self,
        argv,
        target_prefix,
        variants_loader,
        variants_tool,
        outfile=sys.stdout,
    ):

        print(
            f"{target_prefix}_variants: $({target_prefix}_bins_flags)\n",
            file=outfile)

        command = self._construct_variants_command(
            argv, variants_loader, variants_tool
        )
        print(
            f"${{OUTDIR}}/{target_prefix}_%.flag:\n"
            f"\t(time {command} --rb $* "
            f"> ${{OUTDIR}}/logs/{target_prefix}_$*_out.txt "
            f"2> ${{OUTDIR}}/logs/{target_prefix}_$*_err.txt) "
            f"2> ${{OUTDIR}}/logs/{target_prefix}_$*_time.txt && touch $@\n",
            file=outfile)

    def generate_vcf_rule(self, argv, outfile=sys.stdout):
        if self.vcf_loader is None:
            return

        self._generate_variants_rule(
            argv, "vcf", self.vcf_loader, "vcf2parquet.py", outfile=outfile)

    def generate_denovo_rule(self, argv, outfile=sys.stdout):
        if self.denovo_loader is None:
            return

        self._generate_variants_rule(
            argv,
            "denovo",
            self.denovo_loader,
            "denovo2parquet.py",
            outfile=outfile)

    def generate_cnv_rule(self, argv, outfile=sys.stdout):
        if self.cnv_loader is None:
            return

        self._generate_variants_rule(
            argv,
            "cnv",
            self.cnv_loader,
            "cnv2parquet.py",
            outfile=outfile)

    def generate_dae_rule(self, argv, outfile=sys.stdout):
        if self.dae_loader is None:
            return

        self._generate_variants_rule(
            argv, "dae", self.dae_loader, "dae2parquet.py", outfile=outfile)

    def generate_variants_rules(self, argv, outfile=sys.stdout):
        self.generate_vcf_rule(argv, outfile)
        self.generate_dae_rule(argv, outfile)
        self.generate_denovo_rule(argv, outfile)
        self.generate_cnv_rule(argv, outfile)

    def _construct_hdfs_load_command(self, argv):
        assert self.genotype_storage_id is not None

        # output = self._get_output_dir(argv)
        output = "."

        command = [
            f"hdfs_parquet_loader.py {self.study_id}",
            os.path.join(output, f"{self.study_id}_pedigree/pedigree.parquet"),
            os.path.join(output, f"{self.study_id}_variants"),
            f"--gs {self.genotype_storage_id}",
        ]

        # if argv.study_config:
        #     command.append(f"--study-config ./{self.study_id}.conf")

        return " ".join(command)

    def _get_output_dir(self, argv):
        output = argv.output
        if output is None:
            output = "."
        output = os.path.abspath(output)
        return output

    def generate_hdfs_load_targets(self, argv, outfile=sys.stdout):
        print("\n", file=outfile)
        print(f"hdfs_load: hdfs_load.flag\n", file=outfile)

        command = self._construct_hdfs_load_command(argv)
        variants_targets = self._collect_variants_targets()
        if len(variants_targets) > 0:
            variants_targets = " ".join(variants_targets)
            print(
                f"hdfs_load.flag: "
                f"${{OUTDIR}}/ped.flag {variants_targets}\n"
                f"\t{command} && touch $@",
                file=outfile,
            )
        else:
            print(
                f"hdfs_load.flag: ${{OUTDIR}}/ped.flag\n"
                f"\t{command} && touch $@",
                file=outfile)

    def _construct_reports_commands(self, argv):

        command = [
            f"generate_common_report.py --studies {self.study_id}",
            f"generate_denovo_gene_sets.py --studies {self.study_id}",
        ]

        return command

    def generate_report_targets(self, argv, outfile=sys.stdout):
        print("\n", file=outfile)
        print(f"reports: reports.flag\n", file=outfile)
        commands = self._construct_reports_commands(argv)
        print(f"reports.flag: hdfs_load.flag", file=outfile)
        for command in commands:
            print(f"\t{command} && touch $@", file=outfile)
        print(f"\n", file=outfile)

    @classmethod
    def cli_arguments_parser(cls, gpf_instance):
        parser = argparse.ArgumentParser(
            description="Convert variants file to parquet",
            conflict_handler="resolve",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        FamiliesLoader.cli_arguments(parser)
        DenovoLoader.cli_options(parser)
        CNVLoader.cli_options(parser)
        VcfLoader.cli_options(parser)
        DaeTransmittedLoader.cli_options(parser)

        parser.add_argument(
            "--vcf-files",
            type=str,
            nargs="+",
            metavar="<VCF filename>",
            help="VCF file to import",
        )

        parser.add_argument(
            "--denovo-file",
            type=str,
            metavar="<de Novo variants filename>",
            help="denovo variants file",
        )

        parser.add_argument(
            "--cnv-file",
            type=str,
            metavar="<CNV variants filename>",
            help="DAE CNV variants file",
        )

        parser.add_argument(
            "--dae-summary-file",
            type=str,
            metavar="<summary filename>",
            help="summary variants file to import",
        )

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
            help="Path to a config file containing the partition description",
        )

        parser.add_argument(
            "--annotation-config",
            type=str,
            default=None,
            help="Path to an annotation config file to use when annotating",
        )

        default_genotype_storage_id = (
            gpf_instance.dae_config.genotype_storage.default
        )

        parser.add_argument(
            "--genotype-storage",
            "--gs",
            type=str,
            dest="genotype_storage",
            default=default_genotype_storage_id,
            help="Genotype Storage which will be used for import "
            "[default: %(default)s]",
        )

        parser.add_argument(
            "--target-chromosomes",
            "--tc",
            type=str,
            nargs="+",
            dest="target_chromosomes",
            default=None,
            help="specified which targets to build; by default target "
            "chromosomes are extracted from variants file and/or default "
            "reference genome used in GPF instance; "
            "[default: None]",
        )

        parser.add_argument(
            "--study-config",
            type=str,
            default=None,
            dest="study_config",
            help="Config used to overwrite values in generated configuration",
        )

        return parser

    @classmethod
    def main(cls, argv=sys.argv[1:], gpf_instance=None):

        if gpf_instance is None:
            gpf_instance = GPFInstance()

        parser = cls.cli_arguments_parser(gpf_instance)
        argv = parser.parse_args(argv)

        generator = cls(gpf_instance)
        generator.build(argv)
        generator.generate_makefile(argv)
        generator.generate_study_config(argv)


class Variants2ParquetTool:

    VARIANTS_LOADER_CLASS: Any = None
    VARIANTS_TOOL: Optional[str] = None
    VARIANTS_FREQUENCIES: bool = False

    BUCKET_INDEX_DEFAULT = 1000

    @classmethod
    def cli_arguments_parser(cls, gpf_instance):
        parser = argparse.ArgumentParser(
            description="Convert variants file to parquet",
            conflict_handler="resolve",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

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
            help="Path to a config file containing the partition description",
        )

        parser.add_argument(
            "--rows",
            type=int,
            default=100_000,
            dest="rows",
            help="Amount of allele rows to write at once",
        )

        parser.add_argument(
            "--annotation-config",
            type=str,
            default=None,
            help="Path to an annotation config file to use when annotating",
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

        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(
            families_filename, params=families_params
        )
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
                print(f"resetting regions (rb: {argv.region_bin}):", regions)
                variants_loader.reset_regions(regions)

        elif argv.regions is not None:
            regions = argv.regions
            print("resetting regions (region):", regions)
            variants_loader.reset_regions(regions)

        variants_loader = cls._build_variants_loader_pipeline(
            gpf_instance, argv, variants_loader
        )

        print("argv.rows:", argv.rows)

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket_index,
            rows=argv.rows,
        )

    @classmethod
    def _build_variants_loader_pipeline(
        cls, gpf_instance, argv, variants_loader
    ):
        annotation_pipeline = construct_import_annotation_pipeline(
            gpf_instance, annotation_configfile=argv.annotation_config,
        )
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline
        )

        return variants_loader

    @classmethod
    def _load_variants(cls, argv, families, gpf_instance):
        variants_filenames, variants_params = \
            cls.VARIANTS_LOADER_CLASS.parse_cli_arguments(argv)

        variants_loader = cls.VARIANTS_LOADER_CLASS(
            families,
            variants_filenames,
            params=variants_params,
            genome=gpf_instance.genomes_db.get_genome(),
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
            gpf_instance.genomes_db.get_genome(),
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
