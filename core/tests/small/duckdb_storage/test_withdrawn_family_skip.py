# pylint: disable=redefined-outer-name,C0114,C0116
import logging
import pathlib

import pytest
from gain.genomic_resources.testing import setup_pedigree, setup_vcf

from gpf.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.testing.foobar_import import foobar_gpf
from gpf.testing.import_helpers import vcf_study


@pytest.fixture
def two_family_gpf(tmp_path: pathlib.Path) -> GPFInstance:
    storage_config = {
        "id": "test_storage",
        "storage_type": "duckdb_parquet",
        "base_dir": str(tmp_path / "storage"),
    }
    storage = get_genotype_storage_factory("duckdb_parquet")(storage_config)
    gpf = foobar_gpf(tmp_path / "gpf", storage)
    ped_path = setup_pedigree(
        tmp_path / "data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        m1        0      0      2    1       mom
        f1        d1        0      0      1    1       dad
        f1        p1        d1     m1     2    2       prb
        f2        m2        0      0      2    1       mom
        f2        d2        0      0      1    1       dad
        f2        p2        d2     m2     2    2       prb
        """)
    vcf_path = setup_vcf(
        tmp_path / "data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        foo    13  .  G   C   .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/0
        foo    14  .  C   T   .    .      .    GT     0/0 0/1 0/1 0/0 0/0 0/0
        foo    15  .  A   G   .    .      .    GT     0/0 0/0 0/0 0/1 0/0 0/1
        """)
    vcf_study(
        tmp_path / "data", "two_fam_study", ped_path, [vcf_path],
        gpf_instance=gpf)
    return gpf


def test_variant_for_family_absent_from_pedigree_is_skipped(
    two_family_gpf: GPFInstance,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # A family-variant row whose family is not in the pedigree-derived
    # families is skipped at deserialization (returns None) instead of
    # raising KeyError, with a single warning per missing family.
    study = two_family_gpf.get_genotype_data("two_fam_study")
    backend = study.backend

    assert {v.family_id for v in study.query_variants()} == {"f1", "f2"}

    # simulate f1 having been withdrawn from the pedigree while its
    # family-variant rows remain on disk
    del backend.families["f1"]

    with caplog.at_level(logging.WARNING):
        variants = list(study.query_variants())

    assert {v.family_id for v in variants} == {"f2"}
    f1_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "'f1'" in r.getMessage()
    ]
    assert len(f1_warnings) == 1
