from collections import Counter
from typing import Any, Dict, List

from remote.rest_api_client import RESTClient
from studies.study_wrapper import StudyWrapper

from dae.effect_annotation.effect import EffectTypesMixin
from dae.pheno_tool.tool import PhenoResult, PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex


class PhenoToolAdapterBase:

    def calc_by_effect(
        self, effect: str, people_variants: Counter,
    ) -> dict[str, Any]:
        raise NotImplementedError


class PhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for PhenoTool class."""

    def __init__(
        self, study_wrapper: StudyWrapper,
        pheno_tool: PhenoTool,
        pheno_tool_helper: PhenoToolHelper,
    ) -> None:
        self.study_wrapper = study_wrapper
        self.pheno_tool = pheno_tool
        self.helper = pheno_tool_helper

    def get_result_by_sex(
        self, result: Dict[str, PhenoResult],
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
        self, effect: str, people_variants: Counter,
    ) -> dict[str, Any]:
        result = self.pheno_tool.calc(people_variants, sex_split=True)
        assert isinstance(result, dict)

        return {
            "effect": effect,
            "maleResults": self.get_result_by_sex(result, Sex.M.name),
            "femaleResults": self.get_result_by_sex(result, Sex.F.name),
        }

    @staticmethod
    def align_na_results(
        results: List[Dict[str, Any]],
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

    def build_report_description(self) -> str:
        normalize_by = self.pheno_tool.normalize_by
        measure_id = self.pheno_tool.measure_id
        if not normalize_by:
            return measure_id

        return f"{measure_id} ~ {' + '.join(normalize_by)}"

    def calc_variants(
        self, data: Dict[str, Any], effect_groups: list[str],
    ) -> dict[str, Any]:
        """Run pheno tool on given data."""
        data = self.study_wrapper.transform_request(data)
        effect_groups = EffectTypesMixin.build_effect_types_list(effect_groups)

        people_variants = self.helper.genotype_data_variants(
            data, effect_groups)

        results = [
            self.calc_by_effect(
                effect, people_variants.get(effect, Counter()),
            )
            for effect in effect_groups
        ]
        self.align_na_results(results)

        output = {
            "description": self.build_report_description(),
            "results": results,
        }

        return output


class RemotePhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for remote PhenoTool class."""

    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    def calc_variants(
        self, data: Dict[str, Any], effect_groups: list[str],
    ) -> dict[str, Any]:
        # pylint: disable=W0613
        data["datasetId"] = self.dataset_id
        return self.rest_client.post_pheno_tool(data)  # type: ignore

    def calc_by_effect(
        self, effect: str, people_variants: Counter,
    ) -> dict[str, Any]:
        raise NotImplementedError
