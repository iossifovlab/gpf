from typing import Any, cast, Optional

from dae.enrichment_tool.event_counters import EnrichmentSingleResult
from dae.effect_annotation.effect import EffectTypesMixin


class EnrichmentSerializer(EffectTypesMixin):
    """Serializer for enrichment tool results."""

    def __init__(
            self, enrichment_config: dict[str, Any],
            results: list[dict[str, Any]]):
        self.enrichment_config = enrichment_config
        self.enrichment_results = results

    def serialize(self) -> list[dict]:
        assert self.enrichment_results is not None
        output = []
        for results in self.enrichment_results:
            output.append(self.serialize_people_groups(results))
        return output

    def serialize_people_groups(
        self, grouping_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Serialize people group results."""
        output = {}
        output["selector"] = grouping_results["selector"]
        output["peopleGroupId"] = grouping_results["peopleGroupId"]
        output["childrenStats"] = grouping_results["childrenStats"]

        for effect_type in self.enrichment_config["effect_types"]:
            result = cast(
                dict[str, EnrichmentSingleResult],
                grouping_results[effect_type])
            out = {}
            out["all"] = self.serialize_all(
                grouping_results, effect_type, result["all"]
            )
            out["rec"] = self.serialize_rec(
                grouping_results, effect_type, result["rec"]
            )
            out["male"] = self.serialize_male(
                grouping_results, effect_type, result["male"]
            )
            out["female"] = self.serialize_female(
                grouping_results, effect_type, result["female"]
            )
            output[effect_type] = out
        return output

    def serialize_common_filter(
        self,
        grouping_results: dict[str, dict[str, EnrichmentSingleResult]],
        effect_type: str,
        _result: EnrichmentSingleResult,
        gender: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Serialize common filter."""
        if gender is None:
            gender = ["male", "female", "unspecified"]

        effect_types_fixed = self.build_effect_types(effect_type)
        common_filter = {
            "datasetId": grouping_results["datasetId"],
            "effectTypes": effect_types_fixed,
            "gender": gender,
            "peopleGroup": {
                "id": grouping_results["peopleGroupId"],
                "checkedValues": [grouping_results["peopleGroupValue"]],
            },
            "studyTypes": ["we"],
            "variantTypes": ["ins", "sub", "del", "complex"],
        }
        return common_filter

    # def serialize_events_gene_symbols(
    #     self, events: list[list[str]]
    # ) -> set[str]:
    #     return reduce(lambda x, y: set(x) | set(y), events, set([]))

    def serialize_rec_filter(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult,
        gender: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Serialize recurrent events filter."""
        if gender is None:
            gender = ["male", "female", "unspecified"]

        rec_filter = self.serialize_common_filter(
            grouping_results, effect_type, result, gender
        )
        return rec_filter

    def serialize_overlap_filter(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult,
        gender: Optional[list[str]] = None,
        overlapped_genes: bool = False
    ) -> dict[str, Any]:
        """Serialize overlapped events filter."""
        if gender is None:
            gender = ["male", "female", "unspecified"]

        overlap_filter = self.serialize_common_filter(
            grouping_results, effect_type, result, gender=gender
        )
        if overlapped_genes:
            assert result.overlapped_genes is not None
            overlap_filter["overlappedGenes"] = result.overlapped_genes

        return overlap_filter

    def serialize_all(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        assert result.name == "all"
        return self._serialize_gender_filter(
            grouping_results, effect_type, result
        )

    def serialize_male(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        assert result.name == "male"
        return self._serialize_gender_filter(
            grouping_results, effect_type, result
        )

    def serialize_female(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        assert result.name == "female"
        return self._serialize_gender_filter(
            grouping_results, effect_type, result
        )

    def _get_child_gender(self, gender: str) -> list[str]:
        assert gender in ["all", "male", "female", "unspecified"]
        if gender == "all":
            return ["male", "female", "unspecified"]
        return [gender]

    def _serialize_gender_filter(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        assert result.name in set(["all", "male", "female"])
        gender = self._get_child_gender(result.name)
        output = self.serialize_enrichment_result(result)
        output["countFilter"] = self.serialize_common_filter(
            grouping_results, effect_type, result, gender=gender
        )
        output["overlapFilter"] = self.serialize_overlap_filter(
            grouping_results, effect_type, result, gender=gender
        )
        return output

    def serialize_rec(
        self, grouping_results: dict[str, Any],
        effect_type: str,
        result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        """Serialize recurrent events."""
        assert result.name == "rec"
        output = self.serialize_enrichment_result(result)
        output["countFilter"] = self.serialize_rec_filter(
            grouping_results, effect_type, result
        )
        output["overlapFilter"] = self.serialize_overlap_filter(
            grouping_results, effect_type, result, overlapped_genes=True
        )
        return output

    def serialize_enrichment_result(
            self, result: EnrichmentSingleResult
    ) -> dict[str, Any]:
        """Serialize enrichment result."""
        assert isinstance(result, EnrichmentSingleResult)
        assert result.events is not None
        assert result.overlapped is not None

        res: dict[str, Any] = {}

        res["name"] = result.name
        res["count"] = result.events
        res["overlapped"] = result.overlapped
        res["expected"] = result.expected
        res["pvalue"] = result.pvalue
        return res
