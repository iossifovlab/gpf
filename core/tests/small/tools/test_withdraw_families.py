# pylint: disable=redefined-outer-name,C0114,C0116
import pathlib
import textwrap

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from gain.genomic_resources.testing import setup_pedigree, setup_vcf

from gpf.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pheno.common import DestinationConfig, PhenoImportConfig
from gpf.pheno.pheno_data import PhenotypeStudy
from gpf.pheno.pheno_import import import_pheno_data
from gpf.testing.foobar_import import foobar_gpf
from gpf.testing.import_helpers import vcf_study
from gpf.tools.withdraw_families import (
    _remove_from_pheno_leaf,
    _rewrite_parquet,
    main,
)


def _make_family_parquet(
    path: pathlib.Path, col: str = "family_id",
) -> None:
    table = pa.table({
        col: ["f1", "f1", "f2", "f2", "f3"],
        "value": [1, 2, 3, 4, 5],
    })
    pq.write_table(table, path)


def test_rewrite_parquet_removes_matching_families(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "test.parquet"
    _make_family_parquet(path)

    before, after = _rewrite_parquet(
        path, {"f1"}, dry_run=False, keep_original=False,
    )

    assert before == 5
    assert after == 3
    result = pq.read_table(path)
    assert set(result.column("family_id").to_pylist()) == {"f2", "f3"}


def test_rewrite_parquet_unchanged_when_no_match(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "test.parquet"
    _make_family_parquet(path)
    original_bytes = path.read_bytes()

    before, after = _rewrite_parquet(
        path, {"f99"}, dry_run=False, keep_original=False,
    )

    assert before == after == 5
    assert path.read_bytes() == original_bytes


def test_rewrite_parquet_dry_run_does_not_modify(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "test.parquet"
    _make_family_parquet(path)
    original_bytes = path.read_bytes()

    before, after = _rewrite_parquet(
        path, {"f1"}, dry_run=True, keep_original=False,
    )

    assert before == 5
    assert after == 3
    assert path.read_bytes() == original_bytes


def test_rewrite_parquet_keep_original(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "test.parquet"
    _make_family_parquet(path)

    _rewrite_parquet(path, {"f1"}, dry_run=False, keep_original=True)

    orig = path.with_suffix(".parquet.orig")
    assert orig.exists()
    assert len(pq.read_table(orig)) == 5
    result = pq.read_table(path)
    assert set(result.column("family_id").to_pylist()) == {"f2", "f3"}


def test_rewrite_parquet_familyid_camelcase(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "test.parquet"
    _make_family_parquet(path, col="familyId")

    before, after = _rewrite_parquet(
        path, {"f1"}, dry_run=False, keep_original=False,
    )

    assert before == 5
    assert after == 3
    result = pq.read_table(path)
    assert set(result.column("familyId").to_pylist()) == {"f2", "f3"}


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


def test_remove_families_genotype_removes_rows(
    two_family_gpf: GPFInstance,
) -> None:
    storage_base = (
        two_family_gpf.genotype_storages
        .get_default_genotype_storage()
        .config.base_dir
    )
    ped_path = storage_base / "two_fam_study" / "pedigree" / "pedigree.parquet"

    ped_before = pq.read_table(ped_path)
    assert set(ped_before.column("family_id").to_pylist()) == {"f1", "f2"}

    main(["two_fam_study", "f1"], gpf_instance=two_family_gpf)

    ped_after = pq.read_table(ped_path)
    assert set(ped_after.column("family_id").to_pylist()) == {"f2"}

    family_dir = storage_base / "two_fam_study" / "family"
    for pf in family_dir.rglob("*.parquet"):
        table = pq.read_table(pf)
        if len(table) == 0:
            continue
        fid_col = (
            "familyId" if "familyId" in table.schema.names
            else "family_id"
        )
        assert "f1" not in table.column(fid_col).to_pylist()


def test_remove_families_genotype_dry_run(
    two_family_gpf: GPFInstance,
) -> None:
    storage_base = (
        two_family_gpf.genotype_storages
        .get_default_genotype_storage()
        .config.base_dir
    )
    ped_path = (
        storage_base / "two_fam_study" / "pedigree" / "pedigree.parquet"
    )
    original_bytes = ped_path.read_bytes()

    main(["--dry-run", "two_fam_study", "f1"], gpf_instance=two_family_gpf)

    assert ped_path.read_bytes() == original_bytes


def test_remove_families_unknown_study_exits(
    two_family_gpf: GPFInstance,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["no_such_study", "f1"], gpf_instance=two_family_gpf)
    assert exc_info.value.code == 1


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


def test_remove_from_pheno_leaf_removes_persons(
    pheno_study: PhenotypeStudy,
) -> None:
    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 3

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, keep_original=False,
    )

    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 0


def test_remove_from_pheno_leaf_removes_family_record(
    pheno_study: PhenotypeStudy,
) -> None:
    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, keep_original=False,
    )

    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM family WHERE family_id = 'fam1'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 0


def test_remove_from_pheno_leaf_preserves_other_family(
    pheno_study: PhenotypeStudy,
) -> None:
    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, keep_original=False,
    )

    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam2'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 3


def test_remove_from_pheno_leaf_dry_run_no_changes(
    pheno_study: PhenotypeStudy,
) -> None:
    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    before = conn.execute("SELECT COUNT(*) FROM person").fetchone()[0]  # type: ignore[index]
    conn.close()

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=True, keep_original=False,
    )

    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    after = conn.execute("SELECT COUNT(*) FROM person").fetchone()[0]  # type: ignore[index]
    conn.close()
    assert after == before


def test_remove_from_pheno_leaf_keep_original(
    pheno_study: PhenotypeStudy,
) -> None:
    dbfile = pathlib.Path(pheno_study.db.dbfile)

    _remove_from_pheno_leaf(
        pheno_study, {"fam1"}, dry_run=False, keep_original=True,
    )

    orig = dbfile.with_suffix(".db.orig")
    assert orig.exists()

    conn = duckdb.connect(str(orig), read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 3

    conn = duckdb.connect(pheno_study.db.dbfile, read_only=True)
    count = conn.execute(
        "SELECT COUNT(*) FROM person WHERE family_id = 'fam1'",
    ).fetchone()[0]  # type: ignore[index]
    conn.close()
    assert count == 0
