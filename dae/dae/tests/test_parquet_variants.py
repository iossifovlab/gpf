# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genotype_storage import get_genotype_storage_factory
from dae.parquet_variants import ParquetGenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def parquet_storage_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> ParquetGenotypeStorage:
    root_path = tmp_path_factory.mktemp("parquet_storage")
    conf = {
        "id": "test_parquet_storage",
        "storage_type": "parquet",
        "dir": str(root_path),
    }
    storage_factory = get_genotype_storage_factory("parquet")
    storage = storage_factory(conf)
    assert isinstance(storage, ParquetGenotypeStorage)
    return storage


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    parquet_storage_fixture: ParquetGenotypeStorage,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_gpf_instance")
    gpf_instance = t4c8_gpf(root_path, storage=parquet_storage_fixture)
    ped_path = setup_pedigree(
        root_path / "study_data" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "study_data" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }
    study = vcf_study(
        root_path, "study", ped_path, [vcf_path],
        gpf_instance,
        project_config_update=project_config_update,
    )
    assert parquet_storage_fixture.data_dir is not None
    assert pathlib.Path(parquet_storage_fixture.data_dir).exists()
    assert pathlib.Path(parquet_storage_fixture.data_dir, "study").exists()
    return study


def test_query_all_variants(imported_study: GenotypeData) -> None:
    vs = list(imported_study.query_variants())
    assert len(vs) == 12


def test_query_variants_with_region(imported_study: GenotypeData) -> None:
    vs = list(imported_study.query_variants(regions=[Region("chr1", 1, 99)]))
    assert len(vs) == 6
