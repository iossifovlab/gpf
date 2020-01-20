import os
import sys
import argparse

from math import ceil
from collections import defaultdict

from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator
from dae.utils.dict_utils import recursive_dict_update

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator, \
    AlleleFrequencyDecorator, FamiliesGenotypesDecorator
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescriptor, NoPartitionDescriptor


def save_study_config(dae_config, study_id, study_config):
    dirname = os.path.join(dae_config.studies_db.dir, study_id)
    filename = os.path.join(dirname, '{}.conf'.format(study_id))

    if os.path.exists(filename):
        print('configuration file already exists:', filename)
        print('skipping generation of default study config for:', study_id)
        return

    os.makedirs(dirname, exist_ok=True)
    with open(filename, 'w') as outfile:
        outfile.write(study_config)


def construct_import_annotation_pipeline(
        gpf_instance,
        annotation_configfile=None, defaults=None):

    if defaults is None:
        defaults = {}
    if annotation_configfile is not None:
        config_filename = annotation_configfile
    else:
        config_filename = gpf_instance.dae_config.annotation.conf_file

    assert os.path.exists(config_filename), config_filename
    options = {
        "vcf": True,
        'c': 'chrom',
        'p': 'position',
        'r': 'reference',
        'a': 'alternative',
    }
    options = Box(options, default_box=True, default_box_attr=None)

    annotation_defaults = {
        'values': gpf_instance.dae_config.annotation_defaults
    }
    annotation_defaults = recursive_dict_update(annotation_defaults, defaults)

    pipeline = PipelineAnnotator.build(
        options, config_filename,
        gpf_instance.dae_config.dae_data_dir,
        gpf_instance.genomes_db,
        defaults=annotation_defaults)
    return pipeline


class MakefileGenerator:

    def __init__(self, partition_descriptor, genome):
        self.genome = genome
        self.partition_descriptor = partition_descriptor
        self.chromosome_lengths = dict(self.genome.get_all_chr_lengths())

    def region_bins_count(self, chrom):
        result = ceil(
            self.chromosome_lengths[chrom] /
            self.partition_descriptor.region_length)
        return result

    def generate_chrom_targets(self, chrom):
        target = chrom
        if chrom not in self.partition_descriptor.chromosomes:
            target = 'other'
        region_bins_count = self.region_bins_count(chrom)

        if region_bins_count == 1:
            return [(f'{target}_0', chrom)]
        result = []
        for region_index in range(region_bins_count):
            start = region_index * self.partition_descriptor.region_length + 1
            end = (region_index + 1) * self.partition_descriptor.region_length
            if end > self.chromosome_lengths[chrom]:
                end = self.chromosome_lengths[chrom]
            result.append(
                (f'{target}_{region_index}', f'{chrom}:{start}-{end}')
            )
        return result

    def generate_variants_targets(self, target_chromosomes):
        if len(self.partition_descriptor.chromosomes) == 0:
            return {
                'none': [self.partition_descriptor.output]
            }

        targets = defaultdict(list)

        for chrom in target_chromosomes:
            if chrom not in self.chromosome_lengths:
                print(
                    f"WARNING: contig {chrom} not found in specified genome",
                    file=sys.stderr)
                continue

            assert chrom in self.chromosome_lengths, \
                (chrom, self.chromosome_lengths)
            region_targets = self.generate_chrom_targets(chrom)
            for target, region in region_targets:
                targets[target].append(region)
        return targets

    def generate_variants_make(
            self, command, target_chromosomes, output=sys.stdout):
        variants_targets = self.generate_variants_targets(target_chromosomes)

        all_bins = ' '.join(list(variants_targets.keys()))

        print(
            f'all_bins={all_bins}\n',
            file=output)
        print(
            f'all_bins_flags=$(foreach bin, $(all_bins), $(bin).flag)\n',
            file=output)
        print(
            f'\n'
            f'variants: $(all_bins_flags)\n',
            file=output)
        print(
            f'\n'
            f'%.flag:\n'
            f'\t{command} --rb $* && touch $@\n',
            file=output
        )

    def generate_pedigree_make(self, command, output=sys.stdout):
        print(
            f'pedigree: ped.flag\n',
            file=output)
        print(
            f'ped.flag:\n'
            f'\t{command} && touch $@',
            file=output)

    def generate_impala_load_make(self, command, output=sys.stdout):
        print(
            f'impala: load.flag\n',
            file=output)
        print(
            f'load.flag:\n'
            f'\t{command} && touch $@',
            file=output)

    def generate_makefile(
            self, families_command, variants_command, load_command,
            target_chromosomes,
            output=sys.stdout):

        print(
            f'all: pedigree variants\n',
            file=output)

        self.generate_variants_make(
            variants_command, target_chromosomes, output=output)
        self.generate_pedigree_make(
            families_command, output=output)
        self.generate_impala_load_make(
            load_command, output=output)


