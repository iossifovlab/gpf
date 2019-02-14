import pytest

from box import Box

from configurable_entities.configuration import DAEConfig
from tools.dae2parquet import parse_cli_arguments, dae_build_denovo, \
    dae_build_transmitted, dae_build_makefile

from backends.configure import Configure
from annotation.tools.file_io_parquet import ParquetReader

from RegionOperations import Region


def test_dae2parquet_denovo(
        dae_denovo_config, annotation_pipeline_config,
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'denovo',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '-f', 'simple',
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
    ]
    dae_config = DAEConfig()

    argv = parse_cli_arguments(dae_config, argv)

    assert argv is not None
    assert argv.type == 'denovo'

    dae_build_denovo(
        dae_config, argv, defaults={
            'scores_dirname': annotation_scores_dirname,
        })

    parquet_summary = Configure.from_prefix_parquet(
        temp_dirname).parquet.summary_variant
    summary = ParquetReader(Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'


def test_dae2parquet_transmitted(
        dae_transmitted_config, annotation_pipeline_config,
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'dae',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '-f', 'simple',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
    ]
    dae_config = DAEConfig()

    argv = parse_cli_arguments(dae_config, argv)

    assert argv is not None
    assert argv.type == 'dae'

    dae_build_transmitted(
        dae_config, argv, defaults={
            'scores_dirname': annotation_scores_dirname,
        })

    parquet_summary = Configure.from_prefix_parquet(
        temp_dirname).parquet.summary_variant
    summary = ParquetReader(Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'


def test_dae2parquet_make(
        dae_transmitted_config, annotation_pipeline_config,
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'make',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '-f', 'simple',
        '-l', '100000000',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
    ]
    dae_config = DAEConfig()

    argv = parse_cli_arguments(dae_config, argv)

    assert argv is not None
    assert argv.type == 'make'

    dae_build_makefile(
        dae_config, argv)


@pytest.fixture
def dae_iossifov2014_thrift(
        dae_iossifov2014_config,
        annotation_scores_dirname, temp_dirname, parquet_thrift):

    def build(annotation_config):
        config = dae_iossifov2014_config
        argv = [
            'denovo',
            '--annotation', annotation_config,
            '-o', temp_dirname,
            '-f', 'simple',
            config.family_filename,
            config.denovo_filename,
        ]
        dae_config = DAEConfig()

        argv = parse_cli_arguments(dae_config, argv)

        assert argv is not None
        assert argv.type == 'denovo'

        defaults = {
                'scores_dirname': annotation_scores_dirname,
        }
        defaults.update(DAEConfig().annotation_defaults)

        dae_build_denovo(
            dae_config, argv, defaults=defaults)

        parquet_config = Configure.from_prefix_parquet(
            temp_dirname).parquet
        assert parquet_config is not None

        return parquet_thrift(parquet_config)

    return build


@pytest.mark.parametrize("annotation_config", [
    'annotation_pipeline_config',
    # 'annotation_pipeline_default_config'
])
@pytest.mark.parametrize("region,cshl_location,effect_type", [
    (Region('15', 80137553, 80137553), '15:80137554', 'noEnd'),
    (Region('12', 116418553, 116418553), '12:116418554', 'splice-site'),
    (Region('3', 56627767, 56627767), '3:56627768', 'splice-site'),
    (Region('3', 195475903, 195475903), '3:195475904', 'splice-site'),
    (Region('21', 38877891, 38877891), '21:38877892', 'splice-site'),
    (Region('15', 43694048, 43694048), '15:43694049', 'splice-site'),
    (Region('12', 93792632, 93792632), '12:93792633', 'splice-site'),
    (Region('4', 83276456, 83276456), '4:83276456', 'splice-site'),
    (Region('3', 195966607, 195966607), '3:195966608', 'splice-site'),
    (Region('3', 97611837, 97611837), '3:97611838', 'splice-site'),
    (Region('15', 31776803, 31776803), '15:31776804', 'no-frame-shift'),
    (Region('3', 151176416, 151176416), '3:151176417', 'no-frame-shift'),
])
def test_dae2parquet_iossifov2014_variant_coordinates(
        dae_iossifov2014_thrift, fixture_select,
        annotation_config,
        region, cshl_location, effect_type):

    assert dae_iossifov2014_thrift is not None
    annotation_pipeline_config = fixture_select(annotation_config)
    fvars = dae_iossifov2014_thrift(annotation_pipeline_config)

    vs = fvars.query_variants(
        regions=[region]
    )
    vs = list(vs)
    print(vs)
    assert len(vs) == 1
    v = vs[0]
    assert len(v.alt_alleles) == 1
    aa = v.alt_alleles[0]

    assert aa.chromosome == region.chrom
    assert aa.position == region.start
    assert aa.cshl_location == cshl_location
    assert aa.effect.worst == effect_type
