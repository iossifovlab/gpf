# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import pathlib
import shutil

import duckdb
from gain.genomic_resources.testing import setup_pedigree, setup_vcf

from gpf.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from gpf.gpf_instance import GPFInstance
from gpf.testing.import_helpers import vcf_study
from gpf.testing.t4c8_import import t4c8_gpf

FAKE_PHENO_DIR = pathlib.Path(__file__).parents[1] / \
    "pheno" / "fixtures" / "fake_phenoDB" / "fake"


def _assert_writable(dbfile: pathlib.Path) -> None:
    with duckdb.connect(dbfile, read_only=False) as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)


def test_shutdown_closes_genotype_and_pheno_db_files(
    tmp_path: pathlib.Path,
) -> None:
    storage_dbfile = tmp_path / "duckdb_storage" / "test.duckdb"
    storage_factory = get_genotype_storage_factory("duckdb")
    storage = storage_factory({
        "id": "duckdb_test",
        "storage_type": "duckdb",
        "db": "test.duckdb",
        "base_dir": str(tmp_path / "duckdb_storage"),
    })
    instance = t4c8_gpf(tmp_path / "t4c8", storage)
    pheno_dbfile = pathlib.Path(instance.dae_dir) / "pheno" / "fake" / "fake.db"
    shutil.copytree(FAKE_PHENO_DIR, pheno_dbfile.parent)
    ped_path = setup_pedigree(
        tmp_path / "study_1" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
        """)
    vcf_path = setup_vcf(
        tmp_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
chr1   54   .  T   C   .    .      .    GT     0/1  0/0  0/1
        """)
    study = vcf_study(
        tmp_path, "study_1", ped_path, [vcf_path], gpf_instance=instance)
    assert len(list(study.query_variants())) == 1
    assert instance.get_phenotype_data("fake") is not None

    instance.shutdown()

    _assert_writable(storage_dbfile)
    _assert_writable(pheno_dbfile)


def test_shutdown_of_fresh_instance_builds_no_registry(
    tmp_path: pathlib.Path,
) -> None:
    config_path = tmp_path / "gpf_instance.yaml"
    config_path.write_text("instance_id: test_instance\n")
    instance = GPFInstance.build(config_path, grr=None)

    instance.shutdown()
    instance.shutdown()

    assert "genotype_storages" not in instance.__dict__
    assert "_pheno_registry" not in instance.__dict__
