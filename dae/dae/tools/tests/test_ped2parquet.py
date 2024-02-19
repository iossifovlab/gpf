# pylint: disable=W0621,C0114,C0116,W0212,W0613,no-member
import os
import pytest

import pyarrow.parquet as pq

from dae.pedigrees.families_data import FamiliesData
from dae.parquet.partition_descriptor import PartitionDescriptor

from dae.tools.ped2parquet import main


def test_partition_descriptor(global_dae_fixtures_dir: str) -> None:
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
def test_ped2parquet(
    pedigree: str, temp_filename: str, global_dae_fixtures_dir: str
) -> None:
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
    pedigree: str, temp_filename: str, global_dae_fixtures_dir: str
) -> None:
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
