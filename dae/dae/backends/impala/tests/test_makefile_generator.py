import pytest

from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.import_commons import Variants2ParquetTool, \
    MakefileGenerator


@pytest.fixture
def cli_parse(gpf_instance_2013):

    def parser(argv):
        Variants2ParquetTool.VARIANTS_LOADER_CLASS = VcfLoader
        parser = Variants2ParquetTool.cli_arguments_parser(gpf_instance_2013)
        return parser.parse_args(argv)

    return parser


@pytest.fixture
def generator(gpf_instance_2013):
    result = MakefileGenerator(
        gpf_instance_2013,
        VcfLoader,
        'my_tool variants'
    )

    assert result is not None
    return result


def test_makefile_generator_simple(
        fixture_dirname, cli_parse, generator, temp_dirname):
    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = cli_parse([
        'make',
        '-o', temp_dirname,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz',
    ])

    generator\
        .build_familes_loader(argv) \
        .build_variants_loaders(argv) \
        .build_study_id(argv) \
        .build_partition_description(argv)

    assert generator.study_id == 'effects_trio'


def test_makefile_generator_multivcf_simple(
        fixture_dirname, cli_parse, generator, temp_dirname):

    vcf_file1 = fixture_dirname('multi_vcf/multivcf_missing1.vcf.gz')
    vcf_file2 = fixture_dirname('multi_vcf/multivcf_missing2.vcf.gz')
    ped_file = fixture_dirname('multi_vcf/multivcf.ped')

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = cli_parse([
        'make',
        '-o', temp_dirname,
        ped_file,
        vcf_file1, vcf_file2,
        '--pd', partition_description,
    ])

    generator\
        .build_familes_loader(argv) \
        .build_variants_loaders(argv) \
        .build_study_id(argv) \
        .build_partition_description(argv)

    assert generator.study_id == 'multivcf'
