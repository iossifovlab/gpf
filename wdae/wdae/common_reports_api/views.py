from typing import Any

from datasets_api.permissions import get_permissions_etag
from django.http.response import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryDatasetView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from utils.query_params import parse_query_params

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import FamilyTag
from dae.pedigrees.family_tag_builder import check_family_tags_query
from dae.pedigrees.loader import FamiliesLoader


class VariantReportsView(QueryDatasetView):
    """Variant reports view class."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, _request: Request, common_report_id: str) -> Response:
        """Return a variant report when requested."""
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id,
        )

        if common_report is not None:
            return Response(common_report.to_dict())
        return Response(
            {"error": f"Common report {common_report_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class VariantReportsFullView(QueryDatasetView):
    """Variants report full view class."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, _request: Request, common_report_id: str) -> Response:
        """Return full variant report when requested."""
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id,
        )

        if common_report is not None:
            return Response(common_report.to_dict(full=True))
        return Response(
            {"error": f"Common report {common_report_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class FamilyCounterListView(QueryDatasetView):
    """Family couters list view class."""

    def post(self, request: Request) -> Response:
        """Return family counters for specified study and group name."""
        data = request.data

        common_report_id = data["study_id"]
        group_name = data["group_name"]
        counter_id = int(data["counter_id"])

        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id,
        )

        if common_report is None:
            return Response(
                {"error": f"Common report {common_report_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        group = common_report.families_report.families_counters[group_name]

        counter = group.counters[counter_id]

        return Response(counter.families)


class FamilyCounterDownloadView(QueryDatasetView):
    """Family counters download view class."""

    def post(self, request: Request) -> Response:
        """Return family couters for a specified study and group name."""
        data = parse_query_params(request.data)

        study_id = data["study_id"]
        group_name = data["group_name"]
        counter_id = int(data["counter_id"])

        assert study_id is not None

        common_report = self.gpf_instance.get_common_report(
            study_id,
        )

        if common_report is None:
            return Response(
                {"error": f"Common report for {study_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        group = common_report.families_report.families_counters[group_name]

        counter_families = group.counters[counter_id].families

        study_families = self.gpf_instance.get_genotype_data(study_id).families

        counter_families_data = FamiliesData.from_families({
            family_id: study_families[family_id]
            for family_id in counter_families
        })

        tsv = FamiliesLoader.to_tsv(counter_families_data)
        lines = map(lambda x: x + "\n", tsv.strip().split("\n"))

        response = StreamingHttpResponse(
            lines,
            content_type="text/tab-separated-values",
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response


class FamiliesDataDownloadView(QueryDatasetView):
    """Families data download view class."""

    @classmethod
    def collect_families(
        cls,
        study_families: FamiliesData,
        tags_query: dict[str, Any] | None,
    ) -> FamiliesData:
        """Collect and filter families by tags."""
        if tags_query is None:
            return study_families

        result = {}

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

        for family_id, family in study_families.items():
            if check_family_tags_query(
                family, or_mode, include_tags, exclude_tags,
            ):
                result[family_id] = family

        return FamiliesData.from_families(result)

    def get(self, _request: Request, dataset_id: str) -> Response:
        """Return full family data for a specified study."""
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study = self.gpf_instance.get_genotype_data(dataset_id)

        if study is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        tsv = FamiliesLoader.to_tsv(study.families)
        lines = map(lambda x: x + "\n", tsv.strip().split("\n"))

        response = StreamingHttpResponse(
            lines,
            content_type="text/tab-separated-values",
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response

    def post(self, request: Request, dataset_id: str) -> Response:
        """Return full family data for a specified study and tags."""
        data = request.data
        if "queryData" in data:
            data = parse_query_params(data)

        tags_query = data.get("tagsQuery")

        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study = self.gpf_instance.get_genotype_data(dataset_id)

        if study is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        study_families = study.families

        try:
            result = self.collect_families(study_families, tags_query)
        except ValueError as err:
            print(err)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        tsv = FamiliesLoader.to_tsv(result)
        lines = map(lambda x: x + "\n", tsv.strip().split("\n"))

        response = StreamingHttpResponse(
            lines,
            content_type="text/tab-separated-values",
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response
