# pylint: disable=too-many-lines
import abc
import os
import sys
import glob
import argparse
import time
import logging
import shutil
from urllib.parse import urlparse
from typing import Optional, Callable
from math import ceil
from collections import defaultdict

import fsspec
import toml
from box import Box

from jinja2 import Template

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.effect_annotator import EffectAnnotatorAdapter

from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator, \
    EffectAnnotationDecorator, VariantsLoader
from dae.variants_loaders.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.cnv.loader import CNVLoader

from dae.parquet.schema1.parquet_io import ParquetManager, \
    ParquetPartitionDescriptor, \
    NoPartitionDescriptor

from dae.impala_storage.helpers.rsync_helpers import RsyncHelpers

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update


logger = logging.getLogger(__name__)


def save_study_config(dae_config, study_id, study_config, force=False):
    """Save the study config to a file."""
    dirname = os.path.join(dae_config.studies.dir, study_id)
    filename = os.path.join(dirname, f"{study_id}.conf")

    if os.path.exists(filename):
        logger.info(
            "configuration file already exists: %s", filename)
        if not force:
            logger.info("skipping overwring the old config file...")
            return

        new_name = os.path.basename(filename) + "." + str(time.time_ns())
        new_path = os.path.join(os.path.dirname(filename), new_name)
        logger.info(
            "Backing up configuration for %s in %s", study_id, new_path)
        os.rename(filename, new_path)

    os.makedirs(dirname, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(study_config)


def construct_import_annotation_pipeline(
        gpf_instance, annotation_configfile=None):
    """Construct annotation pipeline for importing data."""
    if annotation_configfile is not None:
        config_filename = annotation_configfile
    else:
        if gpf_instance.dae_config.annotation is None:
            return None
        config_filename = gpf_instance.dae_config.annotation.conf_file

    if not os.path.exists(config_filename):
        logger.warning("missing annotation configuration: %s", config_filename)
        return None

    grr = gpf_instance.grr
    assert os.path.exists(config_filename), config_filename
    pipeline = build_annotation_pipeline(
        pipeline_config_file=config_filename, grr_repository=grr)
    # pipeline.open()  # FIXME:
    return pipeline


def construct_import_effect_annotator(gpf_instance):
    """Construct import effect annotator."""
    genome = gpf_instance.reference_genome
    gene_models = gpf_instance.gene_models

    config = Box({
        "annotator_type": "effect_annotator",
        "genome": genome.resource_id,
        "gene_models": gene_models.resource_id,
        "attributes": [
            {
                "source": "allele_effects",
                "destination": "allele_effects",
                "internal": True
            }
        ]
    })

    effect_annotator = EffectAnnotatorAdapter(
        config, genome=genome, gene_models=gene_models)
    return effect_annotator


class MakefilePartitionHelper:
    """Helper class for organizing partition targets."""

    def __init__(
            self,
            partition_descriptor,
            genome,
            add_chrom_prefix=None,
            del_chrom_prefix=None):

        self.genome = genome
        self.partition_descriptor = partition_descriptor
        self.chromosome_lengths = dict(
            self.genome.get_all_chrom_lengths()
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
        """Generate variant targets based on partition descriptor."""
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
        """Return bucket index based on variants target."""
        genome_chromosomes = [
            chrom
            for chrom, _ in
            self.genome.get_all_chrom_lengths()
        ]
        variants_targets = self.generate_variants_targets(genome_chromosomes)
        assert region_bin in variants_targets

        variants_targets = list(variants_targets.keys())
        return variants_targets.index(region_bin)

    def generate_variants_targets(self, target_chromosomes, mode=None):
        """Produce variants targets."""
        if len(self.partition_descriptor.chromosomes) == 0:
            return {"none": [self.partition_descriptor.output]}

        generated_target_chromosomes = [
            self._adjust_chrom(tg) for tg in target_chromosomes[:]
        ]

        if mode == "single_bucket":
            targets = {"all": [None]}
            return targets
        if mode == "chromosome":
            targets = {chrom: [chrom]
                       for chrom in generated_target_chromosomes}
            return targets
        if mode is not None:
            raise ValueError(f"Invalid value for mode '{mode}'")

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


class BatchGenerator:
    """Generate a Makefile which when executed imports a study."""

    @abc.abstractmethod
    def generate(self, context):
        """Generate a Makefile/Snakemakefile."""


class MakefileGenerator(BatchGenerator):

    def generate(self, context):
        return MakefileGenerator.TEMPLATE.render(context)

    TEMPLATE = Template(
        """\

{%- for prefix, context in variants.items() %}

{{prefix}}_bins={{context.bins|join(" ")}}
{{prefix}}_bins_flags=$(foreach bin,$({{prefix}}_bins),{{prefix}}_$(bin).flag)

{%- endfor %}

defaults: parquet.flag

all: pedigree.flag \\
{%- for prefix in variants %}
\t\t$({{prefix}}_bins_flags) \\
{%- endfor %}
\t\thdfs.flag impala.flag \\
\t\tsetup_instance.flag \\
{%- if mirror_of %}
\t\treports.flag \\
\t\tsetup_remote.flag
{%- else %}
\t\treports.flag
{%- endif %}

pedigree: pedigree.flag

pedigree.flag:
\t(time ped2parquet.py --study-id {{study_id}} \\
\t\t{{pedigree.params}} {{pedigree.pedigree}} \\
{%- if partition_description %}
\t\t--pd {{partition_description}} \\
{%- endif %}
\t\t-o {{pedigree.output}} \\
\t\t> logs/pedigree_stdout.log 2> logs/pedigree_stderr.log && touch $@) \\
\t\t\t2> logs/pedigree_benchmark.txt


{%- for prefix, context in variants.items() %}

{{prefix}}_%.flag:
\t(time {{prefix}}2parquet.py --study-id {{study_id}} \\
\t\t{{pedigree.params}} {{pedigree.pedigree}} \\
\t\t{{context.params}} {{context.variants}} \\
{%- if partition_description %}
\t\t--pd {{partition_description}} \\
{%- endif %}
\t\t-o {{ variants_output }} \\
\t\t--rb $* > logs/{{prefix}}_$*_stdout.log \\
\t\t2> logs/{{prefix}}_$*_stderr.log && touch $@) \\
\t\t2> logs/{{prefix}}_$*_benchmark.txt

{%- endfor %}


parquet: parquet.flag

parquet.flag: \\
{%- for prefix in variants %}
\t\t$({{prefix}}_bins_flags) \\
{%- endfor %}
\t\tpedigree.flag
\ttouch parquet.flag

hdfs: hdfs.flag

hdfs.flag: \\
{%- for prefix in variants %}
\t\t$({{prefix}}_bins_flags) \\
{%- endfor %}
\t\tpedigree.flag
\thdfs_parquet_loader.py {{study_id}} \\
\t\t{{pedigree.output}} \\
{%- if variants %}
\t\t--variants {{variants_output}} \\
{%- endif -%}
\t\t--gs {{genotype_storage}} \\
\t\t&& touch $@


impala: impala.flag

impala.flag: hdfs.flag
\timpala_tables_loader.py \\
\t\t{{study_id}} \\
{%- if genotype_storage %}
\t\t--gs {{genotype_storage}} \\
{%- endif %}
{%- if partition_description %}
\t\t--pd {{variants_output}}/_PARTITION_DESCRIPTION \\
{%- endif %}
\t\t--variants-schema {{variants_output}}/_VARIANTS_SCHEMA \\
\t\t&& touch $@


setup_instance: setup_instance.flag

setup_instance.flag: impala.flag
\trsync -avPHt  \\
\t\t--rsync-path "mkdir -p {{dae_db_dir}}/studies/{{study_id}}/ && rsync" \\
\t\t--ignore-existing {{outdir}}/ {{dae_db_dir}}/studies/{{study_id}}/ \\
\t\t&& touch $@


reports: reports.flag

reports.flag: setup_instance.flag
\tgenerate_common_report.py --studies {{study_id}} \\
\t\t&& generate_denovo_gene_sets.py --studies {{study_id}} \\
\t\t&& touch $@


setup_remote: setup_remote.flag

setup_remote.flag: reports.flag
\trsync -avPHt \\
\t\t--rsync-path \\
\t\t"mkdir -p {{mirror_of.path}}/studies/{{study_id}}/ && rsync" \\
\t\t--ignore-existing {{dae_db_dir}}/studies/{study_id}}/ \\
\t\t{{mirror_of.location}}/studies/{{study_id}}/ && touch $@

        """)


class SnakefileGenerator:
    """Generate a Snakefile which when executed imports a study."""

    def generate(self, context):
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

    def generate(self, context):
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

    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance
        assert self.gpf_instance is not None

        self.study_id = None
        self.partition_helper = None

        self.families_loader = None
        self._families = None

        self.variants_loaders = {}

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
        """Construct a family loader based on CLI arguments."""
        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(
            families_filename, **families_params
        )
        self.families_loader = families_loader
        return self

    def build_vcf_loader(self, argv):
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

    def build_denovo_loader(self, argv):
        """Construct a de Novo variants loader based on the CLI arguments."""
        variants_filename, variants_params = \
            DenovoLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DenovoLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.denovo_loader = variants_loader
        self.variants_loaders["denovo"] = variants_loader
        return self

    def build_cnv_loader(self, argv):
        """Construct a CNV loader based on the CLI arguments."""
        variants_filename, variants_params = \
            CNVLoader.parse_cli_arguments(argv)

        logger.info("CNV loader parameters: %s", variants_params)
        if variants_filename is None:
            return self
        variants_loader = CNVLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.cnv_loader = variants_loader
        self.variants_loaders["cnv"] = variants_loader
        return self

    def build_dae_loader(self, argv):
        """Construct a DAE loader based on the CLI arguments."""
        variants_filename, variants_params = \
            DaeTransmittedLoader.parse_cli_arguments(argv)

        if variants_filename is None:
            return self
        variants_loader = DaeTransmittedLoader(
            self.families,
            variants_filename,
            params=variants_params,
            genome=self.gpf_instance.reference_genome,
        )
        self.dae_loader = variants_loader
        self.variants_loaders["dae"] = variants_loader
        return self

    def build_study_id(self, argv):
        """Construct a study_id from CLI arguments."""
        assert self.families_loader is not None
        if argv.study_id is not None:
            study_id = argv.study_id
        else:
            families_filename = self.families_loader.filename
            study_id, _ = os.path.splitext(os.path.basename(families_filename))
        self.study_id = study_id
        return self

    def build_partition_helper(self, argv):
        """Load and adjust the parition description."""
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
            self.gpf_instance.reference_genome,
            add_chrom_prefix=add_chrom_prefix,
            del_chrom_prefix=del_chrom_prefix,
        )

        return self

    def build_genotype_storage(self, argv):
        """Construct a genotype storage."""
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
        if genotype_storage.get_storage_type() != "impala":
            raise ValueError(
                f"genotype storage {genotype_storage_id} is not "
                f"Impala Genotype Storage"
            )
        self.genotype_storage_id = genotype_storage_id
        return self

    def build(self, argv):
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

    def generate_instructions(self, argv):
        """Generate instruction for importing a study using CLI arguments."""
        dirname = argv.generator_output or argv.output
        context = self.build_context(argv)
        if argv.tool == "make":
            generator = MakefileGenerator()
            filename = os.path.join(dirname, "Makefile")
        elif argv.tool == "snakemake":
            generator = SnakefileGenerator()
            filename = os.path.join(dirname, "Snakefile")
        elif argv.tool == "snakemake-kubernetes":
            generator = SnakefileKubernetesGenerator()
            filename = os.path.join(dirname, "Snakefile")
        else:
            assert False, f"unexpected tool format: {argv.tool}"

        content = generator.generate(context)

        with fsspec.open(filename, "w") as outfile:
            outfile.write(content)

    def build_context(self, argv):
        if urlparse(argv.output).scheme:
            return self._build_context_remote(argv)
        return self._build_context_local(argv)

    def _build_context_remote(self, argv):
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

    def _build_context_local(self, argv):
        outdir = argv.output
        study_id = self.study_id

        context = {
            "study_id": study_id,
            "outdir": outdir,
            "dae_db_dir": self.gpf_instance.dae_db_dir,
        }

        verbose = ""
        if argv.verbose > 0:
            verbose = f"-{'V'*argv.verbose}"

        if argv.genotype_storage:
            context["genotype_storage"] = argv.genotype_storage
        if argv.partition_description:
            context["partition_description"] = argv.partition_description

        pedigree_params_dict = self.families_loader.build_arguments_dict()
        pedigree_params = self.families_loader.build_cli_arguments(
            pedigree_params_dict)
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
            variants_context = {}
            if "target_chromosomes" in argv and \
                    argv.target_chromosomes is not None:
                target_chromosomes = argv.target_chromosomes
            else:
                target_chromosomes = variants_loader.chromosomes

            variants_targets = self.partition_helper.generate_variants_targets(
                target_chromosomes
            )

            variants_context["bins"] = list(variants_targets.keys())
            variants_context["variants"] = " ".join(
                [
                    os.path.abspath(fn)
                    for fn in variants_loader.variants_filenames
                ])
            variants_params_dict = variants_loader.build_arguments_dict()
            variants_context["params"] = variants_loader.build_cli_arguments(
                variants_params_dict)
            variants_context["verbose"] = verbose

            context["variants"][prefix] = variants_context

        context["mirror_of"] = {}
        if self.gpf_instance.dae_config.mirror_of:
            rsync_helper = RsyncHelpers(
                self.gpf_instance.dae_config.mirror_of)
            context["mirror_of"]["location"] = rsync_helper.rsync_remote
            context["mirror_of"]["path"] = rsync_helper.parsed_remote.path
            context["mirror_of"]["netloc"] = rsync_helper.parsed_remote.netloc

        return context

    def generate_study_config(self, argv):
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
                argv.study_config
            )
            config_dict = recursive_dict_update(study_config_dict, config_dict)

        config_builder = StudyConfigBuilder(config_dict)
        config = config_builder.build_config()
        with fsspec.open(os.path.join(
                dirname, f"{self.study_id}.conf"), "w") as outfile:
            outfile.write(config)

    @classmethod
    def cli_arguments_parser(cls, gpf_instance):
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
            "If none specified, the output directory is used"
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
    def main(argv=None, gpf_instance=None):
        """Construct and run the importer based on CLI arguments.

        Main function called from CLI tools.
        """
        if gpf_instance is None:
            try:
                # pylint: disable=import-outside-toplevel
                from dae.gpf_instance.gpf_instance import GPFInstance
                gpf_instance = GPFInstance()
            except Exception:  # pylint: disable=broad-except
                logger.warning("GPF not configured properly...", exc_info=True)

        parser = BatchImporter.cli_arguments_parser(gpf_instance)
        argv = parser.parse_args(argv or sys.argv[1:])

        if argv.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif argv.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif argv.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

        importer = BatchImporter(gpf_instance)
        importer.build(argv)
        importer.generate_instructions(argv)
        importer.generate_study_config(argv)


