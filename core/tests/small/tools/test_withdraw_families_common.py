# pylint: disable=redefined-outer-name,C0114,C0116
import pathlib

import pytest

from gpf.tools.withdraw_families_common import (
    backup_path,
    make_run_stamp,
    require_study_kind,
)


class _FakeInstance:
    def __init__(
        self, genotype_ids: list[str], pheno_ids: list[str],
    ) -> None:
        self._g = genotype_ids
        self._p = pheno_ids

    def get_genotype_data_ids(self) -> list[str]:
        return self._g

    def get_phenotype_data_ids(self) -> list[str]:
        return self._p


def test_require_study_kind_genotype_ok() -> None:
    inst = _FakeInstance(["geno1"], ["pheno1"])
    # does not raise for the right kind
    require_study_kind(inst, "geno1", kind="genotypes")


def test_require_study_kind_pheno_ok() -> None:
    inst = _FakeInstance(["geno1"], ["pheno1"])
    require_study_kind(inst, "pheno1", kind="phenotypes")


def test_require_study_kind_wrong_type_redirects_to_pheno_tool() -> None:
    inst = _FakeInstance(["geno1"], ["pheno1"])
    with pytest.raises(SystemExit) as exc:
        require_study_kind(inst, "pheno1", kind="genotypes")
    assert exc.value.code == 1


def test_require_study_kind_wrong_type_redirects_to_geno_tool() -> None:
    inst = _FakeInstance(["geno1"], ["pheno1"])
    with pytest.raises(SystemExit) as exc:
        require_study_kind(inst, "geno1", kind="phenotypes")
    assert exc.value.code == 1


def test_require_study_kind_unknown_exits() -> None:
    inst = _FakeInstance(["geno1"], ["pheno1"])
    with pytest.raises(SystemExit) as exc:
        require_study_kind(inst, "nope", kind="genotypes")
    assert exc.value.code == 1


def test_make_run_stamp_format() -> None:
    stamp = make_run_stamp()
    # 20260625T143000Z -> 16 chars, ends with Z, has a T separator
    assert len(stamp) == 16
    assert stamp.endswith("Z")
    assert stamp[8] == "T"


def test_backup_path_parquet() -> None:
    path = pathlib.Path("/data/study/pedigree/pedigree.parquet")
    result = backup_path(path, "20260625T143000Z")
    assert result == pathlib.Path(
        "/data/study/pedigree/pedigree.20260625T143000Z.parquet.bak",
    )


def test_backup_path_db() -> None:
    path = pathlib.Path("/data/store/test_pheno/test_pheno.db")
    result = backup_path(path, "20260625T143000Z")
    assert result == pathlib.Path(
        "/data/store/test_pheno/test_pheno.20260625T143000Z.db.bak",
    )


def test_backup_path_not_in_parquet_scan() -> None:
    # Terminal .bak keeps backups out of an rglob("*.parquet") scan.
    path = pathlib.Path("/data/x.parquet")
    result = backup_path(path, "20260625T143000Z")
    assert not result.match("*.parquet")
    assert result.suffix == ".bak"
