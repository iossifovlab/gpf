# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf

from dae.genotype_storage.genotype_storage_registry import \
    get_genotype_storage_factory
from dae.import_tools.import_tools import get_import_storage_factory

from gcp_genotype_storage.gcp_genotype_storage import GcpGenotypeStorage
from gcp_genotype_storage.gcp_import_storage import GcpImportStorage


@pytest.fixture(scope="session")
def gcp_storage_config():
    return {
        "id": "dev_gcp_genotype_storage",
        "storage_type": "gcp",
        "project_id": "gcp-genotype-storage",
        "import_bucket": "gs://gcp-genotype-storage-input",
        "big_query": {
            "db": "gpf_genotype_storage_dev_lubo",
        }
    }


def test_experiment_genotype_storage(gcp_storage_config):
    storage_factory = get_genotype_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory(gcp_storage_config)
    assert storage is not None
    assert isinstance(storage, GcpGenotypeStorage)


def test_experiment_import_storage(gcp_storage_config):
    storage_factory = get_import_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory()
    assert storage is not None
    assert isinstance(storage, GcpImportStorage)


@pytest.fixture(scope="module")
def gcp_storage_fixture(gcp_storage_config):
    storage_factory = get_genotype_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory(gcp_storage_config)
    assert storage is not None
    assert isinstance(storage, GcpGenotypeStorage)
    return storage.start()


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, gcp_storage_fixture):
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{gcp_storage_fixture.storage_id}")
    gpf_instance = alla_gpf(root_path, gcp_storage_fixture)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/0 0/0 0/0
        chrA   4   .  A   T    .    .      .    GT     0/1 0/0 0/0 0/1 0/0 0/0
        chrA   5   .  A   T,G  .    .      .    GT     0/1 0/0 0/0 0/2 0/0 0/0
        chrA   6   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/2 0/0 0/0
        chrA   7   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/1 0/0 0/0
        chrA   8   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/1 2/0 0/0
        """)

    study = vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)
    return study


def test_imported_study(imported_study):
    assert imported_study is not None
