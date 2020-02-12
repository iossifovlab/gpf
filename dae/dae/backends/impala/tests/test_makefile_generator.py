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
    ])

    generator\
        .build_familes_loader(argv) \
        .build_vcf_loaders(argv) \
        .build_study_id(argv) \
        .build_partition_helper(argv)

    assert generator.study_id == 'effects_trio'


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
    ])

    generator\
        .build_familes_loader(argv) \
        .build_vcf_loaders(argv) \
        .build_study_id(argv) \
        .build_partition_helper(argv)

    assert generator.study_id == 'multivcf'
    assert generator.partition_helper is not None