class Variants2ParquetTool:

    VARIANTS_LOADER_CLASS = None
    VARIANTS_TOOL = None
    VARIANTS_FREQUENCIES = False
    VARIANTS_GENOTYPES = True

    BUCKET_INDEX_DEFAULT = 1000

    @classmethod
    def cli_common_arguments(cls, gpf_instance, parser):

        FamiliesLoader.cli_arguments(parser)
        cls.VARIANTS_LOADER_CLASS.cli_arguments(parser)

        parser.add_argument(
            '--study-id', type=str, default=None,
            dest='study_id', metavar='<study id>',
            help='Study ID. '
            'If none specified, the basename of families filename is used to '
            'construct study id [default: basename(families filename)]'
        )

        parser.add_argument(
            '-o', '--out', type=str, default='.',
            dest='output', metavar='<output directory>',
            help='output directory. '
            'If none specified, current directory is used '
            '[default: %(default)s]'
        )

        parser.add_argument(
            '--pd', '--partition-description',
            type=str, default=None,
            dest='partition_description',
            help='Path to a config file containing the partition description'
        )

        parser.add_argument(
            '--rows', type=int, default=100000,
            dest='rows',
            help='Amount of allele rows to write at once'
        )

        parser.add_argument(
            '--annotation-config', type=str, default=None,
            help='Path to an annotation config file to use when annotating'
        )

    @classmethod
    def cli_arguments(cls, gpf_instance):
        parser = argparse.ArgumentParser(
            description='Convert variants file to parquet',
            conflict_handler='resolve',
            formatter_class=argparse.RawDescriptionHelpFormatter)

        subparsers = parser.add_subparsers(
            dest='type',
            title='subcommands',
            description='choose what type of data to convert',
            help='variants import or make generation for variants import')

        # variants subcommand
        variants_parser = subparsers.add_parser('variants')
        cls.cli_common_arguments(gpf_instance, variants_parser)
        variants_parser.add_argument(
            '-b', '--bucket-index',
            type=int, default=cls.BUCKET_INDEX_DEFAULT,
            dest='bucket_index', metavar='bucket index',
            help='bucket index [default: %(default)s]'
        )

        variants_parser.add_argument(
            '--region-bin', '--rb', type=str, default=None,
            dest='region_bin', metavar='region bin',
            help='region bin [default: %(default)s] '
            'ex. X_0 '
            'If both `--regions` and `--region-bin` options are specified, '
            'the `--region-bin` option takes precedence'
        )

        variants_parser.add_argument(
            '--regions', type=str,
            dest='regions', metavar='region',
            default=None, nargs='+',
            help='region to convert [default: %(default)s] '
            'ex. chr1:1-10000. '
            'If both `--regions` and `--region-bin` options are specified, '
            'the `--region-bin` option takes precedence'
        )

        # make subcommand
        make_parser = subparsers.add_parser('make')
        cls.cli_common_arguments(gpf_instance, make_parser)
        default_genotype_storage_id = \
            gpf_instance.dae_config.\
            get('genotype_storage', {}).\
            get('default', None)

        make_parser.add_argument(
            '--genotype-storage', '--gs',
            type=str,
            dest='genotype_storage',
            default=default_genotype_storage_id,
            help='Genotype Storage which will be used for import '
            '[default: %(default)s]',
        )

        return parser

    @classmethod
    def build_make_variants_command(
            cls, study_id, argv, families_loader, variants_loader):
        families_params = FamiliesLoader.build_cli_arguments(
            families_loader.params)
        families_filename = families_loader.filename
        families_filename = os.path.abspath(families_filename)

        variants_params = cls.VARIANTS_LOADER_CLASS.build_cli_arguments(
            variants_loader.params)
        variants_filenames = [
            os.path.abspath(fn) for fn in variants_loader.filenames
        ]
        variants_filenames = ' '.join(variants_filenames)

        command = [
            f'{cls.VARIANTS_TOOL} variants',
            f'{families_params} {families_filename}',
            f'{variants_params} {variants_filenames}',
            f'--study-id {study_id}',
            f'-o {study_id}_variants.parquet'
        ]
        if argv.partition_description is not None:
            pd = os.path.abspath(argv.partition_description)
            command.append(f'--pd {pd}')

        return ' '.join(command)

    @classmethod
    def build_make_families_command(
            cls, study_id, argv, families_loader):
        families_params = FamiliesLoader.build_cli_arguments(
            families_loader.params)
        families_filename = families_loader.filename
        families_filename = os.path.abspath(families_filename)

        command = [
            f'ped2parquet.py {families_params} {families_filename}',
            f'--study-id {study_id}',
            f'-o {study_id}_pedigree.parquet'
        ]
        if argv.partition_description is not None:
            pd = os.path.abspath(argv.partition_description)
            command.append(f'--pd {pd}')

        return ' '.join(command)

    @classmethod
    def build_make_impala_load_command(
            cls, study_id, argv):
        output = argv.output
        if output is None:
            output = '.'
        output = os.path.abspath(output)

        command = [
            f'impala_parquet_loader.py {study_id}',
            os.path.join(output, f'{study_id}_pedigree.parquet'),
            os.path.join(output, f'{study_id}_variants.parquet'),
        ]
        if argv.genotype_storage is not None:
            command.append(
                f'--gs {argv.genotype_storage}'
            )

        return ' '.join(command)

    @classmethod
    def main(
            cls, argv=sys.argv[1:],
            gpf_instance=None,
            annotation_defaults={}):
        print("argv:", argv)

        if gpf_instance is None:
            gpf_instance = GPFInstance()

        parser = cls.cli_arguments(gpf_instance)
        argv = parser.parse_args(argv)

        families_filename, families_params = \
            FamiliesLoader.parse_cli_arguments(argv)
        families_loader = FamiliesLoader(
            families_filename, params=families_params)
        families = families_loader.load()

        variants_filenames, variants_params = \
            cls.VARIANTS_LOADER_CLASS.parse_cli_arguments(argv)
        variants_loader = cls.VARIANTS_LOADER_CLASS(
            families, variants_filenames,
            params=variants_params,
            genome=gpf_instance.genomes_db.get_genome())

        if argv.partition_description is not None:
            partition_description = ParquetPartitionDescriptor.from_config(
                argv.partition_description,
                root_dirname=argv.output
            )
        else:
            partition_description = NoPartitionDescriptor(argv.output)

        generator = MakefileGenerator(
            partition_description,
            gpf_instance.genomes_db.get_genome())
        target_chromosomes = variants_loader.chromosomes
        variants_targets = generator.generate_variants_targets(
            target_chromosomes)

        if argv.study_id is not None:
            study_id = argv.study_id
        else:
            study_id, _ = os.path.splitext(os.path.basename(families_filename))

        if argv.type == 'make':
            dirname = argv.output
            if dirname is None:
                dirname = '.'
            os.makedirs(dirname, exist_ok=True)

            variants_command = cls.build_make_variants_command(
                study_id, argv, families_loader, variants_loader)
            families_command = cls.build_make_families_command(
                study_id, argv, families_loader)
            load_command = cls.build_make_impala_load_command(
                study_id, argv)

            with open(os.path.join(dirname, 'Makefile'), 'wt') as output:
                generator.generate_makefile(
                    families_command, variants_command, load_command,
                    target_chromosomes,
                    output=output
                )

        elif argv.type == 'variants':
            annotation_pipeline = construct_import_annotation_pipeline(
                gpf_instance,
                annotation_configfile=argv.annotation_config,
                defaults=annotation_defaults)

            bucket_index = argv.bucket_index
            if argv.region_bin is not None:
                if argv.region_bin == 'none':
                    pass
                else:
                    assert argv.region_bin in variants_targets, \
                        (argv.region_bin, list(variants_targets.keys()))

                    regions = variants_targets[argv.region_bin]
                    bucket_index = cls.BUCKET_INDEX_DEFAULT + \
                        list(variants_targets.keys()).index(argv.region_bin)
                    print("resetting regions:", regions)
                    variants_loader.reset_regions(regions)

            elif argv.regions is not None:
                regions = argv.regions
                print("resetting regions:", regions)
                variants_loader.reset_regions(regions)

            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )

            if cls.VARIANTS_FREQUENCIES:
                variants_loader = AlleleFrequencyDecorator(variants_loader)

            if cls.VARIANTS_GENOTYPES:
                genome = gpf_instance.genomes_db.get_genome()
                variants_loader = FamiliesGenotypesDecorator(
                    variants_loader, genome)

            ParquetManager.variants_to_parquet_partition(
                variants_loader, partition_description,
                bucket_index=bucket_index,
                rows=argv.rows
            )
