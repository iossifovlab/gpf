# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.pheno_tool.tool import PhenoResult
from dae.variants.attributes import Sex
from pheno_tool_api.pheno_tool_adapter import PhenoToolAdapter
from pheno_tool_api.views import PhenoToolView

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_pheno_tool_view_build_report_description() -> None:
    desc = PhenoToolView._build_report_description("measure", [])
    assert desc == "measure"
    desc = PhenoToolView._build_report_description("measure", ["norm1"])
    assert desc == "measure ~ norm1"
    desc = PhenoToolView._build_report_description(
        "measure", ["norm1", "norm2"],
    )
    assert desc == "measure ~ norm1 + norm2"


def test_pheno_tool_view_align_na_results_valid() -> None:
    results = {
        "maleResults": {
            "positive": {"count": 0, "mean": 0, "deviation": 0},
            "negative": {"count": 1, "mean": 1, "deviation": 0},
            "pValue": "NA",
        },
        "femaleResults": {
            "positive": {"count": 0, "mean": 0, "deviation": 0},
            "negative": {"count": 1, "mean": 1, "deviation": 0},
            "pValue": "NA",
        },
    }
    PhenoToolAdapter.align_na_results([results])
    assert results["maleResults"]["positive"]["mean"] == 1  # type: ignore
    assert results["femaleResults"]["positive"]["mean"] == 1  # type: ignore


def test_pheno_tool_view_align_na_results_invalid() -> None:
    results = {
        "maleResults": {
            "positive": {"count": 0, "mean": 5, "deviation": 0.2},
            "negative": {"count": 0, "mean": 1, "deviation": 0.3},
            "pValue": 0.02,
        },
        "femaleResults": {
            "positive": {"count": 0, "mean": 5, "deviation": 0.2},
            "negative": {"count": 0, "mean": 1, "deviation": 0.3},
            "pValue": 0.02,
        },
    }
    with pytest.raises(AssertionError):
        PhenoToolAdapter.align_na_results([results])


def test_pheno_tool_view_get_result_by_sex() -> None:
    expected_result = {
        "positive": {"count": 1, "mean": 2, "deviation": 3},
        "negative": {"count": 4, "mean": 5, "deviation": 6},
        "pValue": 7,
    }
    result = PhenoResult()
    result.set_positive_stats(1, 2, 3)
    result.set_negative_stats(4, 5, 6)
    result.pvalue = 7
    results = {Sex.M.name: result, Sex.F.name: PhenoResult()}
    ret_val = PhenoToolView.get_result_by_sex(results, Sex.M.name)
    assert ret_val == expected_result


# def test_pheno_tool_view_calc_by_effect() -> None:
#     class MockPhenoTool:
#         def calc(self, people_variants: dict, sex_split: bool) -> dict:
#             pr_m = PhenoResult()
#             pr_m.set_positive_stats(1, 2, 3)
#             pr_f = PhenoResult()
#             pr_f.set_positive_stats(4, 5, 6)
#             return {Sex.M.name: pr_m, Sex.F.name: pr_f}

#     mocked_tool = MockPhenoTool()
#     res = PhenoToolView.calc_by_effect("effectName", mocked_tool, {})
#     assert res["effect"] == "effectName"
#     assert res["maleResults"]["positive"]["count"] == 1
#     assert res["maleResults"]["positive"]["mean"] == 2
#     assert res["maleResults"]["positive"]["deviation"] == 3
#     assert res["femaleResults"]["positive"]["count"] == 4
#     assert res["femaleResults"]["positive"]["mean"] == 5
#     assert res["femaleResults"]["positive"]["deviation"] == 6
