import os
import pytest

from dae.backends.impala.import_commons import MakefileGenerator


@pytest.fixture
def cli_parse(gpf_instance_2013):

    def parser(argv):
        parser = MakefileGenerator.cli_arguments_parser(gpf_instance_2013)
        return parser.parse_args(argv)

    return parser


@pytest.fixture
def generator(gpf_instance_2013):
    result = MakefileGenerator(gpf_instance_2013)
    assert result is not None
    return result


def test_makefile_generator_simple(
        fixture_dirname, cli_parse, generator, temp_dirname):
    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = cli_parse([
        '-o', temp_dirname,
        f'{prefix}.ped',
        '--vcf-files', f'{prefix}.vcf.gz',
        '--gs', 'genotype_impala',
    ])

    generator.build(argv)

    assert generator.study_id == 'effects_trio'
    assert generator.vcf_loader is not None
    assert generator.denovo_loader is None
    assert generator.dae_loader is None


def test_makefile_generator_multivcf_simple(
        fixture_dirname, cli_parse, generator, temp_dirname):

    vcf_file1 = fixture_dirname('multi_vcf/multivcf_missing1.vcf.gz')
    vcf_file2 = fixture_dirname('multi_vcf/multivcf_missing2.vcf.gz')
    ped_file = fixture_dirname('multi_vcf/multivcf.ped')

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = cli_parse([
        '-o', temp_dirname,
        ped_file,
        '--vcf-files', vcf_file1, vcf_file2,
        '--pd', partition_description,
        '--gs', 'genotype_impala',
    ])

    generator.build(argv)

    assert generator.study_id == 'multivcf'
    assert generator.partition_helper is not None
    assert generator.vcf_loader is not None
    assert generator.denovo_loader is None
    assert generator.dae_loader is None


def test_makefile_generator_denovo_and_dae(
        fixture_dirname, cli_parse, generator, temp_dirname):

    denovo_file = fixture_dirname('dae_denovo/denovo.txt')
    dae_file = fixture_dirname('dae_transmitted/transmission.txt.gz')
    ped_file = fixture_dirname('dae_denovo/denovo_families.ped')

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = cli_parse([
        '-o', temp_dirname,
        ped_file,
        '--id', 'dae_denovo_and_transmitted',
        '--denovo-file', denovo_file,
        '--dae-summary-file', dae_file,
        '--pd', partition_description,
        '--gs', 'genotype_impala',
    ])

    generator.build(argv)

    assert generator.study_id == 'dae_denovo_and_transmitted'
    assert generator.partition_helper is not None
    assert generator.vcf_loader is None
    assert generator.denovo_loader is not None
    assert generator.dae_loader is not None

    generator.generate_makefile(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)
