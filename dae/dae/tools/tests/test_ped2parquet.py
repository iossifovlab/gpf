import os
import pytest

import pyarrow.parquet as pq

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData
from dae.impala_storage.parquet_io import (
    ParquetPartitionDescriptor,
    ParquetManager,
)

from dae.tools.ped2parquet import main


def test_partition_descriptor(global_dae_fixtures_dir):
    pd_filename = (
        f"{global_dae_fixtures_dir}/"
        f"partition_descriptor/partition_description.conf"
    )
    pd = ParquetPartitionDescriptor.from_config(pd_filename)
    assert pd is not None


@pytest.mark.parametrize(
    "pedigree",
    [
        ("pedigree_A.ped"),
        ("pedigree_B.ped"),
        ("pedigree_B2.ped"),
        ("pedigree_C.ped"),
    ],
)
def test_ped2parquet(pedigree, temp_filename, global_dae_fixtures_dir):
    filename = f"{global_dae_fixtures_dir}/pedigrees/{pedigree}"
    assert os.path.exists(filename)

    argv = [filename, "-o", temp_filename]

    main(argv)
    assert os.path.exists(temp_filename)


@pytest.mark.parametrize(
    "pedigree",
    [
        ("pedigree_A.ped"),
        ("pedigree_B.ped"),
        ("pedigree_B2.ped"),
        ("pedigree_C.ped"),
    ],
)
def test_ped2parquet_patition(
    pedigree, temp_filename, global_dae_fixtures_dir
):
    filename = f"{global_dae_fixtures_dir}/pedigrees/{pedigree}"
    assert os.path.exists(filename)

    pd_filename = (
        f"{global_dae_fixtures_dir}/"
        f"partition_descriptor/partition_description.conf"
    )

    argv = [
        filename,
        "-o",
        temp_filename,
        "--pd",
        pd_filename,
    ]

    main(argv)

    assert os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema
    assert "family_bin" in schema.names
    print(schema)

    df = pqfile.read().to_pandas()
    print(df)
    families = FamiliesData.from_pedigree_df(df)

    assert "f1" in families
    f1 = families["f1"]
    print([p.family_bin for p in f1.persons.values()])
    assert all([p.family_bin == 9 for p in f1.persons.values()])

    assert "f2" in families
    f2 = families["f2"]
    print([p.family_bin for p in f2.persons.values()])
    assert all([p.family_bin == 6 for p in f2.persons.values()])


@pytest.mark.parametrize(
    "pedigree_filename,parquet_filename",
    [
        ("pedigree_A.ped", "pedigree_A.parquet"),
        ("/tmp/pedigree_A.ped", "pedigree_A.parquet"),
        ("tmp/pedigree_A.ped", "pedigree_A.parquet"),
        ("./pedigree_A.ped", "pedigree_A.parquet"),
    ],
)
def test_ped2parquet_outfilename(mocker, pedigree_filename, parquet_filename):

    mocker.patch("dae.pedigrees.loader.FamiliesLoader.load")
    mocker.patch(
        "dae.impala_storage.parquet_io.ParquetManager.families_to_parquet"
    )

    argv = ["pedigree_A.ped"]
    main(argv)

    FamiliesLoader.load.assert_called_once()
    ParquetManager.families_to_parquet.assert_called_once()
    call_args = ParquetManager.families_to_parquet.call_args

    _, outfile = call_args[0]
    assert outfile == parquet_filename
