# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import math
import pathlib
from io import StringIO
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pedigrees.family import Family
from gpf.pedigrees.loader import FamiliesLoader
from gpf.tools import gpf_validation_runner
from gpf.utils.variant_utils import GenotypeType
from gpf.variants.family_variant import FamilyVariant
from gpf.variants.variant import SummaryAllele, SummaryVariant

PED = """
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""

EFFECT = "missense!SAMD11:missense!NM_1:SAMD11:missense:12/100(Arg->Pro)"

Runner = gpf_validation_runner.GenotypeBrowserRunner


@pytest.fixture
def family() -> Family:
    return FamiliesLoader(StringIO(PED), ped_sep=",").load()["f1"]


def _runner(
    tmp_path: pathlib.Path, skip_columns: set[str] | None = None,
) -> Runner:
    runner = Runner(
        {}, cast(GPFInstance, object()),
        detailed_reporting=False,
        skip_columns=set() if skip_columns is None else skip_columns,
    )
    runner.expectations = {
        "file": str(tmp_path / "expectations" / "study1.yaml"),
        "study": "study1",
        "target": "genotype_browser",
        "name": "study1 tests",
    }
    return runner


@pytest.fixture
def runner(tmp_path: pathlib.Path) -> Runner:
    return _runner(tmp_path)


def _variant(
    family: Family, position: int, *,
    effect: str | None = None,
    attributes: dict[str, Any] | None = None,
    genotype: list[list[int]] | None = None,
) -> FamilyVariant:
    sv = SummaryVariant([
        SummaryAllele(
            "1", position, "A", None,
            summary_index=0, allele_index=0),
        SummaryAllele(
            "1", position, "A", "T",
            summary_index=0, allele_index=1,
            effect=effect, attributes=attributes),
    ])
    gt = [[0, 0, 0], [0, 0, 1]] if genotype is None else genotype
    return FamilyVariant(
        sv, family,
        genotype=np.array(gt, dtype=GenotypeType),
        best_state=None,
    )


def test_build_variants_df_empty_list_has_no_rows_and_no_columns(
    runner: Runner,
) -> None:
    df = runner._build_variants_df([])

    assert len(df) == 0
    assert len(df.columns) == 0


def test_build_variants_df_variant_without_alt_allele_is_empty(
    runner: Runner, family: Family,
) -> None:
    variant = _variant(family, 10, genotype=[[0, 0, 0], [0, 0, 0]])

    df = runner._build_variants_df([variant])

    assert len(df) == 0
    assert len(df.columns) == 0


def test_build_variants_df_allele_with_effects_and_frequency(
    runner: Runner, family: Family,
) -> None:
    variant = _variant(
        family, 10, effect=EFFECT,
        attributes={"af_allele_count": 3, "not_checked": 1})

    df = runner._build_variants_df([variant])

    assert df.to_dict("records") == [{
        "allele_index": 1,
        "af_allele_count": 3,
        "fvuid": "f1.1:10.A.T",
        "effect_type": "missense",
        "effect_gene_genes": "SAMD11",
        "effect_gene_types": "missense",
        "effect_details_transcript_ids": "NM_1",
        "effect_details_details": "NM_1:SAMD11:missense:12/100(Arg->Pro)",
        "chromosome": 1,
        "position": 10,
        "reference": "A",
        "alternative": "T",
        "family_id": "f1",
        "cshl_location": "1:10",
        "cshl_variant": "sub(A->T)",
    }]


def test_build_variants_df_does_not_change_the_allele(
    runner: Runner, family: Family,
) -> None:
    variant = _variant(family, 10, attributes={"not_checked": 1})
    before = dict(variant.alt_alleles[0].attributes)

    runner._build_variants_df([variant])

    assert variant.alt_alleles[0].attributes == before
    assert "transmission_type" in before


def test_build_variants_df_missing_frequency_and_effects_become_nan(
    runner: Runner, family: Family,
) -> None:
    variant = _variant(family, 10)

    df = runner._build_variants_df([variant])

    record = df.to_dict("records")[0]
    for key in [
        "af_allele_count", "af_allele_freq",
        "af_parents_called_count", "af_parents_called_percent",
        "effect_type", "effect_gene_genes", "effect_gene_types",
        "effect_details_transcript_ids", "effect_details_details",
    ]:
        assert math.isnan(record[key]), key
    assert "transmission_type" not in record


def test_build_variants_df_sorts_by_position_with_a_new_index(
    runner: Runner, family: Family,
) -> None:
    variants = [_variant(family, 30), _variant(family, 10)]

    df = runner._build_variants_df(variants)

    assert df["position"].to_list() == [10, 30]
    assert df.index.to_list() == [0, 1]


def test_build_variants_df_skip_columns_keeps_the_location_columns(
    tmp_path: pathlib.Path, family: Family,
) -> None:
    runner = _runner(
        tmp_path, skip_columns={"effect_type", "cadd_raw", "chromosome"})
    variant = _variant(
        family, 10, effect=EFFECT, attributes={"cadd_raw": 0.5})

    df = runner._build_variants_df([variant])

    assert "effect_type" not in df.columns
    assert "cadd_raw" not in df.columns
    assert df["chromosome"].to_list() == [1]


def _case_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "expectations" / "study1" / "case_1.tsv"


CASE = {"name": "case 1", "id": "case_1"}
PARAMS = {"genes": ["SAMD11"]}

# The tail of the message of a FAIL against an expected frame with no
# columns: the column-set assertion ends with the columns of that frame.
NO_COLUMNS_FAIL_TAIL = (
    "RangeIndex(start=0, stop=0, step=1))\n"
    "Length mismatch: 1 vs expected 0\n")


def _write_case(tmp_path: pathlib.Path, content: str) -> pathlib.Path:
    path = _case_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _store(
    runner: Runner, tmp_path: pathlib.Path,
    variants: list[FamilyVariant],
) -> pathlib.Path:
    return _write_case(
        tmp_path,
        runner._build_variants_df(variants).to_csv(sep="\t", index=False))


def test_execute_variants_missing_file_returns_none_and_makes_dir(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    result = runner._execute_variants_test_case(
        CASE, PARAMS, [_variant(family, 10)])

    assert result is None
    assert _case_path(tmp_path).parent.is_dir()
    assert not _case_path(tmp_path).exists()


def test_execute_variants_matching_file_passes(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    variants = [_variant(family, 10, effect=EFFECT), _variant(family, 20)]
    _store(runner, tmp_path, variants)

    result = runner._execute_variants_test_case(CASE, PARAMS, variants)

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.PASSED
    assert result.message is None
    assert result.test_for == "variants"
    assert result.case is CASE
    assert result.params is PARAMS
    assert result.expectation is runner.expectations


def test_execute_variants_different_file_fails_with_the_diff(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    path = _store(runner, tmp_path, [_variant(family, 10)])
    variants = [_variant(family, 10), _variant(family, 20)]

    result = runner._execute_variants_test_case(CASE, PARAMS, variants)

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.FAIL
    assert result.message == (
        f"\nreading expected variants from {path};\n"
        "expected 1 variants; got 2\n"
        "Length mismatch: 2 vs expected 1\n")


@pytest.mark.parametrize(
    "positions, status, message_tail",
    [
        ([], gpf_validation_runner.TestStatus.PASSED, None),
        ([10], gpf_validation_runner.TestStatus.FAIL, NO_COLUMNS_FAIL_TAIL),
    ],
)
def test_execute_variants_zero_byte_file_is_an_empty_frame(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
    positions: list[int], status: gpf_validation_runner.TestStatus,
    message_tail: str | None,
) -> None:
    path = _write_case(tmp_path, "")
    variants = [_variant(family, p) for p in positions]

    result = runner._execute_variants_test_case(CASE, PARAMS, variants)

    assert result is not None
    assert result.status == status
    if message_tail is None:
        assert result.message is None
    else:
        assert result.message is not None
        assert result.message.startswith(
            f"\nreading expected variants from {path};\n(Index([")
        assert result.message.endswith(message_tail)


def test_execute_variants_header_only_and_no_variants_passes(
    runner: Runner, tmp_path: pathlib.Path,
) -> None:
    _write_case(tmp_path, "chromosome\tposition\textra\n")

    result = runner._execute_variants_test_case(CASE, PARAMS, [])

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.PASSED


def test_execute_variants_header_only_and_variants_fails(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    path = _write_case(tmp_path, "chromosome\tposition\n")

    result = runner._execute_variants_test_case(
        CASE, PARAMS, [_variant(family, 10)])

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.FAIL
    assert result.message is not None
    assert result.message.startswith(
        f"\nreading expected variants from {path};\n(Index([")
    # The expected frame has no columns, not the columns of the header.
    assert result.message.endswith(NO_COLUMNS_FAIL_TAIL)


def test_execute_variants_skip_columns_drop_expected_columns(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    variants = [_variant(family, 10, effect=EFFECT)]
    _store(runner, tmp_path, variants)
    skipping = _runner(tmp_path, skip_columns={"effect_type"})

    result = skipping._execute_variants_test_case(CASE, PARAMS, variants)

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.PASSED


def test_execute_variants_ignores_unchecked_columns_of_the_file(
    runner: Runner, tmp_path: pathlib.Path, family: Family,
) -> None:
    variants = [_variant(family, 10)]
    path = _store(runner, tmp_path, variants)
    expected = pd.read_csv(path, sep="\t")
    expected["not_checked"] = "x"
    expected.to_csv(path, sep="\t", index=False)

    result = runner._execute_variants_test_case(CASE, PARAMS, variants)

    assert result is not None
    assert result.status == gpf_validation_runner.TestStatus.PASSED
