# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import Any

import pytest
import yaml

from dae.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from gcp_storage.gcp_genotype_storage import GcpGenotypeStorage


@pytest.fixture(scope="session")
def gcp_storage_config() -> dict[str, Any]:
    return {
        "id": "gcp_test",
        "storage_type": "gcp",
        "project_id": "seqpipe-gcp-storage-testing",
        "import_bucket":
        "gs://seqpipe-gcp-storage-testing-bucket",
        "bigquery": {
            "db": "seqpipe_gcp_storage_testing_db",
        },
    }


@pytest.fixture(scope="session")
def gcp_storage_fixture(
    gcp_storage_config: dict[str, Any],
) -> GcpGenotypeStorage:
    storage_factory = get_genotype_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory(gcp_storage_config)
    assert storage is not None
    assert isinstance(storage, GcpGenotypeStorage)
    return storage.start()


@pytest.fixture(scope="session")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    gcp_storage_fixture: GcpGenotypeStorage,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{gcp_storage_fixture.storage_id}")
    gpf_instance = foobar_gpf(root_path, gcp_storage_fixture)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1
        """)

    study = vcf_study(
        root_path,
        "bq_test_minimal_vcf", ped_path, [vcf_path],
        gpf_instance)
    return study


@pytest.fixture(scope="session")
def partition_study(
    tmp_path_factory: pytest.TempPathFactory,
    gcp_storage_fixture: GcpGenotypeStorage,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_partition_{gcp_storage_fixture.storage_id}")
    gpf_instance = foobar_gpf(root_path, gcp_storage_fixture)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/1 0/0 0/1
        foo    10  .  C   G   .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        bar    7   .  A   C   .    .      .    GT     0/1 0/1 0/1 0/1 0/1 0/1
        bar    10  .  C   G   .    .      .    GT     0/0 0/0 0/1 0/0 0/1 0/1
        """)

    study = vcf_study(
        root_path,
        "bq_partition_vcf", ped_path, [vcf_path],
        gpf_instance, project_config_update=yaml.safe_load(textwrap.dedent("""
          partition_description:
            region_bin:
              chromosomes: foo,bar
              region_length: 8
            family_bin:
              family_bin_size: 2
            frequency_bin:
              rare_boundary: 5
        """)))
    return study
