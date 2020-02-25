import pytest
import os
import glob
import pyarrow.parquet as pq

from dae.RegionOperations import Region

from dae.tools.denovo2parquet import main
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor


def test_denovo2parquet_denovo(
        dae_denovo_config, temp_filename, genomes_db_2013):

    argv = [
        '--ped-file-format', 'simple',
        '-o', temp_filename,
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
    ]

    main(argv)

    assert os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema

    assert 'effect_gene' in schema.names
    assert 'effect_type' in schema.names
    assert 'effect_data' in schema.names


def test_denovo2parquet_denovo_partition(
        fixture_dirname, dae_denovo_config,
        temp_dirname, genomes_db_2013):

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = [
        '--ped-file-format', 'simple',
        '--pd', partition_description,
        '-o', temp_dirname,
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
    ]

    main(argv)

    pd = ParquetPartitionDescriptor.from_config(partition_description)
    file_glob = os.path.join(temp_dirname, pd.generate_file_access_glob())
    partition_files = glob.glob(file_glob)

    assert len(partition_files) == 8
    for file in partition_files:
        assert 'frequency_bin=0' in file


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
def test_denovo2parquet_iossifov2014_variant_coordinates(
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
