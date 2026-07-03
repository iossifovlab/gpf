# pylint: disable=redefined-outer-name,C0114,C0116
import logging
import pathlib

import pyarrow.parquet as pq
import pytest
from gain.genomic_resources.testing import setup_pedigree, setup_vcf

from gpf.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.testing.foobar_import import foobar_gpf
from gpf.testing.import_helpers import vcf_study
from gpf.tools import families_withdrawal_genotypes
from gpf.tools.families_withdrawal_genotypes import main


def _build_two_family(
    tmp_path: pathlib.Path,
) -> tuple[GPFInstance, dict]:
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
    return gpf, storage_config


@pytest.fixture
def two_family_gpf(tmp_path: pathlib.Path) -> GPFInstance:
    gpf, _ = _build_two_family(tmp_path)
    return gpf


def _storage_base(gpf: GPFInstance) -> pathlib.Path:
    return (
        gpf.genotype_storages
        .get_default_genotype_storage()
        .config.base_dir
    )


def _ped_path(gpf: GPFInstance) -> pathlib.Path:
    return (
        _storage_base(gpf) / "two_fam_study" / "pedigree" / "pedigree.parquet"
    )


def _family_parquets(gpf: GPFInstance) -> list[pathlib.Path]:
    family_dir = _storage_base(gpf) / "two_fam_study" / "family"
    return sorted(family_dir.rglob("*.parquet"))


def _bak_files(gpf: GPFInstance) -> list[pathlib.Path]:
    return sorted(
        (_storage_base(gpf) / "two_fam_study").rglob("*.bak"),
    )


def test_genotype_removes_pedigree_rows(two_family_gpf: GPFInstance) -> None:
    ped_path = _ped_path(two_family_gpf)
    ped_before = pq.read_table(ped_path)
    assert set(ped_before.column("family_id").to_pylist()) == {"f1", "f2"}

    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)

    ped_after = pq.read_table(ped_path)
    assert set(ped_after.column("family_id").to_pylist()) == {"f2"}


def test_genotype_leaves_family_parquet_untouched(
    two_family_gpf: GPFInstance,
) -> None:
    # The family-variant Parquet files must NOT be rewritten: the tool is
    # pedigree-only. f1's variant rows stay on disk (made inaccessible at
    # query time, not deleted).
    family_originals = {
        pf: pf.read_bytes() for pf in _family_parquets(two_family_gpf)
    }
    assert family_originals, "expected at least one family-variant parquet"

    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)

    for pf, content in family_originals.items():
        assert pf.read_bytes() == content, f"{pf} was modified"
    # and f1 rows are still present somewhere in the family parquets
    seen_f1 = False
    for pf in _family_parquets(two_family_gpf):
        table = pq.read_table(pf)
        if len(table) == 0:
            continue
        fid_col = (
            "familyId" if "familyId" in table.schema.names else "family_id"
        )
        if "f1" in table.column(fid_col).to_pylist():
            seen_f1 = True
    assert seen_f1, "f1 variant rows should remain in the family parquet"


def test_genotype_query_after_withdrawal_is_inaccessible(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The real net effect: after withdrawing f1, querying a freshly-built
    # instance (which re-reads the trimmed pedigree) returns only f2's
    # variants and does NOT raise, even though f1's rows remain on disk.
    gpf, storage_config = _build_two_family(tmp_path)

    baseline = list(gpf.get_genotype_data("two_fam_study").query_variants())
    assert {v.family_id for v in baseline} == {"f1", "f2"}

    main(["two_fam_study", "f1"], gpf_instance=gpf)

    gpf2 = GPFInstance.build(
        str(tmp_path / "gpf" / "gpf_instance" / "gpf_instance.yaml"))
    gpf2.genotype_storages.register_default_storage(
        get_genotype_storage_factory("duckdb_parquet")(storage_config))
    study2 = gpf2.get_genotype_data("two_fam_study")
    assert set(study2.families.keys()) == {"f2"}

    with caplog.at_level(logging.WARNING):
        variants = list(study2.query_variants())

    assert {v.family_id for v in variants} == {"f2"}
    # f1's variant rows on disk were skipped, with a single warning.
    f1_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "'f1'" in r.getMessage()
    ]
    assert len(f1_warnings) == 1, "expected exactly one warn-once for f1"


def test_genotype_resolves_pedigree_from_config_not_hardcoded(
    two_family_gpf: GPFInstance,
) -> None:
    # Pins the config-driven pedigree resolution (iossifovlab/gpf#956):
    # the tool must resolve the pedigree via the study config's
    # genotype_storage.tables.pedigree, NOT the hardcoded
    # base_dir/<study_id>/pedigree/pedigree.parquet location.
    #
    # We move the real pedigree to a non-default location and point the
    # study config at it. The default-location file is removed, so a tool
    # that still used the hardcoded path would fail to find any pedigree
    # and exit(1) instead of rewriting the custom file. This test therefore
    # FAILS against the old hardcoded resolution and PASSES against the fix.
    default_ped = _ped_path(two_family_gpf)
    custom_ped = (
        _storage_base(two_family_gpf) / "two_fam_study" / "custom"
        / "ped.parquet"
    )
    custom_ped.parent.mkdir(parents=True, exist_ok=True)
    default_ped.replace(custom_ped)
    assert not default_ped.exists()

    # get_genotype_data returns the same cached study object on every call,
    # so mutating its config here is what main() will resolve against.
    study = two_family_gpf.get_genotype_data("two_fam_study")
    study.config["genotype_storage"]["tables"]["pedigree"] = (
        "parquet_scan('two_fam_study/custom/ped.parquet')"
    )

    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)

    # The custom-location pedigree was rewritten (f1 dropped) ...
    custom_after = pq.read_table(custom_ped)
    assert set(custom_after.column("family_id").to_pylist()) == {"f2"}
    # ... and nothing was recreated at the hardcoded default location.
    assert not default_ped.exists()


