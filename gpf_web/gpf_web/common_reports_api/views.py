from datasets_api.permissions import get_permissions_etag
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
)


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
    def get(self, _request: Request, common_report_id: str) -> Response:
        """Return full variant report when requested."""
        assert common_report_id

        study = self.gpf_instance.get_wdae_wrapper(common_report_id)
        if not study:
            return Response(status=status.HTTP_404_NOT_FOUND)

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

        try:
            response = StreamingHttpResponse(
                common_reports_helper.get_family_counter_tsv(
                    group_name,
                    counter_id,
                ),
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
        _request: Request,
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

        response = StreamingHttpResponse(
            common_reports_helper.get_family_data_tsv(),
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

        try:
            lines = common_reports_helper.get_filtered_family_data_tsv(data)
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
        raise ValueError(  # noqa: TRY004
            f"Pheno browser helper for {study.study_id} is missing!")

    return CommonReportsHelper(study)