class Variants2ParquetTool:
    """Tool for importing variants into parquet dataset."""

    VARIANTS_LOADER_CLASS: Optional[Callable[..., VariantsLoader]] = None
    VARIANTS_TOOL: Optional[str] = None
    VARIANTS_FREQUENCIES: bool = False

    BUCKET_INDEX_DEFAULT = 1000

    @classmethod
    def cli_arguments_parser(cls, _gpf_instance):
        """Parse CLI arguments."""
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
    def main(cls, argv=None, gpf_instance=None):
        """Construct and run importer to transform variants into parquet.

        Called from CLI tools.
        """
        if gpf_instance is None:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            gpf_instance = GPFInstance()

        parser = cls.cli_arguments_parser(gpf_instance)

        argv = parser.parse_args(argv or sys.argv[1:])
        if argv.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif argv.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif argv.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

        cls.run(argv, gpf_instance)

    @classmethod
    def run(cls, argv, gpf_instance=None):
        """Run actual variants import into parquet dataset."""
        if gpf_instance is None:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            gpf_instance = GPFInstance()

        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(
            families_filename, **families_params
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
                logger.info(
                    "resetting regions (rb: %s): %s", argv.region_bin, regions)
                variants_loader.reset_regions(regions)

        elif argv.regions is not None:
            regions = argv.regions
            logger.info("resetting regions (region): %s", regions)
            variants_loader.reset_regions(regions)

        variants_loader = cls._build_variants_loader_pipeline(
            gpf_instance, argv, variants_loader
        )

        logger.debug("argv.rows: %s", argv.rows)

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket_index,
            rows=argv.rows,
        )

    @classmethod
    def _build_variants_loader_pipeline(
            cls, gpf_instance, argv, variants_loader):

        effect_annotator = construct_import_effect_annotator(gpf_instance)

        variants_loader = EffectAnnotationDecorator(
            variants_loader, effect_annotator)

        annotation_pipeline = construct_import_annotation_pipeline(
            gpf_instance, annotation_configfile=argv.annotation_config,
        )

        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )

        return variants_loader

    @classmethod
    def _load_variants(cls, argv, families, gpf_instance):
        if cls.VARIANTS_LOADER_CLASS is None:
            raise ValueError("VARIANTS_LOADER_CLASS not set")

        variants_filenames, variants_params = \
            cls.VARIANTS_LOADER_CLASS.parse_cli_arguments(argv)

        # pylint: disable=not-callable
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