def test_genotype_dry_run_writes_nothing(
    two_family_gpf: GPFInstance,
) -> None:
    ped_path = _ped_path(two_family_gpf)
    original = ped_path.read_bytes()

    main(["--dry-run", "two_fam_study", "f1"], gpf_instance=two_family_gpf)

    assert ped_path.read_bytes() == original
    assert _bak_files(two_family_gpf) == []


def test_genotype_backup_by_default_holds_original_rows(
    two_family_gpf: GPFInstance,
) -> None:
    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)

    baks = _bak_files(two_family_gpf)
    # pedigree-only: exactly one backup, of the pedigree
    assert len(baks) == 1
    assert baks[0].name.startswith("pedigree.")
    assert baks[0].name.endswith(".parquet.bak")
    backup_table = pq.read_table(baks[0])
    assert set(backup_table.column("family_id").to_pylist()) == {"f1", "f2"}


def test_genotype_no_backup_creates_none(
    two_family_gpf: GPFInstance,
) -> None:
    main(
        ["--no-backup", "two_fam_study", "f1"],
        gpf_instance=two_family_gpf,
    )
    assert _bak_files(two_family_gpf) == []


def test_genotype_two_runs_non_clashing_backups(
    two_family_gpf: GPFInstance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two successive runs against the same study must produce two distinct
    # pedigree .bak files. Inject the stamp to be deterministic.
    stamps = iter(["20260625T100000Z", "20260625T100001Z"])
    monkeypatch.setattr(
        families_withdrawal_genotypes, "make_run_stamp",
        lambda: next(stamps),
    )

    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)
    main(["two_fam_study", "f2"], gpf_instance=two_family_gpf)

    ped_baks = sorted(b.name for b in _bak_files(two_family_gpf))
    assert ped_baks == [
        "pedigree.20260625T100000Z.parquet.bak",
        "pedigree.20260625T100001Z.parquet.bak",
    ]


def test_genotype_no_match_leaves_file_untouched(
    two_family_gpf: GPFInstance,
) -> None:
    ped_path = _ped_path(two_family_gpf)
    original = ped_path.read_bytes()
    family_originals = {
        pf: pf.read_bytes() for pf in _family_parquets(two_family_gpf)
    }

    main(["two_fam_study", "no_such_family"], gpf_instance=two_family_gpf)

    assert ped_path.read_bytes() == original
    for pf, content in family_originals.items():
        assert pf.read_bytes() == content
    assert _bak_files(two_family_gpf) == []


class _FakeInstance:
    """Minimal instance exposing only the id-set accessors main() needs."""

    def get_genotype_data_ids(self) -> list[str]:
        return ["geno_study"]

    def get_phenotype_data_ids(self) -> list[str]:
        return ["pheno_study"]


def test_genotype_accumulating_withdrawals_file(
    two_family_gpf: GPFInstance,
    tmp_path: pathlib.Path,
) -> None:
    # Primary use case: a persistent file of withdrawn families that grows
    # over time. Each re-run must succeed even though families from prior
    # runs are no longer in the pedigree.
    families_file = tmp_path / "withdrawn.txt"
    ped_path = _ped_path(two_family_gpf)

    families_file.write_text("f1\n")
    main(
        ["--no-backup", "--families-file", str(families_file), "two_fam_study"],
        gpf_instance=two_family_gpf,
    )
    assert set(pq.read_table(ped_path).column("family_id").to_pylist()) == {"f2"}

    # Add f2; f1 is already gone but must not cause a failure.
    families_file.write_text("f1\nf2\n")
    main(
        ["--no-backup", "--families-file", str(families_file), "two_fam_study"],
        gpf_instance=two_family_gpf,
    )
    assert pq.read_table(ped_path).num_rows == 0


def test_genotype_families_file_mode(
    two_family_gpf: GPFInstance,
    tmp_path: pathlib.Path,
) -> None:
    families_file = tmp_path / "families.txt"
    families_file.write_text("f1\n\n")
    ped_path = _ped_path(two_family_gpf)

    main(
        ["--families-file", str(families_file), "two_fam_study"],
        gpf_instance=two_family_gpf,
    )

    ped_after = pq.read_table(ped_path)
    assert set(ped_after.column("family_id").to_pylist()) == {"f2"}


def test_genotype_no_families_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["two_fam_study"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1


def test_genotype_wrong_type_redirect_exits() -> None:
    # Handing a phenotype study to the genotype tool exits 1.
    with pytest.raises(SystemExit) as exc:
        main(["pheno_study", "fam1"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1


def test_genotype_unknown_study_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["no_such_study", "f1"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1
