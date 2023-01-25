# pylint: disable=W0621,C0114,C0116,W0212,W0613,no-member
import os
import pytest

import pyarrow.parquet as pq

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.parquet_writer import ParquetWriter

from dae.tools.ped2parquet import main


def test_partition_descriptor(global_dae_fixtures_dir):
    pd_filename = (
        f"{global_dae_fixtures_dir}/"
        f"partition_descriptor/partition_description.conf"
    )
    partition_descriptor = PartitionDescriptor.parse(pd_filename)
    assert partition_descriptor is not None


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
    fam1 = families["f1"]
    assert all(p.family_bin == 9 for p in fam1.persons.values())

    assert "f2" in families
    fam2 = families["f2"]
    assert all(p.family_bin == 6 for p in fam2.persons.values())


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
        "dae.parquet.parquet_writer.ParquetWriter.families_to_parquet"
    )

    argv = ["pedigree_A.ped"]
    main(argv)

    FamiliesLoader.load.assert_called_once()  # pylint: disable=no-member
    ParquetWriter.families_to_parquet.assert_called_once()
    call_args = ParquetWriter.families_to_parquet.call_args

    _, outfile, _ = call_args[0]
    assert outfile == parquet_filename