class DatasetHelpers:
    """Helper class for work with studies in impala genotype storage."""

    def __init__(self, gpf_instance=None):
        if gpf_instance is None:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            self.gpf_instance = GPFInstance()
        else:
            self.gpf_instance = gpf_instance

    def find_genotype_data_config_file(self, dataset_id):
        """Find and return config filename for a dataset."""
        config = self.gpf_instance.get_genotype_data_config(dataset_id)
        if config is None:
            # pylint: disable=protected-access
            self.gpf_instance._variants_db.reload()
            config = self.gpf_instance.get_genotype_data_config(dataset_id)
            if config is None:
                return None

        assert config is not None, dataset_id

        conf_dir = config.conf_dir

        result = glob.glob(os.path.join(conf_dir, "*.conf"))
        assert len(result) == 1, \
            f"unexpected number of config files in {conf_dir}"
        config_file = result[0]
        assert os.path.exists(config_file)
        return config_file

    def find_genotype_data_config(self, dataset_id):
        """Find and return configuration of a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            return None
        with open(config_file, "r") as infile:
            short_config = toml.load(infile)
            short_config = Box(short_config)
        return short_config

    def get_genotype_storage(self, dataset_id):
        """Find the genotype storage that stores a dataset."""
        config = self.find_genotype_data_config(dataset_id)
        if config is None:
            return None
        gpf_instance = self.gpf_instance
        genotype_storage = gpf_instance \
            .genotype_storage_db \
            .get_genotype_storage(
                config.genotype_storage.id)
        return genotype_storage

    def is_impala_genotype_storage(self, dataset_id):
        """Check if genotype storage is an impala genotype storage."""
        genotype_storage = self.get_genotype_storage(dataset_id)
        return "impala" in genotype_storage.get_storage_type()

    def check_dataset_hdfs_directories(self, genotype_storage, dataset_id):
        """Check if a dataset HDFS directories are OK.

        Works only for impala genotype storage.
        """
        # pylint: disable=too-many-return-statements
        logger.info(
            "genotype storage of study %s should be impala: %s",
            dataset_id, genotype_storage.get_storage_type())
        if "impala" not in genotype_storage.get_storage_type():
            return None

        hdfs_helpers = genotype_storage.hdfs_helpers
        study_dir = genotype_storage.default_hdfs_study_path(dataset_id)

        logger.info(
            "study hdfs dir %s should exists: %s",
            study_dir, hdfs_helpers.exists(study_dir))
        logger.info(
            "study hdfs dir %s should be a directory: %s",
            study_dir, hdfs_helpers.isdir(study_dir))

        if not hdfs_helpers.exists(study_dir) or \
                not hdfs_helpers.isdir(study_dir):
            return None

        pedigree_dir = os.path.join(study_dir, "pedigree")
        logger.info(
            "pedigree hdfs dir %s should exists: %s",
            pedigree_dir, hdfs_helpers.exists(pedigree_dir))
        logger.info(
            "pedigree hdfs dir %s should be a directory: %s",
            pedigree_dir, hdfs_helpers.isdir(pedigree_dir))

        if not hdfs_helpers.exists(pedigree_dir) or \
                not hdfs_helpers.isdir(pedigree_dir):
            return None

        pedigree_file = os.path.join(pedigree_dir, "pedigree.parquet")
        logger.info(
            "pedigree hdfs file %s should exists: %s",
            pedigree_file, hdfs_helpers.exists(pedigree_file))
        logger.info(
            "pedigree hdfs file %s should be a file: %s",
            pedigree_file, hdfs_helpers.isfile(pedigree_file))

        if not hdfs_helpers.exists(pedigree_file) or \
                not hdfs_helpers.isfile(pedigree_file):
            return None
        config = self.find_genotype_data_config(dataset_id)
        if config is None:
            return True

        variants_table = config.genotype_storage.tables.variants
        if variants_table is None:
            logger.info(
                "dataset %s does not have variants; skipping checks for "
                "variants directory...", dataset_id)
        else:
            variants_dir = os.path.join(study_dir, "variants")
            logger.info(
                "variants hdfs dir %s should exists: %s",
                variants_dir, hdfs_helpers.exists(variants_dir))
            logger.info(
                "variants hdfs dir %s should be a directory: %s",
                variants_dir, hdfs_helpers.isdir(variants_dir))
            if not hdfs_helpers.exists(variants_dir) or \
                    not hdfs_helpers.isdir(variants_dir):
                return None

        return True

    def check_dataset_rename_hdfs_directory(self, old_id, new_id):
        """Check if it is OK to rename an HDFS directory for a dataset.

        Works for impala genotype storage.
        """
        genotype_storage = self.get_genotype_storage(old_id)
        if not self.check_dataset_hdfs_directories(genotype_storage, old_id):
            return (None, None)

        hdfs_helpers = genotype_storage.hdfs_helpers

        source_dir = genotype_storage.default_hdfs_study_path(old_id)
        dest_dir = genotype_storage.default_hdfs_study_path(new_id)

        logger.info(
            "source hdfs dir %s should exists: %s",
            source_dir, hdfs_helpers.exists(source_dir))

        logger.info(
            "source hdfs dir %s should be a directory: %s",
            source_dir, hdfs_helpers.isdir(source_dir))

        logger.info(
            "destination hdfs dir %s should not exists: %s",
            dest_dir, not hdfs_helpers.exists(dest_dir))

        if hdfs_helpers.exists(source_dir) and \
                hdfs_helpers.isdir(source_dir) and  \
                not hdfs_helpers.exists(dest_dir):
            return (source_dir, dest_dir)

        return (None, None)

    def dataset_rename_hdfs_directory(self, old_id, new_id, dry_run=None):
        """Rename dataset HDFS directory."""
        source_dir, dest_dir = \
            self.check_dataset_rename_hdfs_directory(old_id, new_id)
        if not dry_run:
            assert (source_dir is not None) and (dest_dir is not None), (
                old_id, new_id)

        genotype_storage = self.get_genotype_storage(old_id)
        hdfs_helpers = genotype_storage.hdfs_helpers

        logger.info("going to rename %s to %s", source_dir, dest_dir)
        if not dry_run:
            hdfs_helpers.rename(source_dir, dest_dir)

    def dataset_remove_hdfs_directory(self, dataset_id, dry_run=None):
        """Remove dataset HDFS directory."""
        genotype_storage = self.get_genotype_storage(dataset_id)
        assert self.check_dataset_hdfs_directories(
            genotype_storage, dataset_id)

        hdfs_helpers = genotype_storage.hdfs_helpers

        study_dir = genotype_storage.default_hdfs_study_path(dataset_id)

        logger.info("going to remove HDFS directory: %s", study_dir)
        if not dry_run:
            hdfs_helpers.delete(study_dir, recursive=True)

    def dataset_recreate_impala_tables(self, old_id, new_id, dry_run=None):
        """Recreate impala tables for a dataset."""
        genotype_storage = self.get_genotype_storage(old_id)

        assert genotype_storage.get_storage_type() == "impala"
        if not dry_run:
            assert self.check_dataset_hdfs_directories(
                genotype_storage, new_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        new_hdfs_pedigree = genotype_storage \
            .default_pedigree_hdfs_filename(new_id)
        new_hdfs_pedigree = os.path.dirname(new_hdfs_pedigree)
        # pylint: disable=protected-access
        new_pedigree_table = genotype_storage._construct_pedigree_table(new_id)

        config = self.find_genotype_data_config(old_id)

        pedigree_table = config.genotype_storage.tables.pedigree

        logger.info(
            "going to recreate pedigree table %s from %s",
            new_pedigree_table, new_hdfs_pedigree)
        if not dry_run:
            impala_helpers.recreate_table(
                impala_db, pedigree_table,
                new_pedigree_table, new_hdfs_pedigree)

        variants_table = config.genotype_storage.tables.variants
        new_variants_table = None

        if variants_table is not None:
            new_hdfs_variants = genotype_storage \
                .default_variants_hdfs_dirname(new_id)

            # pylint: disable=protected-access
            new_variants_table = genotype_storage \
                ._construct_variants_table(new_id)

            logger.info(
                "going to recreate variants table %s from %s",
                new_variants_table, new_hdfs_variants)

            if not dry_run:
                impala_helpers.recreate_table(
                    impala_db, variants_table,
                    new_variants_table, new_hdfs_variants)

        return new_pedigree_table, new_variants_table

    def dataset_drop_impala_tables(self, dataset_id, dry_run=None):
        """Drop impala tables for a dataset."""
        assert self.check_dataset_impala_tables(dataset_id)

        genotype_storage = self.get_genotype_storage(dataset_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        config = self.find_genotype_data_config(dataset_id)

        pedigree_table = config.genotype_storage.tables.pedigree
        logger.info(
            "going to drop pedigree impala table %s.%s",
            impala_db, pedigree_table)
        if not dry_run:
            impala_helpers.drop_table(
                impala_db, pedigree_table)

        variants_table = config.genotype_storage.tables.variants
        if variants_table is not None:
            logger.info(
                "going to drop variants impala table %s.%s",
                impala_db, pedigree_table)
            if not dry_run:
                impala_helpers.drop_table(
                    impala_db, variants_table)

    def check_dataset_impala_tables(self, dataset_id):
        """Check if impala tables for a dataset are OK."""
        genotype_storage = self.get_genotype_storage(dataset_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        config = self.find_genotype_data_config(dataset_id)

        pedigree_table = config.genotype_storage.tables.pedigree

        logger.info(
            "impala pedigree table %s.%s should exists: %s",
            impala_db, pedigree_table,
            impala_helpers.check_table(impala_db, pedigree_table))

        if not impala_helpers.check_table(impala_db, pedigree_table):
            return None

        create_statement = impala_helpers.get_table_create_statement(
            impala_db, pedigree_table)

        logger.info(
            "pedigree table %s.%s should be external table: "
            "'CREATE EXTERNAL TABLE' in %s",
            impala_db, pedigree_table, create_statement)
        if "CREATE EXTERNAL TABLE" not in create_statement:
            return None

        variants_table = config.genotype_storage.tables.variants
        if variants_table is None:
            logger.info(
                "dataset %s has no variants; skipping checks for variants "
                "table", dataset_id)
        else:
            logger.info(
                "impala variants table %s.%s should exists: %s",
                impala_db, variants_table,
                impala_helpers.check_table(impala_db, variants_table)
            )
            if not impala_helpers.check_table(impala_db, variants_table):
                return None

            create_statement = impala_helpers.get_table_create_statement(
                impala_db, variants_table)

            logger.info(
                "variants table %s.%s should be external table: "
                "'CREATE EXTERNAL TABLE' in %s",
                impala_db, variants_table, create_statement
            )
            if "CREATE EXTERNAL TABLE" not in create_statement:
                return None

        return True

    def rename_study_config(
            self, dataset_id, new_id, config_content, dry_run=None):
        """Rename study config for a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        logger.info("going to disable config file %s", config_file)
        if not dry_run:
            os.rename(config_file, f"{config_file}_bak")

        config_dirname = os.path.dirname(config_file)
        new_dirname = os.path.join(os.path.dirname(config_dirname), new_id)
        logger.info(
            "going to rename config directory %s to %s",
            config_dirname, new_dirname)
        if not dry_run:
            os.rename(config_dirname, new_dirname)

        new_config_file = os.path.join(new_dirname, f"{new_id}.conf")

        logger.info("going to create a new config file %s", new_config_file)
        if not dry_run:
            with open(new_config_file, "wt") as outfile:
                content = toml.dumps(config_content)
                outfile.write(content)

    def remove_study_config(self, dataset_id):
        config_file = self.find_genotype_data_config_file(dataset_id)
        config_dir = os.path.dirname(config_file)

        shutil.rmtree(config_dir)

    def disable_study_config(self, dataset_id, dry_run=None):
        """Disable dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        config_dir = os.path.dirname(config_file)

        logger.info("going to disable study_config %s", config_file)

        if not dry_run:
            os.rename(config_file, f"{config_file}_bak")
            os.rename(config_dir, f"{config_dir}_bak")
