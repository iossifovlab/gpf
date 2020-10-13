import os
import sys
import argparse
import time
import logging

from typing import Optional, Any

from math import ceil
from collections import defaultdict

from jinja2 import Template

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

from dae.backends.impala.rsync_helpers import RsyncHelpers

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update


logger = logging.getLogger(__name__)


def save_study_config(dae_config, study_id, study_config, force=False):
    dirname = os.path.join(dae_config.studies_db.dir, study_id)
    filename = os.path.join(dirname, "{}.conf".format(study_id))

    if os.path.exists(filename):
        logger.info(
            f"configuration file already exists: {filename}")
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
            del_chrom_prefix=None):

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


class BatchGenerator:

    def __init__(self):
        pass


class MakefileGenerator(BatchGenerator):

    def __init__(self):
        super(MakefileGenerator, self).__init__()

    def generate(self, context):
        return MakefileGenerator.TEMPLATE.render(context)

    TEMPLATE = Template(
        """\

{%- for prefix, context in variants.items() %}

{{prefix}}_bins={{context.bins|join(" ")}}
{{prefix}}_bins_flags=$(foreach bin, $({{prefix}}_bins), {{prefix}}_$(bin).flag)

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


class SnakefileGenerator(BatchGenerator):

    def __init__(self):
        super(SnakefileGenerator, self).__init__()

    def generate(self, context):
        return SnakefileGenerator.TEMPLATE.render(context)

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
        ped2parquet.py --study-id {{study_id}} \\
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
        {{prefix}}2parquet.py --study-id {{study_id}} \\
            {{pedigree.params}} {input.pedigree} \\
            {{context.params}} {params.variants} \\
{%- if partition_description %}
            --pd {input.partition_description} \\
{%- endif %}
            -o {{variants_output}} \\
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
        ssh {{mirror_of.netloc}} "mkdir -p {{mirror_of.path}}/studies/{{study_id}}"
        rsync -avPHt \\
            --ignore-existing \\
            {{dae_db_dir}}/studies/{{study_id}}/ \\
            {{mirror_of.location}}/studies/{{study_id}}
        '''

{%- endif %}

        """)


class BatchImporter:
    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance

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
        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)

        families_loader = FamiliesLoader(
            families_filename, **families_params
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
        self.variants_loaders["vcf"] = variants_loader
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
        self.variants_loaders["denovo"] = variants_loader
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
        self.variants_loaders["cnv"] = variants_loader
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
        self.variants_loaders["dae"] = variants_loader
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
        dirname = os.path.abspath(dirname)

        os.makedirs(dirname, exist_ok=True)
        os.makedirs(os.path.join(dirname, "logs"), exist_ok=True)
        return dirname

    def generate_instructions(self, argv):
        dirname = self._create_output_directory(argv)
        context = self.build_context(argv)
        if argv.tool == "make":
            generator = MakefileGenerator()
            filename = os.path.join(dirname, "Makefile")
        elif argv.tool == "snakemake":
            generator = SnakefileGenerator()
            filename = os.path.join(dirname, "Snakefile")
        else:
            assert False, f"unexpected tool format: {argv.tool}"

        content = generator.generate(context)

        with open(filename, "w") as outfile:
            outfile.write(content)

    def build_context(self, argv):
        outdir = self._create_output_directory(argv)
        study_id = self.study_id

        context = {
            "study_id": study_id,
            "outdir": outdir,
            "dae_db_dir": self.gpf_instance.dae_db_dir,
        }
        if argv.genotype_storage:
            context["genotype_storage"] = argv.genotype_storage
        if argv.partition_description:
            context["partition_description"] = argv.partition_description

        pedigree_params = FamiliesLoader.build_cli_arguments(
            self.families_loader.params)
        pedigree_pedigree = os.path.abspath(
            self.families_loader.filename)
        pedigree_output = os.path.abspath(os.path.join(
            outdir, f"{study_id}_pedigree", "pedigree.parquet"))
        context["pedigree"] = {
            "pedigree": pedigree_pedigree,
            "params": pedigree_params,
            "output": pedigree_output,
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
            variants_context["params"] = variants_loader.build_cli_arguments(
                variants_loader.params)
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
            config_dict = recursive_dict_update(study_config_dict, config_dict)

        config_builder = StudyConfigBuilder(config_dict)
        config = config_builder.build_config()
        with open(os.path.join(
                dirname, f"{self.study_id}.conf"), "w") as outfile:
            outfile.write(config)

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
    def main(argv=sys.argv[1:], gpf_instance=None):

        if gpf_instance is None:
            gpf_instance = GPFInstance()

        parser = BatchImporter.cli_arguments_parser(gpf_instance)
        argv = parser.parse_args(argv)

        importer = BatchImporter(gpf_instance)
        importer.build(argv)
        importer.generate_instructions(argv)
        importer.generate_study_config(argv)


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
        parser.add_argument('--verbose', '-V', action='count', default=0)

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
        if argv.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif argv.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif argv.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

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
                    f"resetting regions (rb: {argv.region_bin}): {regions}")
                variants_loader.reset_regions(regions)

        elif argv.regions is not None:
            regions = argv.regions
            print("resetting regions (region):", regions)
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
