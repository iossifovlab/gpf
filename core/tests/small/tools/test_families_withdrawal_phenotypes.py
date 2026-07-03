# pylint: disable=redefined-outer-name,C0114,C0116
import pathlib
import textwrap

import duckdb
import pytest
from gain.genomic_resources.testing import setup_pedigree

from gpf.pheno.common import DestinationConfig, PhenoImportConfig
from gpf.pheno.pheno_data import PhenotypeStudy
from gpf.pheno.pheno_import import import_pheno_data
from gpf.tools import families_withdrawal_phenotypes
from gpf.tools.families_withdrawal_phenotypes import (
    _remove_from_pheno_leaf,
    main,
)


@pytest.fixture
def pheno_study(tmp_path: pathlib.Path) -> PhenotypeStudy:
    ped_path = setup_pedigree(
        tmp_path / "pedigree.ped",
        """
        familyId  personId   dadId      momId      sex  status  role
        fam1      fam1.mom   0          0          2    1       mom
        fam1      fam1.dad   0          0          1    1       dad
        fam1      fam1.prb   fam1.dad   fam1.mom   2    2       prb
        fam2      fam2.mom   0          0          2    1       mom
        fam2      fam2.dad   0          0          1    1       dad
        fam2      fam2.prb   fam2.dad   fam2.mom   2    2       prb
        """)
    instruments_dir = tmp_path / "instruments"
    instruments_dir.mkdir(parents=True)
    (instruments_dir / "instr1.csv").write_text(textwrap.dedent("""\
        person_id,score
        fam1.mom,10
        fam1.dad,20
        fam1.prb,30
        fam2.mom,40
        fam2.dad,50
        fam2.prb,60
    """))

    storage_dir = tmp_path / "storage"
    import_config = PhenoImportConfig(
        id="test_pheno",
        input_dir=str(tmp_path),
        work_dir=str(tmp_path / "work"),
        instrument_files=[str(instruments_dir)],
        pedigree=str(ped_path),
        person_column="person_id",
        destination=DestinationConfig(storage_dir=str(storage_dir)),
    )
    import_pheno_data(import_config)
    return PhenotypeStudy(
        "test_pheno",
        str(storage_dir / "test_pheno" / "test_pheno.db"),
    )


def _count(dbfile: str, sql: str) -> int:
    conn = duckdb.connect(dbfile, read_only=True)
    count = conn.execute(sql).fetchone()[0]  # type: ignore[index]
    conn.close()
    return count


def test_pheno_removes_persons(pheno_study: PhenotypeStudy) -> None:
    dbfile = pheno_study.db.dbfile
    assert _count(
        dbfile, "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 3

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, backup=False, stamp="x",
    )

    assert _count(
        dbfile, "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 0


def test_pheno_removes_family_record(pheno_study: PhenotypeStudy) -> None:
    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, backup=False, stamp="x",
    )
    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM family WHERE family_id = 'fam1'",
    ) == 0


def test_pheno_preserves_other_family(pheno_study: PhenotypeStudy) -> None:
    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, backup=False, stamp="x",
    )
    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam2'",
    ) == 3


def test_pheno_dry_run_no_changes(pheno_study: PhenotypeStudy) -> None:
    before = _count(pheno_study.db.dbfile, "SELECT COUNT(*) FROM person")

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=True, backup=True, stamp="x",
    )

    after = _count(pheno_study.db.dbfile, "SELECT COUNT(*) FROM person")
    assert after == before
    dbfile = pathlib.Path(pheno_study.db.dbfile)
    assert list(dbfile.parent.glob("*.bak")) == []


