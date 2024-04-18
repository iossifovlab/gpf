# pylint: disable=too-many-lines
from __future__ import annotations

import abc
import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Type, cast
from urllib.parse import urlparse

import fsspec
from jinja2 import Template

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.import_tools import (
    MakefilePartitionHelper,
    construct_import_annotation_pipeline,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.dict_utils import recursive_dict_update
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.raw.loader import (
    AnnotationPipelineDecorator,
    VariantsLoader,
)
from dae.variants_loaders.vcf.loader import VcfLoader
from impala_storage.helpers.rsync_helpers import RsyncHelpers
from impala_storage.schema1.parquet_io import (
    ParquetWriter,
    VariantsParquetWriter,
)

logger = logging.getLogger(__name__)


class BatchGenerator:
    """Generate a Makefile which when executed imports a study."""

    @abc.abstractmethod
    def generate(self, context: dict[str, Any]) -> str:
        """Generate a Makefile/Snakemakefile."""


class SnakefileGenerator(BatchGenerator):
    """Generate a Snakefile which when executed imports a study."""

    def generate(
        self, context: dict[str, Any],
    ) -> str:
        return self.TEMPLATE.render(context)

    TEMPLATE = Template(
        """\

rule default:
    input:
        "parquet.flag"

rule all:
    input:
        "pedigree.flag",
{%- for prefix in variants -%}
        "{{prefix}}_variants.flag",
{%- endfor %}
        "hdfs.flag",
        "impala.flag",
        "setup_instance.flag",
        "reports.flag",
{%- if mirror_of %}
        "setup_remote.flag",
{% endif %}


rule pedigree:
    input:
{%- if partition_description %}
        partition_description="{{partition_description}}",
{%- endif %}
        pedigree="{{pedigree.pedigree}}"
    output:
        parquet="{{pedigree.output}}",
        flag=touch("pedigree.flag")
    benchmark:
        "logs/pedigree_benchmark.txt"
    log:
        stdout="logs/pedigree_stdout.log",
        stderr="logs/pedigree_stderr.log"
    shell:
        '''
        ped2parquet.py --study-id {{study_id}} {{pedigree.verbose}} \\
{%- if partition_description %}
            --pd {input.partition_description} \\
{%- endif %}
            {{pedigree.params}} {input.pedigree} \\
            -o {output.parquet} > {log.stdout} 2> {log.stderr}
        '''

{% for prefix, context in variants.items() %}

{{prefix}}_bins={{context.bins|tojson}}

rule {{prefix}}_variants_region_bin:
    input:
        pedigree="{{pedigree.pedigree}}",
{%- if partition_description %}
        partition_description="{{partition_description}}",
{%- endif %}
    params:
        variants="{{context.variants}}",
    output:
        {{prefix}}_flag=touch("{{prefix}}_{rb}.flag")
    benchmark:
        "logs/{{prefix}}_{rb}_benchmark.tsv"
    log:
        stdout="logs/{{prefix}}_{rb}_stdout.log",
        stderr="logs/{{prefix}}_{rb}_stderr.log"
    shell:
        '''
        {{prefix}}2parquet.py --study-id {{study_id}} {{context.verbose}} \\
            {{pedigree.params}} {input.pedigree} \\
            {{context.params}} \\
{%- if partition_description %}
            --pd {input.partition_description} \\
{%- endif %}
            -o {{variants_output}} \\
            {params.variants} \\
            --rb {wildcards.rb} > {log.stdout} 2> {log.stderr}
        '''

rule {{prefix}}_variants:
    input:
        {{prefix}}_flags=expand("{{prefix}}_{rb}.flag", rb={{prefix}}_bins)
    output:
        touch("{{prefix}}_variants.flag")

{% endfor %}


rule parquet:
    input:
        pedigree="pedigree.flag",
{%- for prefix in variants %}
        {{prefix}}_flags=expand("{{prefix}}_{rb}.flag", rb={{prefix}}_bins),
{%- endfor %}

    output:
        touch("parquet.flag")
    benchmark:
        "logs/parquet_benchmark.tsv"


rule hdfs:
    input:
        pedigree="pedigree.flag",
{%- for prefix in variants %}
        {{prefix}}_flags=expand("{{prefix}}_{rb}.flag", rb={{prefix}}_bins),
{%- endfor %}

    output:
        touch("hdfs.flag")
    benchmark:
        "logs/hdfs_benchmark.tsv"
    log:
        stdout="logs/hdfs_stdout.log",
        stderr="logs/hdfs_stderr.log"
    shell:
        '''
        hdfs_parquet_loader.py {{study_id}} \\
{%- if genotype_storage %}
            --gs {{genotype_storage}} \\
{%- endif %}
{%- if variants %}
            --variants {{variants_output}} \\
{%- endif %}
            {{pedigree.output}} \\
            > {log.stdout} 2> {log.stderr}
        '''

rule impala:
    input:
        "hdfs.flag"

    output:
        touch("impala.flag")
    benchmark:
        "logs/impala_benchmark.tsv"
    log:
        stdout="logs/impala_stdout.log",
        stderr="logs/impala_stderr.log"
    shell:
        '''
        impala_tables_loader.py {{study_id}} \\
{%- if genotype_storage %}
            --gs {{genotype_storage}} \\\n
{%- endif %}
{%- if partition_description %}
            --pd {{variants_output}}/_PARTITION_DESCRIPTION \\
{%- endif %}
{%- if variants %}
            --variants-schema {{variants_output}}/_VARIANTS_SCHEMA \\
{%- endif %}
            > {log.stdout} 2> {log.stderr}
        '''

rule setup_instance:
    input:
        "impala.flag"
    output:
        touch("setup_instance.flag")
    benchmark:
        "logs/setup_instance_benchmark.tsv"
    shell:
        '''
        rsync -avPHt  \\
            --rsync-path \\
            "mkdir -p {{dae_db_dir}}/studies/{{study_id}}/ && rsync" \\
            --ignore-existing \\
            {{outdir}}/{{study_id}}.conf {{dae_db_dir}}/studies/{{study_id}}/
        '''

rule reports:
    input:
        "setup_instance.flag"
    output:
        touch("reports.flag")
    benchmark:
        "logs/reports_benchmark.tsv"
    log:
        stdout="logs/reports_stdout.log",
        stderr="logs/reports_stderr.log"
    shell:
        '''
        generate_common_report.py --studies {{study_id}} \\
            > {log.stdout} 2> {log.stderr}
{%- if variants %}
        generate_denovo_gene_sets.py --studies {{study_id}} \\
            >> {log.stdout} 2>> {log.stderr}
{%- endif %}
        '''

{%- if mirror_of %}
rule setup_remote:
    input:
        "reports.flag"
    output:
        touch("setup_remote.flag")
    benchmark:
        "logs/setup_remote_benchmark.tsv"
    shell:
        '''
        ssh {{mirror_of.netloc}} \\
            "mkdir -p {{mirror_of.path}}/studies/{{study_id}}"
        rsync -avPHt \\
            --ignore-existing \\
            {{dae_db_dir}}/studies/{{study_id}}/ \\
            {{mirror_of.location}}/studies/{{study_id}}
        '''

{%- endif %}

        """)


class SnakefileKubernetesGenerator(BatchGenerator):

    def generate(self, context: dict[str, Any]) -> str:
        return SnakefileKubernetesGenerator.TEMPLATE.render(context)

    TEMPLATE = Template(
        """\
# To run this file against an already-configured k8s cluster run:
# snakemake -j --kubernetes --default-remote-provider S3 --default-remote-prefix {{bucket}}
#           --envvars AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY --container-image seqpipe/seqpipe-gpf-snakemake


rule default:
    input:
        "{{outdir}}/parquet.flag"


rule pedigree:
    input:
{%- if partition_description %}
        partition_description="{{partition_description}}",
{%- endif %}
        pedigree="{{pedigree.pedigree}}"
    output:
        parquet="{{pedigree.output}}",
        flag=touch("{{outdir}}/pedigree.flag")
    benchmark:
        "logs/pedigree_benchmark.txt"
    log:
        stdout="logs/pedigree_stdout.log",
        stderr="logs/pedigree_stderr.log"
    shell:
        '''
        ped2parquet.py --study-id {{study_id}} {{pedigree.verbose}} \\
{%- if partition_description %}
            --pd {input.partition_description} \\
{%- endif %}
            {{pedigree.params}} {input.pedigree} \\
            -o {output.parquet} > {log.stdout} 2> {log.stderr}
        '''

{% for prefix, context in variants.items() %}

{{prefix}}_bins={{context.bins|tojson}}

rule {{prefix}}_variants_region_bin:
    input:
        pedigree="{{pedigree.pedigree}}",
{%- if partition_description %}
        partition_description="{{partition_description}}",
{%- endif %}
    params:
        variants="{{context.variants}}",
    output:
        {{prefix}}_flag=touch("{{outdir}}/{{prefix}}_{rb}.flag")
    benchmark:
        "logs/{{prefix}}_{rb}_benchmark.tsv"
    log:
        stdout="logs/{{prefix}}_{rb}_stdout.log",
        stderr="logs/{{prefix}}_{rb}_stderr.log"
    shell:
        '''
        {{prefix}}2parquet.py --study-id {{study_id}} {{context.verbose}} \\
            {{pedigree.params}} {input.pedigree} \\
            {{context.params}} \\
{%- if partition_description %}
            --pd {input.partition_description} \\
{%- endif %}
            -o {{variants_output}} \\
            {params.variants} \\
            --rb {wildcards.rb} > {log.stdout} 2> {log.stderr}
        '''

rule {{prefix}}_variants:
    input:
        {{prefix}}_flags=expand("{{outdir}}/{{prefix}}_{rb}.flag", rb={{prefix}}_bins)
    output:
        touch("{{outdir}}/{{prefix}}_variants.flag")

{% endfor %}


rule parquet:
    input:
        pedigree="{{outdir}}/pedigree.flag",
{%- for prefix in variants %}
        {{prefix}}_flags=expand("{{outdir}}/{{prefix}}_{rb}.flag", rb={{prefix}}_bins),
{%- endfor %}

    output:
        touch("{{outdir}}/parquet.flag")
    benchmark:
        "logs/parquet_benchmark.tsv"

        """)  # noqa


class BatchImporter:
    """Class that should run tasks for importing of a study."""

    def __init__(self, gpf_instance: GPFInstance) -> None:
        self.gpf_instance = gpf_instance
        assert self.gpf_instance is not None

        self.study_id = None
        self.partition_helper: Optional[MakefilePartitionHelper] = None

        self.families_loader: Optional[FamiliesLoader] = None
        self._families: Optional[FamiliesData] = None

        self.variants_loaders: dict[str, VariantsLoader] = {}

        self.vcf_loader: Optional[VcfLoader] = None
        self.denovo_loader: Optional[DenovoLoader] = None
        self.cnv_loader: Optional[CNVLoader] = None
        self.dae_loader: Optional[DaeTransmittedLoader] = None
        self.genotype_storage_id = None

    @property
    def families(self) -> FamiliesData:
        if self._families is None:
            assert self.families_loader is not None
            self._families = self.families_loader.load()
        return self._families

    def build_familes_loader(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a family loader based on CLI arguments."""
        families_filenames, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)
        families_filename = families_filenames[0]

        families_loader = FamiliesLoader(
            families_filename, **families_params,
        )
        self.families_loader = families_loader
        return self

    def build_vcf_loader(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a VCF loader based on the CLI arguments."""
        variants_filenames, variants_params = \
            VcfLoader.parse_cli_arguments(argv)

        if variants_filenames is None:
            return self

        variants_loader = VcfLoader(
            self.families,
            variants_filenames,
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.vcf_loader = variants_loader
        self.variants_loaders["vcf"] = variants_loader
        return self

    def build_denovo_loader(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a de Novo variants loader based on the CLI arguments."""
        variants_filename, variants_params = \
            DenovoLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DenovoLoader(
            self.families,
            variants_filename,  # type: ignore
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.denovo_loader = variants_loader
        self.variants_loaders["denovo"] = variants_loader
        return self

    def build_cnv_loader(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a CNV loader based on the CLI arguments."""
        variants_filenames, variants_params = \
            CNVLoader.parse_cli_arguments(argv)
        logger.info("CNV loader parameters: %s", variants_params)
        if not variants_filenames:
            return self
        variants_loader = CNVLoader(
            self.families,
            variants_filenames,  # type: ignore
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.cnv_loader = variants_loader
        self.variants_loaders["cnv"] = variants_loader
        return self

    def build_dae_loader(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a DAE loader based on the CLI arguments."""
        variants_filename, variants_params = \
            DaeTransmittedLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DaeTransmittedLoader(
            self.families,
            variants_filename,  # type: ignore
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.dae_loader = variants_loader
        self.variants_loaders["dae"] = variants_loader
        return self

    def build_study_id(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a study_id from CLI arguments."""
        assert self.families_loader is not None
        if argv.study_id is not None:
            study_id = argv.study_id
        else:
            families_filename = self.families_loader.filename
            assert isinstance(families_filename, str)
            study_id, _ = os.path.splitext(os.path.basename(families_filename))
        self.study_id = study_id
        return self

    def build_partition_helper(
        self, argv: argparse.Namespace,
    ) -> BatchImporter:
        """Load and adjust the parition description."""
        if argv.partition_description is not None:
            partition_description = PartitionDescriptor.parse(
                argv.partition_description)
        else:
            partition_description = PartitionDescriptor()

        self.partition_helper = MakefilePartitionHelper(
            partition_description,
            self.gpf_instance.reference_genome,
        )

        return self

    def build_genotype_storage(
        self, argv: argparse.Namespace,
    ) -> BatchImporter:
        """Construct a genotype storage."""
        if argv.genotype_storage is None:
            genotype_storage_id = self.gpf_instance.dae_config.get(
                "genotype_storage", {},
            ).get("default", None)
        else:
            genotype_storage_id = argv.genotype_storage

        genotype_storage = self.gpf_instance.genotype_storages \
            .get_genotype_storage(
                genotype_storage_id,
            )
        if genotype_storage is None:
            raise ValueError(
                f"genotype storage {genotype_storage_id} not found",
            )
        if genotype_storage.storage_type != "impala":
            raise ValueError(
                f"genotype storage {genotype_storage_id} is not "
                f"Impala Genotype Storage",
            )
        self.genotype_storage_id = genotype_storage_id
        return self

    def build(self, argv: argparse.Namespace) -> BatchImporter:
        """Construct a study importer based on CLI aruments."""
        self.build_familes_loader(argv) \
            .build_denovo_loader(argv) \
            .build_cnv_loader(argv) \
            .build_vcf_loader(argv) \
            .build_dae_loader(argv) \
            .build_study_id(argv) \
            .build_partition_helper(argv) \
            .build_genotype_storage(argv)
        return self

    def generate_instructions(self, argv: argparse.Namespace) -> None:
        """Generate instruction for importing a study using CLI arguments."""
        dirname = argv.generator_output or argv.output
        context = self.build_context(argv)
        if argv.tool == "snakemake":
            generator: BatchGenerator = SnakefileGenerator()
            filename = os.path.join(dirname, "Snakefile")
        elif argv.tool == "snakemake-kubernetes":
            generator = SnakefileKubernetesGenerator()
            filename = os.path.join(dirname, "Snakefile")
        else:
            assert False, f"unexpected tool format: {argv.tool}"

        content = generator.generate(context)

        with fsspec.open(filename, "w") as outfile:
            outfile.write(content)

    def build_context(
        self, argv: argparse.Namespace,
    ) -> dict[str, Any]:
        if urlparse(argv.output).scheme:
            return self._build_context_remote(argv)
        return self._build_context_local(argv)

    def _build_context_remote(
        self, argv: argparse.Namespace,
    ) -> dict[str, Any]:
        context = self._build_context_local(argv)

        out_url = urlparse(argv.output)
        outdir = out_url.path[1:]  # strip leading '/' of path
        bucket = out_url.netloc

        context.update({
            "outdir": outdir,
            "bucket": bucket,
        })

        if argv.partition_description:
            context["partition_description"] = \
                urlparse(argv.partition_description).path[1:]

        study_id = context["study_id"]
        pedigree_output = os.path.join(
            outdir, f"{study_id}_pedigree", "pedigree.parquet")

        assert self.families_loader is not None
        assert isinstance(self.families_loader.filename, str)
        pedigree_pedigree = urlparse(self.families_loader.filename).path[1:]
        context["pedigree"].update({
            "pedigree": pedigree_pedigree,
            "output": pedigree_output,
        })

        for prefix, variants_loader in self.variants_loaders.items():
            variants_context = context["variants"][prefix]
            variants_context["variants"] = " ".join(
                list(variants_loader.variants_filenames))

        if self.variants_loaders:
            context["variants_output"] = \
                os.path.join(argv.output, f"{study_id}_variants")

        return context

    def _build_context_local(
        self, argv: argparse.Namespace,
    ) -> dict[str, Any]:
        outdir = argv.output
        study_id = self.study_id

        context = {
            "study_id": study_id,
            "outdir": outdir,
            "dae_db_dir": self.gpf_instance.dae_dir,
        }

        verbose = ""
        if argv.verbose > 0:
            verbose = f"-{'V' * argv.verbose}"

        if argv.genotype_storage:
            context["genotype_storage"] = argv.genotype_storage
        if argv.partition_description:
            context["partition_description"] = argv.partition_description

        assert self.families_loader is not None
        pedigree_params_dict = self.families_loader.build_arguments_dict()
        pedigree_params = self.families_loader.build_cli_arguments(
            pedigree_params_dict)
        assert isinstance(self.families_loader.filename, str)
        pedigree_pedigree = os.path.abspath(
            self.families_loader.filename)
        pedigree_output = os.path.abspath(os.path.join(
            outdir, f"{study_id}_pedigree", "pedigree.parquet"))
        context["pedigree"] = {
            "pedigree": pedigree_pedigree,
            "params": pedigree_params,
            "output": pedigree_output,
            "verbose": verbose,
        }

        context["variants"] = {}
        if self.variants_loaders:
            context["variants_output"] = os.path.abspath(os.path.join(
                outdir, f"{study_id}_variants"))

        for prefix, variants_loader in self.variants_loaders.items():
            variants_context: Dict[str, Any] = {}
            if "target_chromosomes" in argv and \
                    argv.target_chromosomes is not None:
                target_chromosomes = argv.target_chromosomes
            else:
                target_chromosomes = variants_loader.chromosomes

            assert self.partition_helper is not None
            variants_targets = self.partition_helper.generate_variants_targets(
                target_chromosomes,
            )

            variants_context["bins"] = list(variants_targets.keys())
            variants_context["variants"] = " ".join([
                os.path.abspath(fn)
                for fn in variants_loader.variants_filenames
            ])
            variants_params_dict = variants_loader.build_arguments_dict()
            variants_context["params"] = variants_loader.build_cli_arguments(
                variants_params_dict)
            variants_context["verbose"] = verbose

            context["variants"][prefix] = variants_context  # type: ignore

        context["mirror_of"] = {}
        if self.gpf_instance.dae_config.mirror_of:
            rsync_helper = RsyncHelpers(
                self.gpf_instance.dae_config.mirror_of)
            context["mirror_of"][
                "location"] = rsync_helper.rsync_remote  # type: ignore
            context["mirror_of"][
                "path"] = rsync_helper.parsed_remote.path  # type: ignore
            context["mirror_of"][
                "netloc"] = rsync_helper.parsed_remote.netloc  # type: ignore

        return context

    def generate_study_config(self, argv: argparse.Namespace) -> None:
        """Generate a study config for imported study."""
        dirname = argv.output

        config_dict = {
            "id": self.study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "has_cnv": False,
            "genotype_storage": {
                "id": self.genotype_storage_id,
                "tables": {
                    "variants": f"{self.study_id}_variants",
                    "pedigree": f"{self.study_id}_pedigree",
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
                argv.study_config,
            )
            config_dict = recursive_dict_update(study_config_dict, config_dict)

        config_builder = StudyConfigBuilder(config_dict)
        config = config_builder.build_config()
        with fsspec.open(os.path.join(
                dirname, f"{self.study_id}.conf"), "w") as outfile:
            outfile.write(config)

    @classmethod
    def cli_arguments_parser(
        cls, gpf_instance: GPFInstance,
    ) -> argparse.ArgumentParser:
        """Parse CLI arguments."""
        parser = argparse.ArgumentParser(
            description="Convert variants file to parquet",
            conflict_handler="resolve",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument("--verbose", "-V", action="count", default=0)

        FamiliesLoader.cli_arguments(parser)
        DenovoLoader.cli_arguments(parser, options_only=True)
        CNVLoader.cli_arguments(parser, options_only=True)
        VcfLoader.cli_arguments(parser, options_only=True)
        DaeTransmittedLoader.cli_arguments(parser, options_only=True)

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
            "--generator-out",
            type=str,
            default=None,
            dest="generator_output",
            metavar="<output directory>",
            help="generator output directory. "
            "If none specified, the output directory is used",
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

        default_genotype_storage_id = None
        if gpf_instance is not None:
            default_genotype_storage_id = gpf_instance\
                .dae_config\
                .genotype_storage.default

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
        parser.add_argument(
            "--tool",
            type=str,
            default="snakemake",
            dest="tool",
            help="Tool format for generated build instructions. "
            "Supported options are 'snakemake' and 'make'. "
            "[default: 'snakemake']",
        )
        return parser

    @staticmethod
    def main(
        argv: Optional[list[str]] = None,
        gpf_instance: Optional[GPFInstance] = None,
    ) -> None:
        """Construct and run the importer based on CLI arguments.

        Main function called from CLI tools.
        """
        if gpf_instance is None:
            try:
                gpf_instance = GPFInstance.build()
            except Exception:  # pylint: disable=broad-except
                logger.warning("GPF not configured properly...", exc_info=True)

        assert gpf_instance is not None
        parser = BatchImporter.cli_arguments_parser(gpf_instance)
        if argv is None:
            argv = sys.argv[1:]
        args = parser.parse_args(argv)

        if args.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

        importer = BatchImporter(gpf_instance)
        importer.build(args)
        importer.generate_instructions(args)
        importer.generate_study_config(args)


class Variants2ParquetTool:
    """Tool for importing variants into parquet dataset."""

    VARIANTS_LOADER_CLASS: Optional[Type[VariantsLoader]] = None
    VARIANTS_TOOL: Optional[str] = None
    VARIANTS_FREQUENCIES: bool = False

    BUCKET_INDEX_DEFAULT = 1000

    @classmethod
    def cli_arguments_parser(
        cls, _gpf_instance: GPFInstance,
    ) -> argparse.ArgumentParser:
        """Parse CLI arguments."""
        parser = argparse.ArgumentParser(
            description="Convert variants file to parquet",
            conflict_handler="resolve",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("--verbose", "-V", action="count", default=0)

        FamiliesLoader.cli_arguments(parser)

        assert cls.VARIANTS_LOADER_CLASS is not None
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
    def main(
        cls, argv: Optional[List[str]] = None,
        gpf_instance: Optional[GPFInstance] = None,
    ) -> None:
        """Construct and run importer to transform variants into parquet.

        Called from CLI tools.
        """
        if gpf_instance is None:
            gpf_instance = GPFInstance.build()

        parser = cls.cli_arguments_parser(gpf_instance)

        if argv is None:
            argv = sys.argv[1:]
        args = parser.parse_args(argv)
        if args.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

        cls.run(args, gpf_instance)

    @classmethod
    def run(
        cls, argv: argparse.Namespace,
        gpf_instance: Optional[GPFInstance] = None,
    ) -> None:
        """Run actual variants import into parquet dataset."""
        if gpf_instance is None:
            gpf_instance = GPFInstance.build()

        families_filenames, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)
        families_filename = families_filenames[0]
        families_loader = FamiliesLoader(
            families_filename, **families_params,
        )
        families = families_loader.load()

        variants_loader = cls._load_variants(argv, families, gpf_instance)

        partition_description = cls._build_partition_description(argv)
        generator = cls._build_partition_helper(
            gpf_instance, partition_description,
        )

        target_chromosomes = cls._collect_target_chromosomes(
            argv, variants_loader,
        )
        variants_targets = generator.generate_variants_targets(
            target_chromosomes,
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
                    "resetting regions (rb: %s): %s", argv.region_bin, regions)
                variants_loader.reset_regions(regions)

        elif argv.regions is not None:
            regions = argv.regions
            logger.info("resetting regions (region): %s", regions)
            variants_loader.reset_regions(regions)

        variants_loader = cls._build_variants_loader_pipeline(
            gpf_instance, argv, variants_loader,
        )

        logger.debug("argv.rows: %s", argv.rows)

        out_dir = argv.output
        logger.debug("writing to output directory: %s", out_dir)
        ParquetWriter.variants_to_parquet(
            out_dir,
            variants_loader,
            partition_description,
            VariantsParquetWriter,
            bucket_index=bucket_index,
            rows=argv.rows,
        )

        ParquetWriter.write_meta(
            out_dir,
            variants_loader,
            partition_description,
            VariantsParquetWriter,
        )

    @classmethod
    def _build_variants_loader_pipeline(
        cls, gpf_instance: GPFInstance,
        argv: argparse.Namespace,
        variants_loader: VariantsLoader,
    ) -> VariantsLoader:

        annotation_pipeline = construct_import_annotation_pipeline(
            gpf_instance, annotation_configfile=argv.annotation_config,
        )

        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline,
            )

        return variants_loader

    @classmethod
    def _load_variants(
        cls, argv: argparse.Namespace,
        families: FamiliesData,
        gpf_instance: GPFInstance,
    ) -> VariantsLoader:
        if cls.VARIANTS_LOADER_CLASS is None:
            raise ValueError("VARIANTS_LOADER_CLASS not set")

        variants_filenames, variants_params = \
            cls.VARIANTS_LOADER_CLASS.parse_cli_arguments(argv)

        # pylint: disable=not-callable
        variants_loader = cls.VARIANTS_LOADER_CLASS(
            families,
            variants_filenames,
            genome=gpf_instance.reference_genome,
            params=variants_params,
        )
        return variants_loader

    @staticmethod
    def _build_partition_description(
        argv: argparse.Namespace,
    ) -> PartitionDescriptor:
        if argv.partition_description is not None:
            partition_description = PartitionDescriptor.parse(
                argv.partition_description)
        else:
            partition_description = PartitionDescriptor()
        return partition_description

    @staticmethod
    def _build_partition_helper(
        gpf_instance: GPFInstance,
        partition_description: PartitionDescriptor,
    ) -> MakefilePartitionHelper:

        generator = MakefilePartitionHelper(
            partition_description,
            gpf_instance.reference_genome,
        )
        return generator

    @staticmethod
    def _collect_target_chromosomes(
        argv: argparse.Namespace,
        variants_loader: VariantsLoader,
    ) -> List[str]:
        if (
            "target_chromosomes" in argv
            and argv.target_chromosomes is not None
        ):
            target_chromosomes = argv.target_chromosomes
        else:
            target_chromosomes = variants_loader.chromosomes
        return cast(list[str], target_chromosomes)
