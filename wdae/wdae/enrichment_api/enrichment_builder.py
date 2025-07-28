import logging
from abc import abstractmethod
from collections.abc import Iterable
from typing import Any, cast

from dae.gene_scores.gene_scores import GeneScoresDb
from dae.person_sets import PersonSetCollection
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy
from utils.expand_gene_set import expand_gene_set

from enrichment_api.enrichment_helper import EnrichmentHelper
from enrichment_api.enrichment_serializer import EnrichmentSerializer

logger = logging.getLogger(__name__)


class BaseEnrichmentBuilder(GPFTool):
    """Base class for enrichment builders."""
    def __init__(self) -> None:
        super().__init__("enrichment_builder")

    @abstractmethod
    def enrichment_test(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        """Build enrichment test result."""


class EnrichmentBuilder(BaseEnrichmentBuilder):
    """Build enrichment tool test."""

    def __init__(
        self,
        enrichment_helper: EnrichmentHelper,
        gene_scores_db: GeneScoresDb,
        study: WDAEStudy,
    ) -> None:
        assert enrichment_helper.study.study_id == study.study_id
        super().__init__()
        self.enrichment_helper = enrichment_helper
        self.study = study
        self.gene_scores_db = gene_scores_db
        enrichment_config = study.enrichment_config
        assert enrichment_config is not None
        self.enrichment_config = enrichment_config
        self.results: list[dict[str, Any]]

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError

    def build_results(
        self,
        gene_syms: Iterable[str],
        background_id: str | None,
        counting_id: str | None,
    ) -> list[dict[str, Any]]:
        """Build and return a list of enrichment results.

        Returns:
            A list of dictionaries representing the enrichment results.
        """
        results = []

        person_set_collection = cast(
            PersonSetCollection,
            self.study.genotype_data.get_person_set_collection(
                self.enrichment_helper.get_selected_person_set_collections(),
            ),
        )

        effect_types = self.enrichment_config["effect_types"]
        enrichment_result = self.enrichment_helper.calc_enrichment_test(
            person_set_collection.id,
            gene_syms,
            effect_types,
            background_id=background_id,
            counter_id=counting_id,
        )
        for ps_id, effect_res in enrichment_result.items():
            res: dict[str, Any] = {}
            person_set = person_set_collection.person_sets[ps_id]
            children_stats = person_set.get_children_stats()
            res["childrenStats"] = {
                "M": children_stats.male,
                "F": children_stats.female,
                "U": children_stats.unspecified,
            }
            res["selector"] = person_set.name
            res["geneSymbols"] = list(gene_syms)
            res["peopleGroupId"] = person_set_collection.id
            res["peopleGroupValue"] = ps_id
            res["datasetId"] = self.study.study_id
            for effect_type, enrichment_res in effect_res.items():
                res[effect_type] = {}
                res[effect_type]["all"] = enrichment_res.all
                res[effect_type]["rec"] = enrichment_res.rec
                res[effect_type]["female"] = enrichment_res.female
                res[effect_type]["male"] = enrichment_res.male

            results.append(res)

        return results

    @staticmethod
    def _parse_gene_syms(query: dict[str, Any]) -> list[str]:
        gene_syms = query.get("geneSymbols")
        if gene_syms is None:
            return []

        if isinstance(gene_syms, str):
            gene_syms = gene_syms.split(",")
        return [g.strip() for g in gene_syms]

    def enrichment_test(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        """Build enrichment test result."""

        query = expand_gene_set(cast(dict, query))

        if "geneSymbols" not in query and (
            "geneScores" not in query
            or (
                "geneScores" in query
                and "score" not in query.get("geneScores", {})
            )
        ):
            raise ValueError(
                "Gene symbols must be provided or "
                "gene_score must contain a valid score.",
            )

        gene_syms = None
        if "geneSymbols" in query:
            gene_syms = self._parse_gene_syms(query)
        gene_score = cast(dict[str, Any] | None, query.get("geneScores", None))
        background_id = query.get("enrichmentBackgroundModel", None)
        counting_id = query.get("enrichmentCountingModel", None)
        gene_set_id = cast(str, query.get("geneSet"))

        return {
            "desc": self.create_enrichment_description(
                gene_set_id,
                gene_score,
                gene_syms,
            ),
            "result": self.build(
                gene_syms,
                gene_score,
                background_id,
                counting_id,
            ),
        }

    def build(
        self,
        gene_syms: list[str] | None,
        gene_score: dict[str, Any] | None,
        background_id: str | None,
        counting_id: str | None,
    ) -> list[dict[str, Any]]:
        """Build enrichment test result"""
        if gene_syms is None:
            gene_syms = self._get_gene_syms(gene_score)

        logger.info("selected background model: %s", background_id)
        logger.info("selected counting model: %s", counting_id)

        results = self.build_results(gene_syms, background_id, counting_id)

        serializer = EnrichmentSerializer(self.enrichment_config, results)
        results = serializer.serialize()

        self.results = results
        return self.results

    def create_enrichment_description(
        self,
        gene_set_id: str | None,
        gene_score: dict[str, Any] | None,
        gene_syms: list[str] | None,
    ) -> str:
        """Build enrichment result description."""

        if gene_syms is None:
            gene_syms = self._get_gene_syms(gene_score)

        desc = ""
        if gene_set_id:
            desc = f"Gene Set: {gene_set_id}"
        elif gene_score and gene_score.get("score", "") \
            in self.gene_scores_db:
            gene_scores_id = gene_score.get("score")

            if gene_scores_id is not None:
                range_start = cast(float | None, gene_score.get("rangeStart"))
                range_end = cast(float | None, gene_score.get("rangeEnd"))

                if range_start is not None and range_end is not None:
                    desc = (
                        f"Gene Scores: {gene_scores_id} "
                        f"from {round(range_start, 2)} "
                        f"up to {round(range_end, 2)}"
                    )
                elif range_start is not None:
                    desc = (
                        f"Gene Scores: {gene_scores_id} "
                        f"from {round(range_start, 2)}"
                    )
                elif range_end is not None:
                    desc = (
                        f"Gene Scores: {gene_scores_id} "
                        f"up to {round(range_end, 2)}"
                    )
                else:
                    desc = f"Gene Scores: {gene_scores_id}"
        else:
            desc = f"Gene Symbols: {','.join(gene_syms)}"

        return f"{desc} ({len(gene_syms)})"

    def _get_gene_syms(self, gene_score: dict[str, Any] | None) -> list[str]:
        if gene_score is None:
            raise ValueError(
                "Gene symbols must be provided or"
                "gene_score must contain a valid score.",
            )

        gene_score_id = gene_score.get("score", "")
        range_start = gene_score.get("rangeStart")
        range_end = gene_score.get("rangeEnd")

        gene_syms: list[str] = []
        if gene_score_id in self.gene_scores_db:
            score_desc = self.gene_scores_db.get_score_desc(
                gene_score_id,
            )
            if score_desc is None:
                raise ValueError(
                    f"Missing gene score description for {gene_score_id}",
                )
            score = self.gene_scores_db.get_gene_score(
                score_desc.resource_id,
            )
            if score is None:
                raise ValueError(
                    f"Score not found: {gene_score_id}",
                )
            gene_syms = list(
                score.get_genes(
                    gene_score_id,
                    score_min=range_start,
                    score_max=range_end,
                ),
            )
        return gene_syms