def test_pheno_backup_by_default_holds_original_data(
    pheno_study: PhenotypeStudy,
) -> None:
    dbfile = pathlib.Path(pheno_study.db.dbfile)

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, backup=True,
        stamp="20260625T143000Z",
    )

    bak = dbfile.with_name("test_pheno.20260625T143000Z.db.bak")
    assert bak.exists()
    # backup holds original data (fam1 still present)
    assert _count(
        str(bak), "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 3
    # live db had fam1 removed
    assert _count(
        str(dbfile), "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 0


def test_pheno_no_backup_creates_none(pheno_study: PhenotypeStudy) -> None:
    dbfile = pathlib.Path(pheno_study.db.dbfile)

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, backup=False, stamp="x",
    )

    assert list(dbfile.parent.glob("*.bak")) == []


def test_pheno_single_quote_family_id_is_safe(
    pheno_study: PhenotypeStudy,
) -> None:
    # A family ID containing a single quote must be handled via placeholders,
    # not interpolation: it must not raise a SQL parser error and must match
    # by exact string (here: no such family, so nothing is removed).
    dbfile = pheno_study.db.dbfile
    before = _count(dbfile, "SELECT COUNT(*) FROM person")

    _remove_from_pheno_leaf(
        pheno_study, {"o'brien"}, dry_run=False, backup=False, stamp="x",
    )

    # exact-string non-match -> no rows removed (and no parser error raised)
    assert _count(dbfile, "SELECT COUNT(*) FROM person") == before


class _RealPhenoInstance:
    """Wrap a real leaf pheno study so main() can resolve it by id."""

    def __init__(self, study: PhenotypeStudy) -> None:
        self._study = study

    def get_genotype_data_ids(self) -> list[str]:
        return []

    def get_phenotype_data_ids(self) -> list[str]:
        return [self._study.pheno_id]

    def get_phenotype_data(self, study_id: str) -> PhenotypeStudy:
        assert study_id == self._study.pheno_id
        return self._study


def test_pheno_main_happy_path_removes_and_backs_up(
    pheno_study: PhenotypeStudy,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dbfile = pathlib.Path(pheno_study.db.dbfile)
    monkeypatch.setattr(
        families_withdrawal_phenotypes, "make_run_stamp",
        lambda: "20260625T143000Z",
    )

    main(
        ["test_pheno", "fam1"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )

    # persons + family removed from the live db
    assert _count(
        str(dbfile), "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 0
    assert _count(
        str(dbfile), "SELECT COUNT(*) FROM family WHERE family_id = 'fam1'",
    ) == 0
    # other family preserved
    assert _count(
        str(dbfile), "SELECT COUNT(*) FROM person WHERE family_id = 'fam2'",
    ) == 3

    # stamped backup holds the ORIGINAL (pre-removal) data
    bak = dbfile.with_name("test_pheno.20260625T143000Z.db.bak")
    assert bak.exists()
    assert _count(
        str(bak), "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 3


def test_pheno_main_two_runs_non_clashing_backups(
    pheno_study: PhenotypeStudy,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dbfile = pathlib.Path(pheno_study.db.dbfile)
    stamps = iter(["20260625T100000Z", "20260625T100001Z"])
    monkeypatch.setattr(
        families_withdrawal_phenotypes, "make_run_stamp",
        lambda: next(stamps),
    )

    main(
        ["test_pheno", "fam1"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )
    main(
        ["test_pheno", "fam2"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )

    baks = sorted(b.name for b in dbfile.parent.glob("*.db.bak"))
    assert baks == [
        "test_pheno.20260625T100000Z.db.bak",
        "test_pheno.20260625T100001Z.db.bak",
    ]


class _FakeInstance:
    """Minimal instance exposing only the id-set accessors main() needs."""

    def get_genotype_data_ids(self) -> list[str]:
        return ["geno_study"]

    def get_phenotype_data_ids(self) -> list[str]:
        return ["pheno_study"]


def test_pheno_accumulating_withdrawals_file(
    pheno_study: PhenotypeStudy,
    tmp_path: pathlib.Path,
) -> None:
    # Primary use case: a persistent file of withdrawn families that grows
    # over time. Each re-run must succeed even though families from prior
    # runs are no longer in the database.
    families_file = tmp_path / "withdrawn.txt"

    families_file.write_text("fam1\n")
    main(
        ["--no-backup", "--families-file", str(families_file), "test_pheno"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )
    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 0
    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam2'",
    ) == 3

    # Add fam2; fam1 is already gone but must not cause a failure.
    families_file.write_text("fam1\nfam2\n")
    main(
        ["--no-backup", "--families-file", str(families_file), "test_pheno"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )
    assert _count(
        pheno_study.db.dbfile, "SELECT COUNT(*) FROM person",
    ) == 0


def test_pheno_families_file_mode(
    pheno_study: PhenotypeStudy,
    tmp_path: pathlib.Path,
) -> None:
    families_file = tmp_path / "families.txt"
    families_file.write_text("fam1\n\n")

    main(
        ["--families-file", str(families_file), "test_pheno"],
        gpf_instance=_RealPhenoInstance(pheno_study),  # type: ignore[arg-type]
    )

    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ) == 0
    assert _count(
        pheno_study.db.dbfile,
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam2'",
    ) == 3


def test_pheno_no_families_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["pheno_study"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1


def test_pheno_main_wrong_type_redirect_exits() -> None:
    # Handing a genotype study to the phenotype tool exits 1.
    with pytest.raises(SystemExit) as exc:
        main(["geno_study", "fam1"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1


def test_pheno_main_unknown_study_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["no_such_study", "fam1"], gpf_instance=_FakeInstance())  # type: ignore[arg-type]
    assert exc.value.code == 1
