from abc import abstractmethod
from collections import Counter
from collections.abc import Generator
from io import StringIO
from typing import Any, cast

from dae.effect_annotation.effect import EffectTypesMixin
from dae.pheno_tool.tool import PhenoResult, PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex
from gpf_instance.extension import GPFTool
from studies.query_transformer import (
    QueryTransformer,
)
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy


class PhenoToolAdapterBase(GPFTool):
    """Base class for pheno tool adapters."""

    def __init__(self) -> None:
        super().__init__("pheno_tool")

    @abstractmethod
    def calc_variants(
        self,
        query_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Return pheno tool result for given variants."""
        raise NotImplementedError

    @abstractmethod
    def produce_download(
        self,
        query_data: dict[str, Any],
        query_transformer: QueryTransformer,
    ) -> Generator[str, None, None]:
        """Produce columns for download."""
        raise NotImplementedError


class PhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for PhenoTool class."""

    def __init__(self, study: WDAEStudy) -> None:
        super().__init__()
        if not (study.has_genotype_data and study.has_pheno_data):
            raise ValueError(
                f"Study {study.study_id} does not support pheno tool")
        self.study = study
        self.pheno_tool = PhenoTool(study.phenotype_data)
        self.helper = PhenoToolHelper(
            study.genotype_data, study.phenotype_data)

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, WDAEStudy):
            return None
        if study.has_genotype_data and study.has_pheno_data:
            return PhenoToolAdapter(study)
        raise ValueError(f"Study {study.study_id} does not support pheno tool")

    def produce_download(
        self,
        query_data: dict[str, Any],
        query_transformer: QueryTransformer,
    ) -> Generator[str, None, None]:
        yield ""

        query_data["effectTypes"] = EffectTypesMixin.build_effect_types_list(
            query_data["effectTypes"],
        )

        query_data["phenoFilterFamilyIds"] = None
        if query_data.get("familyFilters") is not None:
            query_data["phenoFilterFamilyIds"] = list(
                query_transformer  # noqa: SLF001
                ._transform_filters_to_ids(
                    query_data["familyFilters"],
                    self.study,
                ),
            )
        if query_data.get("familyPhenoFilters") is not None:
            query_data["phenoFilterFamilyIds"] = list(
                query_transformer  # noqa: SLF001
                ._transform_pheno_filters_to_ids(
                    query_data["familyPhenoFilters"],
                    self.study,
                ),
            )

        effect_groups = list(query_data["effectTypes"])
        effect_types = EffectTypesMixin.build_effect_types(
            query_data["effectTypes"])

        measure_id = query_data["measureId"]
        family_ids = query_data.get("phenoFilterFamilyIds")
        person_ids = self.helper.genotype_data_persons(
            query_data.get("familyIds", []),
        )

        normalize_by = cast(
            list[dict[str, str]], query_data.get("normalizeBy"),
        )

        result_df = self.pheno_tool.create_df(
            measure_id, person_ids=cast(list[str], person_ids),
            family_ids=family_ids, normalize_by=normalize_by,
        )

        assert self.study.query_transformer is not None
        assert self.study.response_transformer is not None
        variants = self.study.query_variants_raw(
            query_data, self.study.query_transformer,
        )

        adapted_variants = self.helper.genotype_data_variants(
            variants, effect_types, effect_groups,
        )

        for effect in effect_groups:
            result_df = PhenoTool.join_pheno_df_with_variants(
                result_df, adapted_variants[effect],
            )
            result_df = result_df.rename(columns={"variant_count": effect})

        if normalize_by:
            normalize_by_measures = self.pheno_tool.init_normalize_measures(
                measure_id, normalize_by,
            )
            normalize_desc = " + ".join(normalize_by_measures)
            column_name = f"{measure_id} ~ {normalize_desc}"
            result_df = result_df.rename(columns={"normalized": column_name})
            result_df[column_name] = result_df[column_name].round(decimals=5)

        result_df[measure_id] = \
            result_df[measure_id].round(decimals=5)

        columns = [
            col
            for col in result_df.columns.tolist()
            if col not in {"normalized", "role"}
        ]

        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False, columns=columns)
        csv_buffer.seek(0)

        yield from csv_buffer.readlines()

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
        *,
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        normalize_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Run the base pheno tool calc on given variant counts."""
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
        """Build a description for a report."""
        normalize_by = self.pheno_tool.init_normalize_measures(
            measure_id, normalize_by,
        )
        if not normalize_by:
            return measure_id

        return f"{measure_id} ~ {' + '.join(normalize_by)}"

    def calc_variants(
        self,
        query_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run pheno tool on given data."""
        effect_groups = list(query_data["effectTypes"])
        effect_types = EffectTypesMixin.build_effect_types(
            query_data["effectTypes"])

        measure_id = query_data["measureId"]
        family_ids = query_data.get("phenoFilterFamilyIds")
        person_ids = self.helper.genotype_data_persons(
            query_data.get("familyIds", []),
        )

        normalize_by = cast(
            list[dict[str, str]], query_data.get("normalizeBy"))
        effect_groups = EffectTypesMixin.build_effect_types_list(effect_groups)

        assert self.study.query_transformer is not None
        assert self.study.response_transformer is not None
        variants = self.study.query_variants_raw(
            query_data, self.study.query_transformer,
        )

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
