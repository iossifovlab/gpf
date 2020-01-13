import os
import pytest
from dae.backends.impala.parquet_io import ParquetPartitionDescription
from dae.tools.ped2parquet import main


def test_partition_descriptor(global_dae_fixtures_dir):
    pd_filename = f'{global_dae_fixtures_dir}/' \
        f'partition_descriptor/partition_description.conf'
    pd = ParquetPartitionDescription.from_config(pd_filename)
    assert pd is not None


@pytest.mark.parametrize('pedigree', [
    ('pedigree_A.ped'),
    ('pedigree_B.ped'),
    ('pedigree_B2.ped'),
    ('pedigree_C.ped'),
])
def test_ped2parquet(pedigree, temp_filename, global_dae_fixtures_dir):
    filename = f'{global_dae_fixtures_dir}/pedigrees/{pedigree}'
    assert os.path.exists(filename)

    argv= [
        filename,
        '-o', temp_filename
    ]

    main(argv)
    assert os.path.exists(temp_filename)


@pytest.mark.parametrize('pedigree', [
    ('pedigree_A.ped'),
    ('pedigree_B.ped'),
    ('pedigree_B2.ped'),
    ('pedigree_C.ped'),
])
def test_ped2parquet_patition(
        pedigree, temp_filename, global_dae_fixtures_dir):
    filename = f'{global_dae_fixtures_dir}/pedigrees/{pedigree}'
    assert os.path.exists(filename)

    pd_filename = f'{global_dae_fixtures_dir}/' \
        f'partition_descriptor/partition_description.conf'

    argv= [
        filename,
        '-o', temp_filename,
        '--pd', pd_filename,
    ]

    main(argv)

    assert os.path.exists(temp_filename)