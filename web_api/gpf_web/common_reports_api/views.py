from typing import cast

from datasets_api.partial_grants import (
    families_to_tsv_lines,
    get_fully_granted_family_ids,
    get_partial_grant_families,
    get_partial_grant_studies,
)
from datasets_api.permissions import get_permissions_etag
from django.contrib.auth.models import User
from django.http.response import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from gpf_instance.gpf_instance import WGPFInstance
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy
from utils.query_params import parse_query_params

from common_reports_api.common_reports_helper import (
    BaseCommonReportsHelper,
    CommonReportsHelper,
    collect_families_by_tags,
)
from gpf.pedigrees.families_data import FamiliesData


class VariantReportsView(QueryBaseView):
    """Variant reports view class."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, _request: Request, common_report_id: str) -> Response:
        """Return a variant report when requested."""
        assert common_report_id

        study = self.gpf_instance.get_wdae_wrapper(common_report_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        common_report = common_reports_helper.get_common_report()

        if common_report is not None:
            return Response(common_report)
        return Response(
            {"error": f"Common report {common_report_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class VariantReportsFullView(QueryBaseView, DatasetAccessRightsView):
    """Variants report full view class."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request, common_report_id: str) -> Response:
        """Return full variant report when requested."""
        assert common_report_id

        study = self.gpf_instance.get_wdae_wrapper(common_report_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if get_partial_grant_studies(
            self.instance_id, cast(User, request.user), common_report_id,
        ) is not None:
            # The full report counts the data of all child studies.
            return Response(status=status.HTTP_403_FORBIDDEN)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        full_common_report = common_reports_helper.get_full_common_report()

        if full_common_report is not None:
            return Response(full_common_report)
        return Response(
            {"error": f"Common report {common_report_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class FamilyCounterListView(QueryBaseView, DatasetAccessRightsView):
    """Family couters list view class."""

    def post(self, request: Request) -> Response:
        """Return family counters for specified study and group name."""
        data = request.data
        assert isinstance(data, dict)

        common_report_id = data.get("study_id")
        group_name = data.get("group_name")
        counter_id = data.get("counter_id")

        assert common_report_id
        assert group_name
        assert counter_id is not None

        study = self.gpf_instance.get_wdae_wrapper(common_report_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        try:
            counter_list = common_reports_helper.get_family_counter_list(
                group_name,
                int(counter_id),
            )
        except ValueError:
            return Response(
                {"error": f"Common report {common_report_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        families = get_partial_grant_families(
            self.gpf_instance, cast(User, request.user), common_report_id,
        )
        if families is not None:
            counter_list = get_fully_granted_family_ids(
                counter_list, families, study.families,
            )

        return Response(counter_list)


class FamilyCounterDownloadView(QueryBaseView, DatasetAccessRightsView):
    """Family counters download view class."""

    def post(self, request: Request) -> Response | StreamingHttpResponse:
        """Return family couters for a specified study and group name."""
        data = parse_query_params(request.data)

        study_id = data["study_id"]
        group_name = data["group_name"]
        counter_id = int(data["counter_id"])

        assert study_id is not None

        study = self.gpf_instance.get_wdae_wrapper(study_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        families = get_partial_grant_families(
            self.gpf_instance, cast(User, request.user), study_id,
        )

        try:
            if families is None:
                lines = common_reports_helper.get_family_counter_tsv(
                    group_name,
                    counter_id,
                )
            else:
                family_ids = get_fully_granted_family_ids(
                    common_reports_helper.get_family_counter_list(
                        group_name, counter_id,
                    ),
                    families,
                    study.families,
                )
                lines = families_to_tsv_lines(FamiliesData.from_families({
                    family_id: families[family_id]
                    for family_id in family_ids
                }))
            response = StreamingHttpResponse(
                lines,
                content_type="text/tab-separated-values",
            )
            response["Content-Disposition"] = (
                "attachment; filename=families.ped"
            )
            response["Expires"] = "0"
        except ValueError:
            response = Response(
                {"error": f"Common report for {study_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return response


class FamiliesDataDownloadView(QueryBaseView, DatasetAccessRightsView):
    """Families data download view class."""

    def get(
        self,
        request: Request,
        dataset_id: str,
    ) -> Response | StreamingHttpResponse:
        """Return full family data for a specified study."""
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        families = get_partial_grant_families(
            self.gpf_instance, cast(User, request.user), dataset_id,
        )
        if families is None:
            lines = common_reports_helper.get_family_data_tsv()
        else:
            lines = families_to_tsv_lines(families)

        response = StreamingHttpResponse(
            lines,
            content_type="text/tab-separated-values",
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response

    def post(
        self,
        request: Request,
        dataset_id: str,
    ) -> Response | StreamingHttpResponse:
        """Return full family data for a specified study and tags."""
        data = request.data
        assert isinstance(data, dict)

        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

        common_reports_helper = create_common_reports_helper(
            self.gpf_instance,
            study,
        )

        families = get_partial_grant_families(
            self.gpf_instance, cast(User, request.user), dataset_id,
        )

        try:
            if families is None:
                lines = common_reports_helper.get_filtered_family_data_tsv(
                    data)
            else:
                query = parse_query_params(data) if "queryData" in data \
                    else data
                lines = families_to_tsv_lines(collect_families_by_tags(
                    families, query.get("tagsQuery"),
                ))
        except ValueError as err:
            print(err)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        response = StreamingHttpResponse(
            lines,
            content_type="text/tab-separated-values",
        )
        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response


def create_common_reports_helper(
    gpf_instance: WGPFInstance, study: WDAEAbstractStudy,
) -> BaseCommonReportsHelper:
    """Create an pheno browser helper for the given dataset."""
    for ext_name, extension in gpf_instance.extensions.items():
        common_reports_helper = extension.get_tool(
            study,
            "common_reports_helper",
        )
        if common_reports_helper is not None:
            if not isinstance(common_reports_helper, BaseCommonReportsHelper):
                raise ValueError(
                    f"{ext_name} returned an invalid pheno browser helper!")
            return common_reports_helper

    if not isinstance(study, WDAEStudy):
        raise ValueError(  # ruff: ignore[type-check-without-type-error]
            f"Pheno browser helper for {study.study_id} is missing!")

    return CommonReportsHelper(study)
