import pytest
import os
import io

from contextlib import redirect_stdout

from box import Box
from dae.RegionOperations import Region
from dae.pedigrees.family import FamiliesLoader

from dae.pedigrees.family import FamiliesData, PedigreeReader
from dae.backends.impala.loader import ParquetLoader
from dae.tools.dae2parquet import main

from dae.annotation.tools.file_io_parquet import ParquetReader


def test_dae2parquet_denovo(
        dae_denovo_config, annotation_pipeline_default_config,
        temp_dirname,
        genomes_db_2013):

    argv = [
        'denovo',
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
        '--annotation', annotation_pipeline_default_config,
        '--family-format', 'simple',
        '-o', temp_dirname
    ]

    main(argv)

    summary = ParquetReader(Box({
        'infile': os.path.join(temp_dirname, 'variant', 'variants.parquet'),
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    # assert schema['worst_effect'].type_name == 'str'


def test_dae2parquet_transmitted(
        dae_transmitted_config, annotation_pipeline_default_config,
        temp_dirname,
        genomes_db_2013):

    argv = [
        'dae',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        '--annotation', annotation_pipeline_default_config,
        '--family-format', 'simple',
        '-o', temp_dirname
    ]

    main(argv)

    summary = ParquetReader(Box({
        'infile': os.path.join(temp_dirname, 'variant', 'variants.parquet'),
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    # assert schema['worst_effect'].type_name == 'str'


def test_dae2parquet_make(
        dae_transmitted_config, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        genomes_db_2013):

    argv = [
        'make',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        '-f', 'simple',
        '-l', '100000000',
    ]

    f = io.StringIO()
    with redirect_stdout(f):
        main(argv)

    makefile = f.getvalue()
    assert 'all:' in makefile
    assert 'dae2parquet.py dae ' in makefile


def test_dae2parquet_make_partition(
        dae_transmitted_config, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        genomes_db_2013,
        parquet_partition_configuration):

    argv = [
        'make',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        '-f', 'simple',
        '-l', '100000000',
        '--pd', parquet_partition_configuration
    ]

    f = io.StringIO()
    with redirect_stdout(f):
        main(argv)

    makefile = f.getvalue()
    assert 'all:' in makefile
    assert 'dae2parquet.py dae ' in makefile
    assert '1_8:' in makefile
    assert '--region 1:800001-900000'
    assert '1_0:' in makefile
    assert '--region 1:1-100000'


@pytest.mark.xfail(reason='ParquetLoader is broken')
def test_dae2parquet_dae_partition(
        dae_transmitted_config, annotation_pipeline_default_config,
        temp_dirname, parquet_partition_configuration):

    argv = [
        'dae',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        '--annotation', annotation_pipeline_default_config,
        '--family-format', 'simple',
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration
    ]

    main(argv)

    generated_conf = os.path.join(temp_dirname, '_PARTITION_DESCRIPTION')
    assert os.path.exists(generated_conf)

    ped_df = PedigreeReader.load_simple_family_file(
        dae_transmitted_config.family_filename)
    families = FamiliesData.from_pedigree_df(ped_df)

    pl = ParquetLoader(families, generated_conf)
    summary_genotypes = []
    for summary, gt in pl.summary_genotypes_iterator():
        summary_genotypes.append((summary, gt))

    assert len(summary_genotypes) == 15
    assert all(sgt[0].get_attribute('region_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('family_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('coding_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('frequency_bin')[0] is not None
               for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'G' for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'C' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'T' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'A' for sgt in summary_genotypes)


@pytest.mark.xfail(reason='ParquetLoader is broken')
def test_dae2parquet_denovo_partition(
        dae_denovo_config, annotation_pipeline_default_config,
        temp_dirname, parquet_partition_configuration):

    argv = [
        'denovo',
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
        '--annotation', annotation_pipeline_default_config,
        '--family-format', 'simple',
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration
    ]

    main(argv)

    generated_conf = os.path.join(temp_dirname, '_PARTITION_DESCRIPTION')
    assert os.path.exists(generated_conf)

    ped_df = PedigreeReader.load_simple_family_file(
        dae_denovo_config.family_filename)
    families = FamiliesData.from_pedigree_df(ped_df)

    pl = ParquetLoader(families, generated_conf)
    summary_genotypes = []
    for summary, gt in pl.summary_genotypes_iterator():
        print(summary, gt)
        summary_genotypes.append((summary, gt))

    assert len(summary_genotypes) == 9
    assert all(sgt[0].get_attribute('region_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('family_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('coding_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('frequency_bin')[0] is not None
               for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'G' for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'C' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'T' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'A' for sgt in summary_genotypes)


@pytest.mark.parametrize('variants', [
    'iossifov2014_raw_denovo',
    'iossifov2014_impala',
])
@pytest.mark.parametrize('region,cshl_location,effect_type', [
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
        variants,
        iossifov2014_impala, iossifov2014_raw_denovo,
        region, cshl_location, effect_type):

    if variants == 'iossifov2014_impala':
        fvars = iossifov2014_impala
    elif variants == 'iossifov2014_raw_denovo':
        fvars = iossifov2014_raw_denovo
    else:
        assert False, variants

    vs = fvars.query_variants(regions=[region])
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
