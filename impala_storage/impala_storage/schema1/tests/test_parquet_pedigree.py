# pylint: disable=W0621,C0114,C0116,W0212,W0613,no-member
import os
import pytest

from dae.pedigrees.loader import FamiliesLoader
from impala_storage.schema1.parquet_io import VariantsParquetWriter, \
    ParquetWriter


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
    pedigree: str, temp_dirname: str,
    global_dae_fixtures_dir: str
) -> None:
    pedigree_filename = f"{global_dae_fixtures_dir}/pedigrees/{pedigree}"
    assert os.path.exists(pedigree_filename)

    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    assert families is not None

    parquet_filename = os.path.join(temp_dirname, "pedigree.parquet")

    ParquetWriter.families_to_parquet(
        families, parquet_filename, VariantsParquetWriter)

    assert os.path.exists(parquet_filename)
