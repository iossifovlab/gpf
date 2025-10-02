# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any

import pytest
from dae.duckdb_storage.duckdb_genotype_storage import (
    DuckDbStorage,
)
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing.import_helpers import vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def duckdb_storage(
    tmp_path_factory: pytest.TempPathFactory,
) -> DuckDbStorage:
    storage_path = tmp_path_factory.mktemp("duckdb_storage")
    storage_config = {
        "id": "duckdb_test",
        "storage_type": "duckdb",
        "db": "duckdb_storage/test.duckdb",
        "base_dir": str(storage_path),
    }
    storage_factory = get_genotype_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory(storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbStorage)
    return storage


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    duckdb_storage: DuckDbStorage,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_instance")
    return t4c8_gpf(root_path, duckdb_storage)


@pytest.fixture(scope="module")
def t4c8_study_partitioned(
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
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

    return vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        gpf_instance=t4c8_instance,
        project_config_update=project_config_update,
    )


def test_summary_variants_simple(
    t4c8_study_partitioned: GenotypeData,
) -> None:
    svs = list(t4c8_study_partitioned.query_summary_variants())
    assert len(svs) == 6


@pytest.mark.parametrize("region, attrs", [
    (Region("chr1", 4, 4), {
        "summary_index": 0,
        "bucket_index": 100000,
    }),
    (Region("chr1", 54, 54), {
        "summary_index": 1,
        "bucket_index": 100000,
    }),
])
def test_summary_variants_deserialization(
    t4c8_study_partitioned: GenotypeData,
    region: Region,
    attrs: dict[str, Any],
) -> None:
    svs = list(t4c8_study_partitioned.query_summary_variants(regions=[region]))
    assert len(svs) == 1

    for allele_index, sa in enumerate(svs[0].alt_alleles):
        assert sa["allele_index"] == allele_index + 1
        for key, value in attrs.items():
            assert sa[key] == value, (key, value)


@pytest.mark.parametrize("region, attrs", [
    (Region("chr1", 4, 4), [
        {
            "summary_index": 0,
            "bucket_index": 100000,
            "allele_index": 0,
            "sj_index": 1000000000000000000,
        },
        {
            "summary_index": 0,
            "bucket_index": 100000,
            "allele_index": 1,
            "sj_index": 1000000000000000001,
        },
        {
            "summary_index": 0,
            "bucket_index": 100000,
            "allele_index": 2,
            "sj_index": 1000000000000000002,
        },
    ]),
    (Region("chr1", 100, 100), [
        {
            "summary_index": 3,
            "bucket_index": 100000,
            "allele_index": 0,
            "sj_index": 1_000_000_000_000_030_000,
        },
        {
            "summary_index": 3,
            "bucket_index": 100000,
            "allele_index": 1,
            "sj_index": 1_000_000_000_000_030_001,
        },
        {
            "summary_index": 3,
            "bucket_index": 100000,
            "allele_index": 2,
            "sj_index": 1_000_000_000_000_030_002,
        },
    ]),
    (Region("chr1", 122, 123), [
        {
            "summary_index": 5,
            "bucket_index": 100000,
            "allele_index": 0,
            "sj_index": 1_000_000_000_000_050_000,
        },
        {
            "summary_index": 5,
            "bucket_index": 100000,
            "allele_index": 1,
            "sj_index": 1_000_000_000_000_050_001,
        },
        {
            "summary_index": 5,
            "bucket_index": 100000,
            "allele_index": 2,
            "sj_index": 1_000_000_000_000_050_002,
        },
    ]),
])
def test_summary_alleles_deserialization(
    t4c8_study_partitioned: GenotypeData,
    region: Region,
    attrs: list[dict[str, Any]],
) -> None:
    svs = list(t4c8_study_partitioned.query_summary_variants(regions=[region]))
    assert len(svs) == 1

    for index, sa in enumerate(svs[0].alleles):
        for key, value in attrs[index].items():
            assert sa[key] == value, (sa, key, value)
