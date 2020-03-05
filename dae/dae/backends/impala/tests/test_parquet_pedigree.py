import os
import dae
import pytest

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.impala.parquet_io import ParquetManager


@pytest.mark.parametrize(
    "pedigree",
    [
        ("pedigree_A.ped"),
        ("pedigree_B.ped"),
        ("pedigree_B2.ped"),
        ("pedigree_C.ped"),
    ],
)
def test_ped2parquet(pedigree, temp_dirname, global_dae_fixtures_dir):
    pedigree_filename = f"{global_dae_fixtures_dir}/pedigrees/{pedigree}"
    assert os.path.exists(pedigree_filename)

    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    assert families is not None

    parquet_filename = os.path.join(temp_dirname, "pedigree.parquet")

    ParquetManager.families_to_parquet(families, parquet_filename)

    assert os.path.exists(parquet_filename)


@pytest.mark.parametrize(
    "pedigree, outfile, dirname",
    [
        ("pedigree_A.ped", "./pedigree.parquet", "."),
        ("pedigree_A.ped", "/tmp/pedigree.parquet", "/tmp"),
        ("pedigree_A.ped", "tmp/pedigree.parquet", "tmp"),
    ],
)
def test_ped2parquet_mock(
    mocker, pedigree, outfile, dirname, global_dae_fixtures_dir
):

    pedigree_filename = f"{global_dae_fixtures_dir}/pedigrees/{pedigree}"
    assert os.path.exists(pedigree_filename)

    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    assert families is not None

    mocker.patch("os.makedirs")
    mocker.patch("dae.backends.impala.parquet_io.save_ped_df_to_parquet")

    ParquetManager.families_to_parquet(families, outfile)

    os.makedirs.assert_called_once_with(dirname, exist_ok=True)
    dae.backends.impala.parquet_io.save_ped_df_to_parquet.assert_called_once()

    call_args = dae.backends.impala.parquet_io.save_ped_df_to_parquet.call_args
    _, filename = call_args[0]
    assert filename == outfile
