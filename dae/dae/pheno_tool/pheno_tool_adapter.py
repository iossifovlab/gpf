from collections import Counter
from collections.abc import Iterable
from typing import Any, cast

from dae.effect_annotation.effect import EffectTypesMixin
from dae.pheno_tool.tool import PhenoResult, PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex
from dae.variants.family_variant import FamilyVariant


class PhenoToolAdapterBase:
    """Base class for pheno tool adapters."""

    def calc_by_effect(
        self, measure_id: str, effect: str, people_variants: Counter,
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        normalize_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def calc_variants(
        self,
        measure_id: str,
        family_ids: list[str] | None,
        person_ids: set[str],
        normalize_by: list[dict[str, str]],
        variants: Iterable[FamilyVariant],
        effect_types: list[str],
        effect_groups: list[str],
    ) -> dict[str, Any]:
        raise NotImplementedError


class PhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for PhenoTool class."""

    def __init__(
        self,
        pheno_tool: PhenoTool,
        pheno_tool_helper: PhenoToolHelper,
    ) -> None:
        self.pheno_tool = pheno_tool
        self.helper = pheno_tool_helper

    def get_result_by_sex(
        self, result: dict[str, PhenoResult],
        sex: str,
    ) -> dict[str, Any]:
        return {
            "negative": {
                "count": result[sex].negative_count,
                "deviation": result[sex].negative_deviation,
                "mean": result[sex].negative_mean,
            },
            "positive": {
                "count": result[sex].positive_count,
                "deviation": result[sex].positive_deviation,
                "mean": result[sex].positive_mean,
            },
            "pValue": result[sex].pvalue,
        }

    def calc_by_effect(
        self, measure_id: str, effect: str, people_variants: Counter,
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        normalize_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        result = self.pheno_tool.calc(
            measure_id, people_variants,
            sex_split=True,
            person_ids=person_ids,
            family_ids=family_ids,
            normalize_by=normalize_by,
        )
        assert isinstance(result, dict)

        return {
            "effect": effect,
            "maleResults": self.get_result_by_sex(result, Sex.M.name),
            "femaleResults": self.get_result_by_sex(result, Sex.F.name),
        }

    @staticmethod
    def align_na_results(
        results: list[dict[str, Any]],
    ) -> None:
        """Align NA results."""
        for result in results:
            for sex in ["femaleResults", "maleResults"]:
                res = result[sex]
                if res["positive"]["count"] == 0:
                    assert res["positive"]["mean"] == 0
                    assert res["positive"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["positive"]["mean"] = res["negative"]["mean"]
                if res["negative"]["count"] == 0:
                    assert res["negative"]["mean"] == 0
                    assert res["negative"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["negative"]["mean"] = res["positive"]["mean"]

    def build_report_description(
        self, measure_id: str, normalize_by: Any,
    ) -> str:
        normalize_by = self.pheno_tool.init_normalize_measures(
            measure_id, normalize_by,
        )
        if not normalize_by:
            return measure_id

        return f"{measure_id} ~ {' + '.join(normalize_by)}"

    def calc_variants(
        self,
            measure_id: str,
            family_ids: list[str] | None,
            person_ids: set[str],
            normalize_by: list[dict[str, str]],
            variants: Iterable[FamilyVariant],
            effect_types: list[str],
            effect_groups: list[str],
    ) -> dict[str, Any]:
        """Run pheno tool on given data."""
        effect_groups = EffectTypesMixin.build_effect_types_list(effect_groups)

        people_variants = self.helper.genotype_data_variants(
            variants, effect_types, effect_groups)

        results = [
            self.calc_by_effect(
                measure_id, effect, people_variants.get(effect, Counter()),
                person_ids=cast(list[str], person_ids),
                family_ids=family_ids,
                normalize_by=normalize_by,
            )
            for effect in effect_groups
        ]
        self.align_na_results(results)

        return {
            "description": self.build_report_description(
                measure_id, normalize_by,
            ),
            "results": results,
        }
