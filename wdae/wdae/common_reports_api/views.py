from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from datasets_api.permissions import user_has_permission

from query_base.query_base import QueryBaseView


class VariantReportsView(QueryBaseView):
    def __init__(self):
        super(VariantReportsView, self).__init__()

    def get(self, request, common_report_id):
        assert common_report_id

        common_report = self.gpf_instance.get_common_report(
            common_report_id
        )

        if common_report:
            return Response(common_report)
        return Response(
            {"error": "Common report {} not found".format(common_report_id)},
            status=status.HTTP_404_NOT_FOUND,
        )


class FamiliesDataDownloadView(QueryBaseView):
    def __init__(self):
        super(FamiliesDataDownloadView, self).__init__()

    def get(self, request, common_report_id):
        report = self.gpf_instance.get_common_report(common_report_id)
        if not report:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user_has_permission(
            request.user, common_report_id
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        families_data = self.gpf_instance.get_common_report_families_data(
            common_report_id
        )
        if not families_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            families_data, content_type="text/tsv"
        )

        response["Content-Disposition"] = "attachment; filename=families.ped"
        response["Expires"] = "0"

        return response
