# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.gpf_instance import GPFInstance
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


@pytest.fixture(scope="module")
def t4c8_study_odd(t4c8_instance: GPFInstance) -> str:
    """
    Study fixture containing edge cases.

    This study is designed to exhibit specific behaviour that might break
    a naive implementation for loading family variants.

    There are five summary variants in this study.
    They are distributed among 3 families in the following way:

    [f1.1]      [f1.2]      [f1.3]
    - sv0       - sv0       - sv0
    - sv1       - sv2       - sv2
    - sv2                   - sv3
    - sv3
    """
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_odd" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.2     mom2     0     0     2   1      mom
f1.2     dad2     0     0     1   1      dad
f1.2     ch2      dad2  mom2  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_odd" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom2 dad2 ch2 mom3 dad3 ch3
chr1   4    .  T   G    .    .      .    GT     0/1  0/1  0/1 0/1  0/1  0/1 0/1  0/1  0/1
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/0  0/0  0/0 0/0  0/0  0/0
chr1   90   .  G   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/1  0/1 0/1  0/1  0/1
chr1   100  .  T   G    .    .      .    GT     0/1  0/1  0/1 0/0  0/0  0/0 0/1  0/1  0/1
        """)  # noqa

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 1000,
            },
            "family_bin": {
                "family_bin_size": 3,
            },
        },
    }
    vcf_study(
        root_path,
        "study_odd", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        project_config_overwrite={"destination": {"storage_type": "schema2"}},
    )
    return f"{root_path}/work_dir/study_odd"


def test_fetch_variants_count_nonpartitioned(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 3
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 4


def test_fetch_variants_count_partitioned(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 6
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 12


def test_fetch_variants_count_nonpartitioned_region(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants(region=Region("chr1", 119, 119)))
    # summary variants
    assert len(vs) == 1
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 2

    vs = list(loader.fetch_variants(region=Region("chr1", 119, 122)))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 3


def test_fetch_variants_count_partitioned_region(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants(region=Region("chr1", 1, 89)))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 4

    vs = list(loader.fetch_variants(region=Region("chr1", 90, 200)))
    # summary variants
    assert len(vs) == 4
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 8


def test_fetch_variants_odd_study(
    t4c8_study_odd: str,
) -> None:
    loader = ParquetLoader(t4c8_study_odd)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 4
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 9


def test_fetch_variants_pedigree_only(
    t4c8_study_pedigree_only: str,
) -> None:
    loader = ParquetLoader(t4c8_study_pedigree_only)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 0
    # family variants
    assert sum(len(fvs) for _, fvs in vs) == 0
