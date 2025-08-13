from abc import abstractmethod
from typing import Any

from dae.common_reports.common_report import CommonReport
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import FamilyTag
from dae.pedigrees.family_tag_builder import check_family_tags_query
from dae.pedigrees.loader import FamiliesLoader
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy
from utils.query_params import parse_query_params


class BaseCommonReportsHelper(GPFTool):
    """Base class for common reports helper"""

    def __init__(self) -> None:
        super().__init__("common_reports_helper")

    @abstractmethod
    def get_common_report(self) -> CommonReport | None:
        """Load and return common report (dataset statistics) for a study."""

    @abstractmethod
    def get_family_counter_tsv(
        self,
        group_name: str,
        counter_id: int,
    ) -> list[str]:
        """Return family counters as tsv file."""

    @abstractmethod
    def get_family_data_tsv(
        self,
    ) -> list[str]:
        """Return family counters as tsv file."""

    @abstractmethod
    def get_filtered_family_data_tsv(
        self,
        data: dict,
    ) -> list[str]:
        """Return family counters as tsv file."""


class CommonReportsHelper(BaseCommonReportsHelper):
    """Build enrichment tool test."""

    def __init__(
        self,
        study: WDAEStudy,
    ) -> None:
        super().__init__()
        self.study = study

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError

    def get_common_report(self) -> CommonReport | None:
        common_report = None
        if self.study.has_genotype_data:
            common_report = self.study.genotype_data.get_common_report()
        elif self.study.has_pheno_data:
            common_report = self.study.phenotype_data.get_common_report()
        return common_report

    def get_family_counter_tsv(
        self,
        group_name: str,
        counter_id: int,
    ) -> list[str]:
        common_report = self.get_common_report()
        if common_report is None:
            raise ValueError
        group = common_report.families_report.families_counters[group_name]
        counter_families = group.counters[counter_id].families
        if self.study.is_genotype:
            study_families = self.study.genotype_data.families
        else:
            study_families = self.study.phenotype_data.families

        counter_families_data = FamiliesData.from_families({
            family_id: study_families[family_id]
            for family_id in counter_families
        })

        tsv = FamiliesLoader.to_tsv(counter_families_data)
        return [f"{ln}\n" for ln in tsv.strip().split("\n")]

    def get_family_data_tsv(
        self,
    ) -> list[str]:
        tsv = FamiliesLoader.to_tsv(self.study.families)
        return [f"{ln}\n" for ln in tsv.strip().split("\n")]

    def get_filtered_family_data_tsv(
        self,
        data: dict,
    ) -> list[str]:
        if "queryData" in data:
            data = parse_query_params(data)

        tags_query = data.get("tagsQuery")

        study_families = self.study.families

        result = self._collect_families(study_families, tags_query)

        tsv = FamiliesLoader.to_tsv(result)
        return [f"{ln}\n" for ln in tsv.strip().split("\n")]

    def _collect_families(
        self,
        study_families: FamiliesData,
        tags_query: dict[str, Any] | None,
    ) -> FamiliesData:
        """Collect and filter families by tags."""
        if tags_query is None:
            return study_families

        or_mode = tags_query.get("orMode")
        if or_mode is None or not isinstance(or_mode, bool):
            raise ValueError("Invalid mode or none specified")
        include_tags = tags_query.get("includeTags")
        if include_tags is None or not isinstance(include_tags, list):
            raise ValueError("Invalid include or none specified")
        include_tags = {FamilyTag.from_label(label) for label in include_tags}
        exclude_tags = tags_query.get("excludeTags")
        if exclude_tags is None or not isinstance(exclude_tags, list):
            raise ValueError("Invalid exclude or none specified")
        exclude_tags = {FamilyTag.from_label(label) for label in exclude_tags}

        result = {
            family_id: family
            for family_id, family in study_families.items()
            if check_family_tags_query(
                family, or_mode=or_mode,
                include_tags=include_tags,
                exclude_tags=exclude_tags,
            )
        }

        return FamiliesData.from_families(result)
